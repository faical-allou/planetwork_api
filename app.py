from flask import Flask, send_file, request, redirect, url_for, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return 'Hello there'