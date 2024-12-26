import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session,flash
import logging
import threading
import time
from datetime import datetime, timedelta
from logging import handlers
from functools import wraps
from mysql.connector import Error
from mysql.connector import pooling
# gunicorn -w 8 -b 127.0.0.1:5000 14:app

seat_locks = {}


log_file = 'logging.txt'
log_handler = handlers.RotatingFileHandler(
    log_file, maxBytes=5*1024*1024, backupCount=10
)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'sudheer5'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
app.config['MYSQL_DATABASE_CONNECT_TIMEOUT'] = 30 

dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "bookingbus"
}

connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=32,  
    **dbconfig
)

def get_db_connection():
    connection = connection_pool.get_connection()  
    logging.info('Database connection established from pool.')
    return connection


connection = get_db_connection()
cursor = connection.cursor(dictionary=True)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']  
        
        try:
            sql = "INSERT INTO users1 (username, password, email) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, password, email)) 
            connection.commit()
            flash('You have successfully registered!', 'success')
            return redirect(url_for('login'))
        
        except Error as e:
            print(f"Error: {e}")
            flash('Registration failed due to a database error. Please try again.', 'danger')
        
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(username, password)

        cursor.execute("SELECT * FROM users1 WHERE username = %s", (username,))
        user = cursor.fetchone()  

        print(f"User fetched: {user}") 


        if user:
            print(f"Stored Password: {user['password']}, Entered Password: {password}")  
            if user['password'] == password:  
                session['logged_in'] = True
                session['username'] = user['username']  
                flash('You are logged in!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid password!', 'danger')
        else:
            flash('User not found!', 'danger')

    return render_template('login.html')





