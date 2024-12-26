import mysql.connector
from datetime import datetime, timedelta

# Database connection
db = mysql.connector.connect(
    host='localhost',
        user='root',
        password='root',
        database='alnewbooking'
)

cursor = db.cursor()

# Starting and ending dates
start_date = datetime.strptime('2024-09-25', '%Y-%m-%d')
end_date = datetime.strptime('2024-09-30', '%Y-%m-%d')

# Number of buses
num_buses = 10
agent_id = 2  # Set the agent ID for the buses

# Insert buses for each date in the range
current_date = start_date
bus_counter = 1  # Unique bus ID for each insertion

while current_date <= end_date:
    for bus_num in range(1, num_buses + 1):
        bus_id = bus_counter  # Ensure each bus_id is unique
        bus_name = f"Bus {bus_num}"
        
        try:
            cursor.execute("""
                INSERT INTO buses (bus_id, bus_name, date, status, agent_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (bus_id, bus_name, current_date.strftime('%Y-%m-%d'), 'available', agent_id))
            
            bus_counter += 1  # Increment the unique bus_id for each new insertion

        except mysql.connector.errors.IntegrityError as e:
            print(f"Error inserting bus_id {bus_id} for {current_date.strftime('%Y-%m-%d')}: {e}")
    
    current_date += timedelta(days=1)

# Commit changes to the database
db.commit()

# Close the database connection
cursor.close()
db.close()

print("Data inserted successfully!")
