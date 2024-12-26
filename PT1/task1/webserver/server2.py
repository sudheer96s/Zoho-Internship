from flask import Flask, jsonify
import time

app = Flask(__name__)

def handle_request(data):
    time.sleep(20)
    print(f"Processed data: {data}")

@app.route('/')
def process():
    data = 'Zoho'
    # Directly call the handle_request function
    handle_request(data)
    return jsonify({"status": "Request has been processed"}), 200

if __name__ == '__main__':
    app.run(debug=True)
