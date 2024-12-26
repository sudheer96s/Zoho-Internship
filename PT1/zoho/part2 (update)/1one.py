from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'sudheer'

# Database connection
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='newbooking'
    )
    return connection

# Function to check load factor and add buses dynamically
def check_and_add_buses(date):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Calculate load factor
    cursor.execute("""
        SELECT SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) / COUNT(*) AS load_factor
        FROM bus_seat_availability
        WHERE availability_date = %s
    """, (date,))
    load_factor = cursor.fetchone()['load_factor']

    # Check if load factor exceeds 0.8 and add buses if necessary
    if load_factor > 0.8:
        cursor.execute("SELECT COUNT(*) AS total_buses FROM buses WHERE date = %s", (date,))
        total_buses = cursor.fetchone()['total_buses']
        
        # Add buses if the total number of buses is less than 100
        if total_buses < 100:
            buses_to_add = min(2, 100 - total_buses)  # Add up to 2 buses or until total buses reach 100
            for _ in range(buses_to_add):
                cursor.execute("""
                    INSERT INTO buses (bus_name, date, status)
                    VALUES (%s, %s, 'available')
                """, (f"Bus {total_buses + 1}", date))
                total_buses += 1

            connection.commit()

    cursor.close()
    connection.close()

# Home route with visitor count and date selection
@app.route('/', methods=['GET', 'POST'])
def home():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Increment visitor count
    cursor.execute("SELECT count FROM visitor_count WHERE id = 1")
    result = cursor.fetchone()

    if result:
        visitor_count = result['count'] + 1
        cursor.execute("UPDATE visitor_count SET count = %s WHERE id = 1", (visitor_count,))
    else:
        visitor_count = 1
        cursor.execute("INSERT INTO visitor_count (count) VALUES (%s)", (visitor_count,))

    connection.commit()

    if request.method == 'POST':
        date = request.form.get('date')
        session['selected_date'] = date
        
        # Fetch all buses for the selected date, including those unavailable
        cursor.execute("""
            SELECT bus_id, bus_name, status
            FROM buses
            WHERE date = %s
        """, (date,))
        buses = cursor.fetchall()

        # Update bus availability status
        for bus in buses:
            if bus['status'] == 'unavailable':
                bus['status_message'] = 'Bus alteration in process'
            else:
                bus['status_message'] = 'Available'

        # Check load factor and dynamically add buses if needed
        check_and_add_buses(date)

        cursor.close()
        connection.close()

        return render_template('index.html', buses=buses, visitor_count=visitor_count, selected_date=date)
    
    # Handle GET request to display visitor count and date selection
    session['visitor_count'] = visitor_count

    cursor.close()
    connection.close()

    return render_template('index.html', buses=[], visitor_count=visitor_count, selected_date=None)

@app.route('/view_seats', methods=['POST'])
def view_seats():
    date = request.form.get('date')
    bus_id = request.form.get('bus_id')
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)
    
    try:
        # Fetch bus details
        cursor.execute("""
            SELECT bus_name FROM buses WHERE bus_id = %s
        """, (bus_id,))
        bus = cursor.fetchone()
        
        if bus is None:
            return "Bus not found.", 404
        
        # Fetch seat availability
        cursor.execute("""
            SELECT seat_number, status FROM bus_seat_availability 
            WHERE bus_id = %s AND availability_date = %s
        """, (bus_id, date))
        seats = cursor.fetchall()
    except mysql.connector.Error as err:
        return f"Error: {err}", 500
    finally:
        cursor.close()
        connection.close()
    
    return render_template('view_seats.html', seats=seats, bus_id=bus_id, bus_name=bus['bus_name'], date=date)

