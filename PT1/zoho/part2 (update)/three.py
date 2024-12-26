import mysql.connector
from datetime import datetime, timedelta

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='alnewbooking'
    )

def insert_seat_availability(start_date, end_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Define number of buses and seats per bus
    number_of_buses = 10
    seats_per_bus = 40

    # Iterate through each date and insert data
    current_date = start_date
    while current_date <= end_date:
        for bus_id in range(1, number_of_buses + 1):
            for seat_number in range(1, seats_per_bus + 1):
                # Use INSERT IGNORE to avoid duplicate key errors
                cursor.execute("""
                    INSERT IGNORE INTO bus_seat_availability (bus_id, seat_number, availability_date, status,agent_id)
                    VALUES (%s, %s, %s, %s,%s)
                """, (bus_id, seat_number, current_date, 0,2))  # 0 means available
        
        current_date += timedelta(days=1)

    conn.commit()
    cursor.close()
    conn.close()

# Example usage
start_date = datetime(2024, 9, 27)
end_date = datetime(2024, 10, 2)
insert_seat_availability(start_date, end_date)
