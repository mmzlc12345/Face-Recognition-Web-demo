#!/usr/bin/python
#--*-coding: utf-8 --*-

#----------------------------------------------------------------------------------------------
#
# Description: Face Recognition Web app
# Author: WIll Wu
# Company: School of MicroElectronic. SJTU
#
#-----------------------------------------------------------------------------------------

import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, session, flash, jsonify
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import tornado.wsgi
import tornado.httpserver
import optparse
from form import PhotoForm,RegForm
from werkzeug.datastructures import FileStorage
import sys

sys.path.append('../')

from recognition.classfier import *
from recognition.dataset import db
from recognition.image import alignment

# upload_folder: when picture snapped, store in upload_folder
UPLOAD_FOLDER = "/tmp/"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

# flask app setting 
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'hard to guess string'

# add bootstrap framwork
bootstrap = Bootstrap()
bootstrap.init_app(app)

# load classfier for face recognition
classfier = Classfier()
classfier.check()

# db means person picture database
database = db()

#---------------------------------------------
#
# Description: base view function
#
#---------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('base.html')


#---------------------------------------------
#
# Description: upload view function
# Fcuntion: upload image file, flash the recognition result
#
#---------------------------------------------
@app.route('/upload',methods=['GET','POST'])
def upload():
    form = PhotoForm()
    if form.validate_on_submit():
        filename = secure_filename(form.photo.data.filename)
        form.photo.data.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        facefilename = alignment(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if facefilename ==  None:
            flash('This picture can not find faces, Please change another picture')
        else:
            person = classfier.recognition(facefilename)
            if person == '':
                flash('Can not recognize the picture, Please change another picture')
            else:
                flash("The person is "+person)
    else:
        filename = None
    return render_template('upload.html', form=form, filename=filename)

#---------------------------------------------
#
# Description: just a showresult function for ajax, not for view
#
#---------------------------------------------
@app.route('/_show',methods=['GET'])
def show():
    return jsonify(result= session['result'])

#---------------------------------------------
#
# Description: realtime view function
# Fcuntion: snapshot picture by using Webcam and recognition the person
#
#---------------------------------------------

@app.route('/realtime',methods=['GET','POST'])
def realtime():
    if request.method == 'POST':
        info = "load image file failed"
        file = request.files['webcam']
        filename = 'realtime.jpg'
        if file:
            FileStorage(stream=file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename)))
            facefilename = alignment(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if facefilename ==  None:
                info = 'This picture can not find faces, Please change another picture'
            else:
                person = classfier.recognition(facefilename)
                if person == '':
                    info = 'Can not recognize the picture, Please change another picture'
                else:
                    info = "Person name "+person
            session['result'] = info
            return redirect(url_for('realtime'))
    return render_template('realtime.html')
    
#---------------------------------------------
#
# Description: register view function
# Fcuntion: add new person and new picture of him to the person picture database
#
#---------------------------------------------

@app.route('/register',methods=['GET','POST'])
def register():
    registform = RegForm()
    if registform.validate_on_submit():
        if session.get('personface'):
            facefilename = session['personface'] 
            if facefilename !='No face':
                database.addperson(facefilename,registform.name.data)
                classfier.check()
                flash('Register new person success')
            else:
                flash('Register new person failed, please retry')
        else:
            flash('Register new person failed, please retry')

    if request.method =='POST' and request.files.get('webcam'):
        file = request.files['webcam']
        filename = 'realtime.jpg'
        FileStorage(stream=file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename)))
        facefilename = alignment(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if facefilename is not None:
            session['personface'] = facefilename
        else:
            session['personface'] = 'No face'
    return render_template('register.html',form=registform)


def start_tornado(app, port=5000):
    http_server = tornado.httpserver.HTTPServer(
        tornado.wsgi.WSGIContainer(app))
    http_server.listen(port)
    print("Tornado server starting on port {}".format(port))
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.add_option(
        '-d', '--debug',
        help="enable debug mode",
        action="store_true", default=False)
    parser.add_option(
        '-p', '--port',
        help="which port to serve content on",
        type='int', default=5000)

    opts, args = parser.parse_args()
    if opts.debug:
        app.run(debug=True, host='0.0.0.0', port=opts.port)
    else:
        start_tornado(app, opts.port)