@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('You need to log in first!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def check_and_add_buses(date):  
    logging.debug(f'Checking and adding buses for date: {date}')

    try:
        cursor.execute("""
            SELECT SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) / COUNT(*) AS load_factor
            FROM bus_seat_availability
            WHERE availability_date = %s
        """, (date,))
        load_factor = cursor.fetchone()['load_factor']
        logging.info(f'Load factor for date {date}: {load_factor}')

        if load_factor > 0.79:
            cursor.execute("SELECT COUNT(*) AS total_buses FROM buses WHERE date = %s", (date,))
            total_buses = cursor.fetchone()['total_buses']
            logging.info(f'Total buses for date {date}: {total_buses}')
            
            if total_buses < 101:
                buses_to_add = 2
                for _ in range(buses_to_add):
                    cursor.execute("""
                        INSERT INTO buses (bus_id,bus_name, date, status)
                        VALUES (%s,%s, %s, 'available')
                    """, (total_buses+1,f"Bus {total_buses + 1}", date))
                    total_buses += 1
                    for seat_number in range(1, 41):
                        cursor.execute("""
                            INSERT IGNORE INTO bus_seat_availability (bus_id, seat_number, availability_date, status)
                            VALUES (%s, %s, %s, %s)
                        """, (total_buses, seat_number, date, 0))
                connection.commit()
                logging.info(f'Added {buses_to_add} buses for date {date}.')
    except mysql.connector.Error as err:
        logging.error(f'Database error: {err}')

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    logging.debug('Home route accessed.')

    try:
        cursor.execute("SELECT count FROM visitor_count WHERE id = 1")
        result = cursor.fetchone()
        print(result)
        if result:
            visitor_count = result['count'] + 1
            cursor.execute("UPDATE visitor_count SET count = %s WHERE id = 1", (visitor_count,))
        else:
            visitor_count = 1
            cursor.execute("INSERT INTO visitor_count (count) VALUES (%s)", (visitor_count,))
        connection.commit()
        logging.info(f'Visitor count updated to {visitor_count}.')
        
        if request.method == 'POST':
            date = request.form.get('date')
            session['selected_date'] = date

            cursor.execute("""
                SELECT bus_id, bus_name, status
                FROM buses
                WHERE date = %s
            """, (date,))
            buses = cursor.fetchall()
            if not buses:
                total_buses = 0  
                for _ in range(10): 
                    cursor.execute("""
                        INSERT INTO buses (bus_id, bus_name, date, status)
                        VALUES (%s, %s, %s, 'available')
                    """, (total_buses+1, f"Bus {total_buses + 1}", date))
                    total_buses += 1
                    for seat_number in range(1, 41):  
                        cursor.execute("""
                            INSERT IGNORE INTO bus_seat_availability (bus_id, seat_number, availability_date, status)
                            VALUES (%s, %s, %s, %s)
                        """, (total_buses, seat_number, date, 0))

                connection.commit()
                logging.info(f'New buses and seats added for date {date}.')

                cursor.execute("""
                    SELECT bus_id, bus_name, status
                    FROM buses
                    WHERE date = %s
                """, (date,))
                buses = cursor.fetchall()

            for bus in buses:
                if bus['status'] == 'unavailable':
                    bus['status_message'] = 'Bus alteration in process'
                else:
                    bus['status_message'] = 'Available'

            logging.info(f'Buses for date {date} fetched and checked.')
            return render_template('index.html', buses=buses, visitor_count=visitor_count, selected_date=date)
        
        session['visitor_count'] = visitor_count
        logging.info(f'Visitor count set in session: {visitor_count}.')
        return render_template('index.html', buses=[], visitor_count=visitor_count, selected_date=None)
    
    except mysql.connector.Error as err:
        logging.error(f'Database error: {err}')
        return render_template('error.html', error_message=f"Database error: {err}")

@app.route('/view_seats', methods=['POST'])
@login_required
def view_seats():
    date = request.form.get('date')
    bus_id = request.form.get('bus_id')

    cursor = connection.cursor(dictionary=True,buffered=True)  

    try:
        cursor.execute("""
            SELECT bus_name FROM buses WHERE bus_id = %s
        """, (bus_id,))
        bus = cursor.fetchone()  
        
        if bus is None:
            logging.warning(f'Bus with ID {bus_id} not found.')
            return "Bus not found.", 404
        
        cursor.execute("""
            SELECT bsa.seat_number, bsa.status 
            FROM bus_seat_availability AS bsa
            JOIN buses AS b ON bsa.bus_id = b.bus_id
            WHERE bsa.bus_id = %s 
              AND bsa.availability_date = %s
              AND b.status = 'available' AND b.date = %s
        """, (bus_id, date, date))

        seats = cursor.fetchall()  
        logging.info(f'Seats for bus {bus_id} on date {date} fetched.')

    except mysql.connector.Error as err:
        logging.error(f'Database error: {err}')
        return f"Error: {err}", 500
    return render_template('view_seats.html', seats=seats, bus_id=bus_id, bus_name=bus['bus_name'], date=date)



@app.route('/book', methods=['POST'])
@login_required
def book():
    bus_id = request.form.get('bus_id')
    bus_name = request.form.get('bus_name')
    seat_number = request.form.get('seat_number')
    date = request.form.get('date')

    logging.debug(f'Booking request: bus_id={bus_id}, seat_number={seat_number}, date={date}')

    lock_key = (bus_id, seat_number, date)

    if lock_key not in seat_locks:
        seat_locks[lock_key] = threading.Lock()

    with seat_locks[lock_key]:
        
        try:
            cursor.execute("""
                SELECT status FROM bus_seat_availability
                WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
            """, (bus_id, seat_number, date))
            seat_status = cursor.fetchone()

            if seat_status is None:
                logging.warning(f'Seat not found: bus_id={bus_id}, seat_number={seat_number}, date={date}')
                return "Seat not found.", 404

            seat_status = seat_status['status']

            if seat_status == 1:
                logging.warning(f'Seat already booked: bus_id={bus_id}, seat_number={seat_number}, date={date}')
                return "Seat is already booked.", 400
            elif seat_status == 2:
                logging.warning(f'Seat in waiting state: bus_id={bus_id}, seat_number={seat_number}, date={date}')
                return "Seat is currently in waiting state.", 400

            cursor.execute("""
                UPDATE bus_seat_availability 
                SET status = 2 
                WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
            """, (bus_id, seat_number, date))

            connection.commit()

            def release_seat():
                time.sleep(300)
                with seat_locks[lock_key]:
                    
                    
                    cursor.execute("""
                        SELECT status FROM bus_seat_availability
                        WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
                    """, (bus_id, seat_number, date))
                    seat_status = cursor.fetchone()
                    if seat_status and seat_status['status'] == 2:
                        cursor.execute("""
                            UPDATE bus_seat_availability 
                            SET status = 0 
                            WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
                        """, (bus_id, seat_number, date))
                        connection.commit()
            
            threading.Thread(target=release_seat).start()

            message = "Seat is in waiting state. Please confirm booking within 5 minutes."

        except mysql.connector.Error as err:
            logging.error(f'Database error: {err}')
            message = f"Database error: {err}"


    return render_template('show_booking_details.html', date=date, bus_id=bus_id, bus_name=bus_name, seat_number=seat_number, message=message)

@app.route('/show_booking_details', methods=['POST'])
@login_required
def show_booking_details():
    date = request.form.get('date')
    bus_id = request.form.get('bus_id')
    bus_name = request.form.get('bus_name')
    seat_number = request.form.get('seat_number')

    logging.info(f'Show booking details: date={date}, bus_id={bus_id}, seat_number={seat_number}')

    return render_template('show_booking_details.html', date=date, bus_id=bus_id, bus_name=bus_name, seat_number=seat_number)

@app.route('/confirm_booking', methods=['POST'])
@login_required
def confirm_booking():
    bus_id = request.form.get('bus_id')
    bus_name = request.form.get('bus_name')
    seat_number = request.form.get('seat_number')
    date = request.form.get('date')
    user_name = request.form.get('user_name')
    phone_number = request.form.get('phone_number')
    age = request.form.get('age')
    email = request.form.get('email')
    
    logging.info(f"Attempting to confirm booking: bus_id={bus_id}, seat_number={seat_number}, date={date}, user_name={user_name}")
    
    try:
        cursor.execute("""
            SELECT * FROM bus_bookings
            WHERE bus_id = %s AND booking_date = %s AND (user_name = %s OR email = %s)
        """, (bus_id, date, user_name, email))
        existing_booking = cursor.fetchone()
        
        if existing_booking:
            logging.warning(f"User already has a booking for this bus on this date: bus_id={bus_id}, user_name={user_name}")
            return "You have already booked a seat on this bus for the selected date.", 400

        cursor.execute("""
            SELECT status FROM bus_seat_availability
            WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
        """, (bus_id, seat_number, date))
        seat_status = cursor.fetchone()
        
        if seat_status is None:
            logging.error(f"Seat not found: bus_id={bus_id}, seat_number={seat_number}, date={date}")
            return "Seat not found.", 404
        
        if seat_status['status'] == 1:
            logging.warning(f"Seat is already booked: bus_id={bus_id}, seat_number={seat_number}, date={date}")
            return "Seat is already booked.", 400
        elif seat_status['status'] == 0 or seat_status['status'] == 2:
            cursor.execute("""
                UPDATE bus_seat_availability
                SET status = 1
                WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
            """, (bus_id, seat_number, date))
            
            cursor.execute("""
                INSERT INTO bus_bookings (bus_id, bus_name, seat_number, booking_date, user_name, phone_number, age, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (bus_id, bus_name, seat_number, date, user_name, phone_number, age, email))
            
            connection.commit()
            message = "Booking confirmed successfully."
            logging.info(f"Booking confirmed: bus_id={bus_id}, seat_number={seat_number}, date={date}, user_name={user_name}")
        else:
            logging.error(f"Seat status is not available: bus_id={bus_id}, seat_number={seat_number}, date={date}")
            return "Seat is available but not in waiting state.", 400
        
    except mysql.connector.Error as err:
        message = f"Database error: {err}"
        logging.error(message)    
    return render_template('booking_confirmation.html', message=message)


@app.route('/cancel_booking', methods=['GET', 'POST'])
@login_required
def cancel_booking():
    if request.method == 'POST':
        bus_id = request.form.get('bus_id')
        seat_number = request.form.get('seat_number')
        date = request.form.get('date')
        user_name = request.form.get('user_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        
        
        
        try:
            cursor.execute("""
                SELECT COUNT(*) AS count
                FROM bus_bookings
                WHERE bus_id = %s AND seat_number = %s AND booking_date = %s
                AND user_name = %s AND email = %s AND phone_number = %s
            """, (bus_id, seat_number, date, user_name, email, phone_number))
            result = cursor.fetchone()
            
            if result and result['count'] > 0:
                cursor.execute("""
                    DELETE FROM bus_bookings
                    WHERE bus_id = %s AND seat_number = %s AND booking_date = %s
                    AND user_name = %s AND email = %s AND phone_number = %s
                """, (bus_id, seat_number, date, user_name, email, phone_number))
    
                cursor.execute("""
                    UPDATE bus_seat_availability 
                    SET status = 0 
                    WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
                """, (bus_id, seat_number, date))
                
                connection.commit()
                message = "Booking canceled successfully."
                logging.info(f"Booking canceled successfully for bus_id: {bus_id}, seat_number: {seat_number}, date: {date}.")
            else:
                message = "No matching booking found."
                logging.warning(f"No matching booking found for bus_id: {bus_id}, seat_number: {seat_number}, date: {date}.")
        except mysql.connector.Error as err:
            message = f"Database error: {err}"
            logging.error(f"Database error during booking cancellation: {err}")
        
        return render_template('cancel_booking.html', message=message)
    
    return render_template('cancel_booking.html')


def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Session data:", session)  
        
        if not session.get('logged_in'):
            logging.warning('Access denied: admin not logged in.')
            return redirect(url_for('admin_login'))  
        
        logging.info('Admin is logged in, allowing access to admin dashboard.')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            cursor.execute("""
                SELECT * FROM admin_users 
                WHERE username = %s AND password = %s
            """, (username, password))
            admin = cursor.fetchone()

            if admin:
                session['logged_in'] = True  
                session.permanent = True
                print("Session after login:", session)  
                logging.info(f'Admin login successful for user: {username}')
                return redirect(url_for('admin_dashboard'))
            else:
                logging.warning(f'Invalid credentials attempt for user: {username}')
                return "Invalid credentials, please try again."
        except mysql.connector.Error as err:
            logging.error(f'Database error during admin login: {err}')

    return render_template('admin_login.html')

def merge_buses(bus_id_1, bus_id_2, date):
    try:
        cursor.execute("""
            SELECT seat_number, user_name, phone_number, age, email
            FROM bus_bookings
            WHERE bus_id = %s AND booking_date = %s
        """, (bus_id_2, date))
        bookings_to_merge = cursor.fetchall()

        if not bookings_to_merge:
            logging.info(f'No bookings found for bus {bus_id_2} on date {date}.')
            return "No bookings found for bus {} on date {}.".format(bus_id_2, date)

        merge_errors = []

        for booking in bookings_to_merge:
            seat_number = booking['seat_number'] 
            cursor.execute("""
                SELECT status FROM bus_seat_availability
                WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
            """, (bus_id_1, seat_number, date))
            seat_status = cursor.fetchone()

            if seat_status is None:
                merge_errors.append(f"Seat status could not be found for seat {seat_number} in bus {bus_id_1}.")
                logging.warning(f"Seat status could not be found for seat {seat_number} in bus {bus_id_1}.")
                continue

            if seat_status['status'] == 0:  
                cursor.execute("""
                    UPDATE bus_bookings
                    SET bus_id = %s, bus_name = (SELECT bus_name FROM buses WHERE bus_id = %s AND date = %s)
                    WHERE bus_id = %s AND seat_number = %s AND booking_date = %s
                """, (bus_id_1, bus_id_1, date, bus_id_2, seat_number, date))

                cursor.execute("""
                    UPDATE bus_seat_availability
                    SET status = 1
                    WHERE bus_id = %s AND seat_number = %s AND availability_date = %s
                """, (bus_id_1, seat_number, date))
            else:
                merge_errors.append(f"Seat {seat_number} is not available in bus {bus_id_1}.")
                logging.warning(f"Seat {seat_number} is not available in bus {bus_id_1}.")

        if merge_errors:
            logging.info(f'Merge completed with some errors: {", ".join(merge_errors)}')
            return "Merge completed with some errors: " + ", ".join(merge_errors)

        cursor.execute("""
            UPDATE buses
            SET status = 'unavailable'
            WHERE bus_id = %s AND date = %s
        """, (bus_id_2, date))

        connection.commit()
        logging.info(f'Bus {bus_id_2} merged successfully into Bus {bus_id_1}.')
        return f"Bus {bus_id_2} merged successfully into Bus {bus_id_1}."

    except mysql.connector.Error as err:
        logging.error(f'Error merging buses: {err}')
        connection.rollback()
        return f"Error merging buses: {err}"

 



@app.route('/merge_buses', methods=['POST'])
def admin_merge_buses():
    if not session.get('logged_in'):
        logging.warning('Unauthorized access attempt to merge buses.')
        return redirect(url_for('admin_login'))

    date = request.form.get('date')
    bus_id_1 = request.form.get('bus_id_1')
    bus_id_2 = request.form.get('bus_id_2')
    message = merge_buses(bus_id_1, bus_id_2, date)
    logging.info(f'Bus merge request: {bus_id_1} with {bus_id_2} on date {date}. Message: {message}')
    
    return redirect(url_for('admin_dashboard', message=message, date=date))



@app.route('/admin_dashboard', methods=['GET', 'POST'])
@admin_login_required  
def admin_dashboard():
    
    
    message = None

    if request.method == 'POST':
        if 'bus_id_1' in request.form and 'bus_id_2' in request.form:
            date = request.form.get('date')
            bus_id_1 = request.form.get('bus_id_1')
            bus_id_2 = request.form.get('bus_id_2')

            merge_message = merge_buses(bus_id_1, bus_id_2, date)
            logging.info(f'Bus merge performed: {bus_id_1} with {bus_id_2} on date {date}. Message: {merge_message}')
            return render_template('admin_dashboard.html', buses=[], date=date, message=merge_message)
        
        if 'date' in request.form:
            date = request.form.get('date')

            cursor.execute("""
                SELECT bus_id, bus_name, status,
                (SELECT SUM(status) / COUNT(*) FROM bus_seat_availability WHERE bus_id = buses.bus_id AND availability_date = %s) AS load_factor
                FROM buses
                WHERE date = %s AND (SELECT SUM(status) / COUNT(*) FROM bus_seat_availability WHERE bus_id = buses.bus_id AND availability_date = %s) < 0.2
            """, (date, date, date))
            buses_to_merge = cursor.fetchall()
            logging.info(f'Fetched buses with load factor below 0.2 for date {date}.')
            return render_template('admin_dashboard.html', buses=buses_to_merge, date=date, message=message)

    logging.info('Rendering admin dashboard with date selection form.')
    return render_template('admin_dashboard.html', buses=[], date=None, message=message)




def simulate_booking(date, bus_id, seat_number, user_name, phone_number, age, email):
    with app.app_context():
        with app.test_request_context('/book', method='POST', data={
            'bus_id': bus_id,
            'bus_name': 'Test Bus',
            'seat_number': seat_number,
            'date': date,
            'user_name': user_name,
            'phone_number': phone_number,
            'age': age,
            'email': email
        }):
            app.preprocess_request()
            app.dispatch_request()

@app.route('/simulate_bookings', methods=['POST'])
def simulate_bookings():
    date = request.form.get('date')
    bus_id = request.form.get('bus_id')
    seat_number = request.form.get('seat_number')
    

    threads = []
    for i in range(15):  
        t = threading.Thread(target=simulate_booking, args=(date, bus_id, seat_number, f'User{i}', f'123456789{i}', 25+i, f'user{i}@example.com'))
        t.start()
        threads.append(t)
    

    for t in threads:
        t.join()
    
    logging.info(f'Simulation of bookings complete for date {date}, bus_id {bus_id}, seat_number {seat_number}.')
    return "Simulation complete."

if __name__ == '__main__':
    app.run(debug=False, threaded=True)
