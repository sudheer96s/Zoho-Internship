import requests

def send_request():
    url = 'http://127.0.0.1:5000/echo'
    data = {'message': 'Hello, server!'}
    response = requests.post(url, json=data)
    print('Server responded with:', response.json())

if __name__ == '__main__':
    send_request()
