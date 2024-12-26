import socket

def start_client(host='127.0.0.1', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        while True:
            message = input("Enter message to send (or 'exit' to quit): ")
            if message.lower() == 'exit':
                break
            s.sendall(message.encode())
            data = s.recv(1024)
            print(f"Received from server: {data.decode()}")

if __name__ == "__main__":
    start_client()
