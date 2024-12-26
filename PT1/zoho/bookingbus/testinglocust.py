
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  

    @task
    def access_home(self):
        """Access the home route."""
        response = self.client.get("/")
        if response.status_code == 200:
            print("Home route accessed successfully.")
        else:
            print(f"Failed to access home route with status code: {response.status_code}")

    @task
    def book_seat(self):
        """Simulate booking a seat."""
        data = {
            'bus_id': '1',
            'bus_name': 'Bus 101',
            'seat_number': '12',
            'date': '2024-10-01'
        }
        response = self.client.post("/book", data=data)
        if response.status_code == 200:
            print("Booking request successful.")
        else:
            print(f"Booking failed with status code: {response.status_code}")

    @task
    def confirm_booking(self):
        """Simulate confirming a seat booking."""
        data = {
            'bus_id': '1',
            'bus_name': 'Bus 101',
            'seat_number': '12',
            'date': '2024-10-01',
            'user_name': 'zohouser',
            'phone_number': '1234567890',
            'age': '30',
            'email': 'zohouser@zoho.com'
        }
        response = self.client.post("/confirm_booking", data=data)
        if response.status_code == 200:
            print("Booking confirmed successfully.")
        else:
            print(f"Failed to confirm booking with status code: {response.status_code}")

    @task
    def cancel_booking(self):
        """Simulate canceling a booking."""
        data = {
            'bus_id': '1',
            'seat_number': '12',
            'date': '2024-10-01',
            'user_name': 'zohouser',
            'email': 'zohouser@zoho.com',
            'phone_number': '1234567890'
        }
        response = self.client.post("/cancel_booking", data=data)
        if response.status_code == 200:
            print("Booking canceled successfully.")
        else:
            print(f"Failed to cancel booking with status code: {response.status_code}")
