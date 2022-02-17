from flask import Flask, request,  send_from_directory
from flask_cors import CORS
from werkzeug.serving import WSGIRequestHandler
import time
from models.mkshare import *
from models.cost import *

import os, os.path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './temp/'
app.config['PARAM_FOLDER'] = './param/'
CORS(app)

mkmod = MkshareModel()
costmod = CostModel()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/')
def hello():
    return 'Hello there Plantework'

@app.route('/upload/<filetype>', methods=['GET', 'POST'])
def upload(filetype):
    if request.method == 'POST':
        file = request.files[filetype]
        analysisName = request.form['analysisName']
        
        if file:
            filename = analysisName+"-"+filetype
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))       
    return ' upload done'

@app.route('/download/<filename>')
def send_file(filename):
    time.sleep(10)  
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']), filename)

@app.route('/run/<analysisName>')
def run_mksare(analysisName):

    max_stop = 1
    time_period = 4

    data, param = mkmod.read_data(os.path.join(app.config['UPLOAD_FOLDER']), os.path.join(app.config['PARAM_FOLDER']), analysisName)
    full_sked, list_itin = mkmod.create_itin(data,param, max_stop)
    list_itin_summary, od_itin = mkmod.build_options(list_itin, max_stop, data['preferences'])
    demand_rand = mkmod.create_demand_set(data, time_period)
    spill, full_sked_rev, list_itin, avail_list_itin = mkmod.allocate_traffic(max_stop, time_period, data["demand"],data['preferences'], full_sked, list_itin, list_itin_summary, od_itin, demand_rand )
    route_prof = costmod.create_route_prof(data, full_sked_rev)
    filename = 'test'+'-route_prof.csv'
    route_prof.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    print('done')
    return 'done'

@app.route('/run/')
def run_nothing():
    return 'Choose an analysis'

if __name__ == '__main__':
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    if os.environ.get('ON_HEROKU'):
        port = int(os.environ.get('PORT'))
        print(port)
        app.run(host='0.0.0.0', port=port)
    else :
        print('local')
        app.run(host='0.0.0.0', port=8080, debug=True)