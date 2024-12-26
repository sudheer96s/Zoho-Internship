from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import mysql.connector
import cgi
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
# Database setup
def setup_database():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="sudheer"
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        first_name VARCHAR(255),
                        last_name VARCHAR(255),
                        dob DATE,
                        place VARCHAR(255)
                    )''')
    conn.commit()
    cursor.close()
    conn.close()

setup_database()

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.path = '/home.html'
        elif self.path == '/index3.html':
            self.path = '/index3.html'
        elif self.path == '/delete.html':
            self.path = '/delete.html'
        elif self.path == '/update.html':
            self.path = '/update.html'
        elif self.path == 'search.html':
            self.path = '/search.html'

        try:
            file_to_open = open(self.path[1:]).read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(file_to_open, 'utf-8'))
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'404 - Not Found')

    def do_POST(self):
        # Determine if the request is for adding or deleting data
        if self.path == '/index3':
            self.handle_add()
        elif self.path == '/delete':
            self.handle_delete()
        elif self.path == '/update':
            self.handle_update()
        elif self.path == '/search':
            self.handle_search()

    def handle_add(self):
        # Parse the form data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],
                     }
        )

        # Get the form values
        first_name = form.getvalue("first_name")
        last_name = form.getvalue("last_name")
        dob = form.getvalue("dob")  # Expected format: 'YYYY-MM-DD'
        place = form.getvalue("place")

        # Save to the MySQL database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="sudheer"
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (first_name, last_name, dob, place) VALUES (%s, %s, %s, %s)",
                       (first_name, last_name, dob, place))
        conn.commit()
        cursor.close()
        conn.close()

        # Respond to the client
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Hello, ' + first_name.encode() + b' ' + last_name.encode() + b' from ' + place.encode())

    def handle_delete(self):
        # Parse the form data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],
                     }
        )

        # Get the form values
        first_name = form.getvalue("first_name")
        last_name = form.getvalue("last_name")

        # Delete from the MySQL database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="sudheer"
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE first_name=%s AND last_name=%s",
                       (first_name, last_name))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()

        # Respond to the client
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        if affected_rows > 0:
            self.wfile.write(b'Deleted ' + first_name.encode() + b' ' + last_name.encode() + b' from the database.')
        else:
            self.wfile.write(b'No record found for ' + first_name.encode() + b' ' + last_name.encode() + b'.')

    def handle_update(self):
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': self.headers['Content-Type'],
                        }
            )
            search_first_name = form.getvalue("search_first_name")
            search_last_name = form.getvalue("search_last_name")
            new_first_name = form.getvalue("new_first_name")
            new_last_name = form.getvalue("new_last_name")
            new_dob = form.getvalue("new_dob")
            new_place = form.getvalue("new_place")

            logging.info(f"Update request: search_first_name={search_first_name}, search_last_name={search_last_name}, new_first_name={new_first_name}, new_last_name={new_last_name}, new_dob={new_dob}, new_place={new_place}")

            
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root",
                database="sudheer"
            )
            cursor = conn.cursor()

            update_fields = []
            update_values = []
            if new_first_name:
                update_fields.append("first_name = %s")
                update_values.append(new_first_name)
            if new_last_name:
                update_fields.append("last_name = %s")
                update_values.append(new_last_name)
            if new_dob:
                update_fields.append("dob = %s")
                update_values.append(new_dob)
            if new_place:
                update_fields.append("place = %s")
                update_values.append(new_place)

            update_values.append(search_first_name)
            update_values.append(search_last_name)

            if update_fields:
                cursor.execute(f"UPDATE users SET {', '.join(update_fields)} WHERE first_name=%s AND last_name=%s", tuple(update_values))
                conn.commit()

            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            if affected_rows > 0:
                self.wfile.write(b'Updated details for ' + search_first_name.encode() + b' ' + search_last_name.encode())
            else:
                self.wfile.write(b'No record found for ' + search_first_name.encode() + b' ' + search_last_name.encode())

        except Exception as e:
            print(e)
            logging.error(f"Error in update handling: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Internal Server Error')


    def handle_search(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                    }
        )
        first_name = form.getvalue("first_name")
        last_name = form.getvalue("last_name")

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="sudheer"
        )
        cursor = conn.cursor()

        if first_name and last_name:
            cursor.execute("SELECT * FROM users WHERE first_name=%s AND last_name=%s", (first_name, last_name))
        elif first_name:
            cursor.execute("SELECT * FROM users WHERE first_name=%s", (first_name,))
        elif last_name:
            cursor.execute("SELECT * FROM users WHERE last_name=%s", (last_name,))
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Error: At least one search field must be provided.')
            cursor.close()
            conn.close()
            return

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if results:
            response_html = '<h1>Search Results</h1><ul>'
            for row in results:
                response_html += f'<li>ID: {row[0]}, First Name: {row[1]}, Last Name: {row[2]}, DOB: {row[3]}, Place: {row[4]}</li>'
            response_html += '</ul>'
        else:
            response_html = '<h1>No results found</h1>'

        self.wfile.write(response_html.encode('utf-8'))



def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}...')
    httpd.serve_forever()

# Enable threading for the HTTP server
class ThreadedHTTPServer(HTTPServer):
    def process_request(self, request, client_address):
        thread = threading.Thread(target=self.finish_request, args=(request, client_address))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    run(server_class=ThreadedHTTPServer)
