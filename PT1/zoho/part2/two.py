import mysql.connector
from datetime import datetime, timedelta

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='newbooking'
    )

def insert_bus_data(start_date, end_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Define the bus names and IDs
    bus_names = [f'Bus {i+1}' for i in range(10)]

    # Iterate through each date and insert data
    current_date = start_date
    while current_date <= end_date:
        for bus_id, bus_name in enumerate(bus_names, start=1):
            # Use INSERT IGNORE to avoid duplicate key errors
            cursor.execute("""
                INSERT IGNORE INTO buses (bus_id, bus_name, date, status)
                VALUES (%s, %s, %s, %s)
            """, (bus_id, bus_name, current_date, 'available'))
        
        current_date += timedelta(days=1)

    conn.commit()
    cursor.close()
    conn.close()

# Example usage
start_date = datetime(2024, 9, 17)
end_date = datetime(2024, 9, 30)
insert_bus_data(start_date, end_date)
