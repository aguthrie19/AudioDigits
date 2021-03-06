# To run, open a virtual python environment and then
# export/set FLASK_ENV=development
# export/set FLASK_APP=./webapp.py
# flask run
# Note to self, file cannot be called app.py because there's a name collision

import os #, requests
from flask import Flask, request, render_template, make_response, jsonify
from werkzeug import secure_filename

from mltools import mfcc_calc
from mltools import clf_SVM
import numpy
from sklearn.externals import joblib

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/train')
def train():
    app.logger.debug("[server] train success")

    with open('./mlresources/X', 'rb') as f:  # with automatically closes the file afterwards
        X = numpy.load(f)
    with open('./mlresources/Y', 'rb') as f:
        Y = numpy.load(f)
    clf, testing_score = clf_SVM(X, Y)
    # persist model
    joblib.dump(clf, './mlresources/model.pkl')

    accuracy = round(testing_score * 100, 2)

    data = jsonify(message='[server] train success', model_accuracy="Model Accuracy: " + str(accuracy))  # Use jsonify because its easiest on the javascript side
    resp = make_response(data, 200)
    return resp

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        app.logger.debug("[server] predict success")

        #get file name
        content = request.get_json()  # makes a python dictionary: content={'clipName': 'myrecording', 'smpLabel': 'zero'}. And on Javascript side is also {'clipName': 'record', 'smpLabel': 'zero'}
        filename = str(content['clipName'])
        filename = filename.replace(":", "") #gotta remove those autogenerated ":"s in the javascript file name. Strings are immutable so we just reassign the output to our original variable.
        print(filename)
        fullname = ['./uploads/',filename,'.wav'] #adding on full path name
        filename = ''.join(str(s) for s in fullname)
        print(filename)

        #Take the file name and load it into python for mfcc and prediction
        clf = joblib.load('./mlresources/model.pkl')  # read model
        x = mfcc_calc(filename)  # MFCC The Newest File
        prediction = str(clf.predict(x))

        #return the results
        data = jsonify(message='[server] predict success', label=content['smpLabel'], predicted=prediction)  # Use jsonify because its easiest on the javascript side
        resp = make_response(data, 200)
        return resp

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    #The Request object
    #http://flask.pocoo.org/docs/1.0/api/#flask.Request
    if request.method == 'POST':

        if 'file' not in request.files:
            app.logger.debug("[server] no file part")
            return '[server] no file part'

        f = request.files['file']

        if f.filename == '':
            app.logger.debug("[server] empty file")
            return '[server] empty file'

        filename = secure_filename(f.filename)

        f.save(os.path.join(app.root_path,'uploads', filename))
        #https://stackoverflow.com/questions/46792270/saving-an-uploaded-file-to-disk-doesnt-work-in-flask

        app.logger.debug("[server] file uploaded")
        return '[server] file uploaded'

        #Other ways to retrieve data from a POST Request
        #forms = request.form
        #f = request.get_data() #gets the entire parameter payload even if cached, better than 'data'
        #f = request.stream #returns a <werkzeug.wsgi.LimitedStream> object for handling in python