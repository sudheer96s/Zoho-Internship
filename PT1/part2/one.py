from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import cgi
import mysql.connector
import logging

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="bus_booking"
    )

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        # Serving bus seats dynamically
        if path == '/bus_seats':
            busid = query.get('busid', [None])[0]
            if not busid:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing bus ID')
                return

            # Fetch seat information from database
            db_conn = get_db_connection()
            cursor = db_conn.cursor(dictionary=True)
            
            cursor.execute(f"SELECT seat, status FROM bus_{busid}")
            seats = cursor.fetchall()
            cursor.close()
            db_conn.close()

            seat_data = {seat['seat']: seat['status'] for seat in seats}

            # Generate HTML to display bus seats
            html = '<html><head><title>Bus Seats</title></head><body>'
            html += f'<h1>Bus Seats for Bus ID {busid}</h1>'
            html += '<table>'

            # Display 10 rows of 4 seats per row
            for row in range(1, 11):
                html += '<tr>'
                for col in range(1, 5):
                    seat_num = f'{row}-{col}'
                    seat_color = 'green' if seat_data.get(seat_num) == 1 else 'white'
                    html += f'<td><button style="background-color: {seat_color}; width: 50px; height: 50px;" onclick="window.location.href=\'/seat_booking?busid={busid}&seat={seat_num}\'">{seat_num}</button></td>'
                html += '</tr>'
            html += '</table>'
            html += '</body></html>'

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        # Other file serving logic (index, admin, etc.)
        else:
            if path == '/':
                path = '/index.html'
            elif path == '/book':
                path = '/book.html'
            elif path == '/cancel':
                path = '/cancel.html'
            elif path == '/admin':
                path = '/admin.html'
            elif path == '/seat_booking':
                path = '/seat_booking.html'
            else:
                path = '/404.html'

            file_path = '.' + path
            if not os.path.isfile(file_path):
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'404 - Not Found')
                return

            try:
                with open(file_path, 'r') as file:
                    file_to_open = file.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes(file_to_open, 'utf-8'))
            except Exception as e:
                logging.error(f"Error serving file {file_path}: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'500 - Internal Server Error')

    def do_POST(self):
        if self.path == '/submit_booking':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-Type']
            })

            busid = form.getvalue('busid')
            seat = form.getvalue('seat')
            name = form.getvalue('name')
            email = form.getvalue('email')
            phone = form.getvalue('phone')

            try:
                db_conn = get_db_connection()
                cursor = db_conn.cursor()

                # Create table if it doesn't exist
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS bus_{busid} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        seat VARCHAR(10),
                        name VARCHAR(255),
                        email VARCHAR(255),
                        phone VARCHAR(50),
                        bus_id VARCHAR(10),
                        status INT DEFAULT 0,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Insert booking details and update status to 1 (booked)
                cursor.execute(f'''
                    INSERT INTO bus_{busid} (seat, name, email, phone, bus_id, status)
                    VALUES (%s, %s, %s, %s, %s, 1)
                ''', (seat, name, email, phone, busid))

                db_conn.commit()
                cursor.close()
                db_conn.close()

                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Seat booked successfully. <a href="/">Go to Home</a>')

            except mysql.connector.Error as e:
                logging.error(f"Database error: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'500 - Internal Server Error')

        elif self.path == '/cancel_booking':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-Type']
            })

            busid = form.getvalue('busid')
            seat = form.getvalue('seat')
            phone = form.getvalue('phone')

            try:
                db_conn = get_db_connection()
                cursor = db_conn.cursor()

                # Check if booking exists
                cursor.execute(f"SELECT * FROM bus_{busid} WHERE seat = %s AND phone = %s", (seat, phone))
                booking = cursor.fetchone()

                print(booking)

                if booking:
                    # Delete the booking
                    cursor.execute(f"DELETE FROM bus_{busid} WHERE seat = %s AND phone = %s", (seat, phone))
                    db_conn.commit()
                    
                    # Set the status back to 0 (available)
                    cursor.execute(f"UPDATE bus_{busid} SET status = 0 WHERE seat = %s", (seat,))
                    db_conn.commit()

                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'Booking cancelled successfully. <a href="/">Go to Home</a>')
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'Invalid booking details')

                cursor.close()
                db_conn.close()

            except mysql.connector.Error as e:
                logging.error(f"Database error: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'500 - Internal Server Error')


# Run the server on port 8000
httpd = HTTPServer(('', 3000), SimpleHTTPRequestHandler)
print("Serving on port 8000")
httpd.serve_forever()
