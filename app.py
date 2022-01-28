from flask import Flask, request,  send_from_directory
from flask_cors import CORS
from werkzeug.serving import WSGIRequestHandler
import time
from models.mkshare import *

import os, os.path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './temp/'
CORS(app)

mkshareModel = mkshareModel()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/')
def hello():
    return 'Hello there'

@app.route('/upload/<filetype>', methods=['GET', 'POST'])
def upload(filetype):
    if request.method == 'POST':
        file = request.files[filetype]
        analysisName = request.form['analysisName']
        print(analysisName)
        if file:
            filename = analysisName+"-"+filetype
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))       
    return ' upload done'

@app.route('/download/<filename>')
def send_file(filename):
    time.sleep(10)  
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']), filename)

@app.route('/run')
def run_mksare():
    mkshareModel.read_files()
    return 'done'



if __name__ == '__main__':
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    if os.environ.get('ON_HEROKU'):
        port = int(os.environ.get('PORT'))
        print(port)
        app.run(host='0.0.0.0', port=port)
    else :
        print('local')
        app.run(host='0.0.0.0', port=8080, debug=True)