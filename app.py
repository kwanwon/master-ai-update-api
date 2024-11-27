from flask import Flask, jsonify, send_file
import os
import sys
from datetime import datetime

app = Flask(__name__)

VERSION_INFO = {
    "version": "1.0.0",
    "release_date": "2023-11-27",
    "description": "초기 버전 릴리스",
    "required": True
}

@app.route('/')
def home():
    return "Master AI Update API"

@app.route('/check_version', methods=['GET'])
def check_version():
    return jsonify(VERSION_INFO)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)