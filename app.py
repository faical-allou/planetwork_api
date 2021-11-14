from flask import Flask, send_file, request, redirect, url_for, abort
from flask_cors import CORS
from werkzeug.serving import WSGIRequestHandler

import os, os.path

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return 'Hello there'


if __name__ == '__main__':

    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    if os.environ.get('ON_HEROKU'):
        port = int(os.environ.get('PORT'))
        print(port)
        app.run(host='0.0.0.0', port=port)
    else :
        print('local')
        app.run(host='0.0.0.0', port=8080, debug=True)