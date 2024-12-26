import threading
import multiprocessing
import time
import logging
import random
from queue import Queue
import psutil
import os
import hashlib
from datetime import datetime, timedelta

# Constants
BUS_CAPACITY = 50
LOAD_FACTOR_THRESHOLD = 0.8
MIN_THRESHOLD = 0.2
INITIAL_BUSES = 10
MAX_BUSES = 100
WAIT_TIME = 300  # 5 minutes in seconds for seat reservation
RESERVE_TIMEOUT = 10  # Seat hold time for reservation in seconds

# Initialize logging
logging.basicConfig(filename='bus_booking_archive.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Global Variables
visitor_count = 0
lock = threading.Lock()
admin_password_hash = hashlib.sha256("admin123".encode()).hexdigest()

# Monitoring CPU, memory, and idle time
def monitor_resources():
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = process.memory_info()
    idle_time = psutil.cpu_times().idle
    return cpu_usage, memory_info.vms, memory_info.rss, idle_time

# Periodic resource monitoring with CPU idle time
def periodic_monitoring():
    while True:
        cpu_usage, virtual_mem, physical_mem, idle_time = monitor_resources()
        logging.info(f"Periodic Monitor: CPU Usage: {cpu_usage}%, Virtual Memory: {virtual_mem} bytes, "
                     f"Physical Memory: {physical_mem} bytes, CPU Idle Time: {idle_time}")
        time.sleep(10)  # Logs every 10 seconds

# Disk I/O measurement function
def log_performance(file_write_time):
    logging.info(f"Disk I/O: File write time = {file_write_time} seconds")

# Bus class
class Bus:
    def __init__(self, bus_id, capacity=BUS_CAPACITY):
        self.bus_id = bus_id
        self.capacity = capacity
        self.seats = [False] * capacity  # False means seat is available
        self.reserved = [False] * capacity  # Temporary reservation
        self.lock = threading.Lock()  # Lock for each bus
        self.alteration_in_process = False

    def book_seat(self, seat_number):
        with self.lock:
            if self.alteration_in_process:
                logging.info(f"Bus {self.bus_id} alteration in process. Seat booking suspended.")
                return False

            if self.seats[seat_number]:
                return False  # Seat already booked
            else:
                self.seats[seat_number] = True
                logging.info(f"Seat {seat_number} booked on Bus {self.bus_id}")
                return True

    def cancel_seat(self, seat_number):
        with self.lock:
            if self.seats[seat_number]:
                self.seats[seat_number] = False
                logging.info(f"Seat {seat_number} canceled on Bus {self.bus_id}")
                return True
            return False

    def reserve_seat(self, seat_number):
        with self.lock:
            if not self.seats[seat_number] and not self.reserved[seat_number]:
                self.reserved[seat_number] = True
                logging.info(f"Seat {seat_number} reserved temporarily on Bus {self.bus_id}")
                return True
            return False

    def release_reservation(self, seat_number):
        with self.lock:
            self.reserved[seat_number] = False
            logging.info(f"Seat {seat_number} reservation released on Bus {self.bus_id}")

    def get_load_factor(self):
        return sum(self.seats) / self.capacity

    def start_alteration(self):
        with self.lock:
            self.alteration_in_process = True
            logging.info(f"Bus {self.bus_id}: Bus alteration in process...")

    def stop_alteration(self):
        with self.lock:
            self.alteration_in_process = False
            logging.info(f"Bus {self.bus_id}: Bus alteration finished.")

# Bus Manager Class
class BusManager:
    def __init__(self):
        self.buses = [Bus(bus_id=i) for i in range(INITIAL_BUSES)]
        self.max_buses = MAX_BUSES
        self.lock = threading.Lock()

    def get_available_buses(self):
        return [bus for bus in self.buses if any(not seat for seat in bus.seats)]

    def add_bus(self):
        with self.lock:
            if len(self.buses) < self.max_buses:
                new_bus = Bus(bus_id=len(self.buses))
                self.buses.append(new_bus)
                logging.info(f"New bus added. Total buses: {len(self.buses)}")
            else:
                logging.warning("Maximum number of buses reached.")

    def merge_buses(self):
        with self.lock:
            logging.info("Bus merging started.")
            available_buses = [bus for bus in self.buses if bus.get_load_factor() < MIN_THRESHOLD]
            for bus in available_buses:
                bus.start_alteration()
                time.sleep(2)  # Simulate time for bus merging
                bus.stop_alteration()

    def check_load_factor_and_add(self):
        total_seats = sum([bus.capacity for bus in self.buses])
        booked_seats = sum([sum(bus.seats) for bus in self.buses])
        load_factor = booked_seats / total_seats

        if load_factor >= LOAD_FACTOR_THRESHOLD and len(self.buses) < self.max_buses:
            self.add_bus()

    def get_total_load_factor(self):
        total_seats = sum([bus.capacity for bus in self.buses])
        booked_seats = sum([sum(bus.seats) for bus in self.buses])
        return booked_seats / total_seats if total_seats > 0 else 0

# Admin Class
class Admin:
    def __init__(self, bus_manager):
        self.bus_manager = bus_manager

    def login(self):
        password = input("Enter admin password: ")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash == admin_password_hash:
            return True
        else:
            logging.info("Invalid admin password attempt.")
            return False

    def merge_buses_if_needed(self):
        self.bus_manager.merge_buses()

# Client class simulating bus booking
class Client(threading.Thread):
    def __init__(self, client_id, bus_manager, day, seat_number):
        threading.Thread.__init__(self)
        self.client_id = client_id
        self.bus_manager = bus_manager
        self.day = day
        self.seat_number = seat_number

    def run(self):
        global visitor_count
        with lock:
            visitor_count += 1

        buses = self.bus_manager.get_available_buses()
        if buses:
            bus = random.choice(buses)  # Choose a random available bus
            if bus.reserve_seat(self.seat_number):
                logging.info(f"Client {self.client_id} reserved seat {self.seat_number} on bus {bus.bus_id} for day {self.day}")
                time.sleep(RESERVE_TIMEOUT)  # Simulating time client has to confirm
                if bus.book_seat(self.seat_number):
                    logging.info(f"Client {self.client_id} confirmed booking of seat {self.seat_number} on bus {bus.bus_id}")
                else:
                    logging.info(f"Client {self.client_id} failed to confirm booking of seat {self.seat_number}, seat already taken.")
            else:
                logging.info(f"Client {self.client_id} failed to reserve seat {self.seat_number}, already reserved or booked.")
        else:
            logging.info(f"No available buses for Client {self.client_id}.")

# CPU/Memory Resource monitoring
def monitor_system_resources():
    cpu_usage, virtual_mem, physical_mem, idle_time = monitor_resources()
    logging.info(f"CPU Usage: {cpu_usage}%, Virtual Memory: {virtual_mem} bytes, Physical Memory: {physical_mem} bytes, CPU Idle Time: {idle_time}")

# Simulate multiple agents booking with multiprocessing
def agent_booking_process(client_id, bus_manager, day, seat_number):
    client = Client(client_id, bus_manager, day, seat_number)
    client.run()

# Main function
def main():
    bus_manager = BusManager()
    admin = Admin(bus_manager)

    # Start periodic resource monitoring
    monitor_thread = threading.Thread(target=periodic_monitoring, daemon=True)
    monitor_thread.start()

    # Create multiprocessing pool for simulating multiple clients
    with multiprocessing.Pool(processes=5) as pool:
        pool.starmap(agent_booking_process, [(i, bus_manager, "2024-09-15", random.randint(0, BUS_CAPACITY-1)) for i in range(10)])

    # Admin login and merging if needed
    if admin.login():
        admin.merge_buses_if_needed()

    # Check load factor and add new buses if necessary
    bus_manager.check_load_factor_and_add()

    # Log total visitors
    logging.info(f"Total visitors: {visitor_count}")

    # Monitor system resources (CPU, memory)
    monitor_system_resources()

if __name__ == "__main__":
    main()
