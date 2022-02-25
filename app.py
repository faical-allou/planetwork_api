from flask import Flask, request,  send_from_directory
from flask_cors import CORS
from werkzeug.serving import WSGIRequestHandler
import time
import json
from shutil import make_archive, rmtree
import os, os.path

from models.mkshare import *
from models.cost import *




app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './temp/'
app.config['PARAM_FOLDER'] = './param/'
app.config['RESULT_FOLDER'] = './results/'
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
    return send_from_directory(os.path.join(app.config['RESULT_FOLDER']), filename)

@app.route('/download_rp/<analysisname>')
def send_route_prof(analysisname): 
    return send_from_directory(os.path.join(app.config['RESULT_FOLDER'],analysisname), analysisname+"-route_prof.csv")


@app.route('/run/<analysisName>')
def run_mksare(analysisName):
    print('starting')
    max_stop = 1
    time_period = 1

    data, param = mkmod.read_data(os.path.join(app.config['UPLOAD_FOLDER']), os.path.join(app.config['PARAM_FOLDER']), analysisName)
    full_sked, list_itin = mkmod.create_itin(data,param, max_stop)
    list_itin_summary, od_itin = mkmod.build_options(list_itin, max_stop, data['preferences'])
    demand_rand = mkmod.create_demand_set(data, time_period)
    spill, full_sked_rev, list_itin, avail_list_itin = mkmod.allocate_traffic(max_stop, time_period, data["demand"],data['preferences'], full_sked, list_itin, list_itin_summary, od_itin, demand_rand )
    route_prof = costmod.create_route_prof(data, full_sked_rev)

    outputfolder = os.path.join(app.config['RESULT_FOLDER'], analysisName)
    
    rmtree(outputfolder)
    os.mkdir(outputfolder)

    route_prof.to_csv(os.path.join(outputfolder, analysisName+'-route_prof.csv'))
    spill.to_csv(os.path.join(outputfolder, analysisName+'-spill.csv'))
    full_sked_rev.to_csv(os.path.join(outputfolder, analysisName+'-full_sked.csv'))
    list_itin_summary.to_csv(os.path.join(outputfolder, analysisName+'-list_itineraries.csv'))
    
    make_archive(outputfolder, 'zip', outputfolder)

    print('done')
    return 'done'

@app.route('/run/')
def run_nothing():
    return 'Choose an analysis name first'

@app.route('/resultlist/')
def list_results():
    results = set()
    for _filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if _filename[0] == '.' or len(_filename.split('-')) != 2:
                continue 
        results.add(_filename.split('-')[0])

    return json.dumps(list(results))


if __name__ == '__main__':
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    if os.environ.get('ON_HEROKU'):
        port = int(os.environ.get('PORT'))
        print(port)
        app.run(host='0.0.0.0', port=port)
    else :
        print('local')
        app.run(host='0.0.0.0', port=8080, debug=True)