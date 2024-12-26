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
        
        # Fetch available buses for the selected date
        cursor.execute("""
            SELECT bus_id, bus_name
            FROM buses
            WHERE date = %s AND status = 'available'
        """, (date,))
        buses = cursor.fetchall()
        
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

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch buses
    cursor.execute("""
        SELECT bus_id, bus_name, date, status 
        FROM buses
    """)
    buses = cursor.fetchall()
    
    # Calculate load factor
    cursor.execute("""
        SELECT SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) / COUNT(*) AS load_factor
        FROM bus_seat_availability
        WHERE availability_date = CURDATE()
    """)
    load_factor = cursor.fetchone()['load_factor']
    
    cursor.close()
    connection.close()
    
    return render_template('admin_dashboard.html', buses=buses, load_factor=load_factor)

if __name__ == '__main__':
    app.run(debug=True)
