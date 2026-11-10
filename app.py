from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Ukraine Alert Map is running!"

@app.route('/api/status')
def status():
    return jsonify({"status": "active", "region": "Ukraine"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