@app.route('/book', methods=['POST'])
def book():
    bus_id = request.form.get('bus_id')
    bus_name = request.form.get('bus_name')
    seat_number = request.form.get('seat_number')
    date = request.form.get('date')
    user_name = request.form.get('user_name')
    phone_number = request.form.get('phone_number')
    age = request.form.get('age')
    email = request.form.get('email')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Insert booking details
        cursor.execute("""
            INSERT INTO bus_bookings (bus_id, bus_name, seat_number, booking_date, user_name, phone_number, age, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (bus_id, bus_name, seat_number, date, user_name, phone_number, age, email))
        
        # Update seat availability
        cursor.execute("""
            UPDATE bus_seat_availability 
            SET status = 1 
            WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
        """, (bus_id, seat_number, date))
        
        connection.commit()
        message = "Booking successful!"

        # Check load factor and dynamically add buses if needed
        check_and_add_buses(date)

    except mysql.connector.Error as err:
        message = f"Database error: {err}"
    finally:
        cursor.close()
        connection.close()
    
    return render_template('index.html', message=message)

@app.route('/cancel_booking', methods=['GET', 'POST'])
def cancel_booking():
    if request.method == 'POST':
        bus_id = request.form.get('bus_id')
        seat_number = request.form.get('seat_number')
        date = request.form.get('date')
        user_name = request.form.get('user_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Check if the booking exists
            cursor.execute("""
                SELECT COUNT(*) AS count
                FROM bus_bookings
                WHERE bus_id = %s AND seat_number = %s AND booking_date = %s
                AND user_name = %s AND email = %s AND phone_number = %s
            """, (bus_id, seat_number, date, user_name, email, phone_number))
            result = cursor.fetchone()
            
            if result and result['count'] > 0:
                # Delete booking
                cursor.execute("""
                    DELETE FROM bus_bookings
                    WHERE bus_id = %s AND seat_number = %s AND booking_date = %s
                    AND user_name = %s AND email = %s AND phone_number = %s
                """, (bus_id, seat_number, date, user_name, email, phone_number))
                
                # Update seat availability
                cursor.execute("""
                    UPDATE bus_seat_availability 
                    SET status = 0 
                    WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
                """, (bus_id, seat_number, date))
                
                connection.commit()
                message = "Booking canceled successfully."
            else:
                message = "No matching booking found."
        except mysql.connector.Error as err:
            message = f"Database error: {err}"
        finally:
            cursor.close()
            connection.close()
        
        return render_template('cancel_booking.html', message=message)
    
    return render_template('cancel_booking.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check admin credentials
        cursor.execute("""
            SELECT * FROM admin_users 
            WHERE username = %s AND password = %s
        """, (username, password))
        admin = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if admin:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials, please try again."
    
    return render_template('admin_login.html')

# Function to merge buses
def merge_buses(bus_id_1, bus_id_2, date):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Fetch bookings from bus_id_2 for the given date
        cursor.execute("""
            SELECT seat_number, user_name, phone_number, age, email
            FROM bus_bookings
            WHERE bus_id = %s AND booking_date = %s
        """, (bus_id_2, date))
        bookings_to_merge = cursor.fetchall()
        print(bookings_to_merge)

        if not bookings_to_merge:
            return "No bookings found for bus {} on date {}.".format(bus_id_2, date)

        merge_errors = []

        for booking in bookings_to_merge:
            seat_number = booking[0]

            # Check if seat is available in bus_id_1
            cursor.execute("""
                SELECT status FROM bus_seat_availability
                WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
            """, (bus_id_1, seat_number, date))
            seat_status = cursor.fetchone()

            print(seat_status)


            if seat_status is None:
                merge_errors.append(f"Seat status could not be found for seat {seat_number} in bus {bus_id_1}.")
                continue

            if seat_status[0] == 0:  # Seat is available
                # Transfer booking to bus_id_1
                cursor.execute("""
                    UPDATE bus_bookings
                    SET bus_id = %s, bus_name = (SELECT bus_name FROM buses WHERE bus_id = %s AND date = %s)
                    WHERE bus_id = %s AND seat_number = %s AND booking_date = %s
                """, (bus_id_1, bus_id_1, date, bus_id_2, seat_number, date))

                # Mark seat as booked in bus_id_1
                cursor.execute("""
                    UPDATE bus_seat_availability
                    SET status = 1
                    WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
                """, (bus_id_1, seat_number, date))
            else:
                merge_errors.append(f"Seat {seat_number} is not available in bus {bus_id_1}.")

        if merge_errors:
            return "Merge completed with some errors: " + ", ".join(merge_errors)

        # After merging, mark bus_id_2 as unavailable
        cursor.execute("""
            UPDATE buses
            SET status = 'unavailable'
            WHERE bus_id = %s AND date = %s
        """, (bus_id_2, date))

        connection.commit()
        return f"Bus {bus_id_2} merged successfully into Bus {bus_id_1}."

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        connection.rollback()
        return f"Error merging buses: {err}"

    finally:
        cursor.close()
        connection.close()


# Admin route for merging buses when load factor is low
@app.route('/merge_buses', methods=['POST'])
def admin_merge_buses():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    date = request.form.get('date')
    bus_id_1 = request.form.get('bus_id_1')
    bus_id_2 = request.form.get('bus_id_2')

    message = merge_buses(bus_id_1, bus_id_2, date)
    
    return redirect(url_for('admin_dashboard', message=message, date=date))

# Admin login and dashboard route (with bus merging option)
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    message = None

    if request.method == 'POST':
        if 'bus_id_1' in request.form and 'bus_id_2' in request.form:

            date = request.form.get('date')
            bus_id_1 = request.form.get('bus_id_1')
            bus_id_2 = request.form.get('bus_id_2')

            # Perform bus merging
            merge_message = merge_buses(bus_id_1, bus_id_2, date)
            return render_template('admin_dashboard.html', buses=[], date=date, message=merge_message)
        
        if 'date' in request.form:
            date = request.form.get('date')

            # Fetch buses with load factor below 0.2 for the selected date
            cursor.execute("""
                SELECT bus_id, bus_name, status,
                (SELECT SUM(status) / COUNT(*) FROM bus_seat_availability WHERE bus_id = buses.bus_id AND availability_date = %s) AS load_factor
                FROM buses
                WHERE date = %s AND (SELECT SUM(status) / COUNT(*) FROM bus_seat_availability WHERE bus_id = buses.bus_id AND availability_date = %s) < 0.2
            """, (date, date, date))
            buses_to_merge = cursor.fetchall()

            return render_template('admin_dashboard.html', buses=buses_to_merge, date=date, message=message)

    # Handle GET request to display the date selection form
    return render_template('admin_dashboard.html', buses=[], date=None, message=message)



# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
