from flask import Flask, request, jsonify
from threading import Thread
import time

app = Flask(__name__)


def handle_request(data):
    time.sleep(10)
    print(f"Processed data: {data}")

@app.route('/')
def process():
    data = 'Zoho'
    thread = Thread(target=handle_request, args=(data,))
    thread.start()
    return jsonify({"status": "Request is being processed in a separate thread"}), 202

if __name__ == '__main__':
    app.run(threaded=True, debug=True)
