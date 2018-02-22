from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
import sys
import json
from flask_heroku import Heroku
from werkzeug.utils import secure_filename
import os
import config
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
heroku = Heroku(app)
db = SQLAlchemy(app)

from helpers import *

class Dataentry(db.Model):
    __tablename__ = "dataentry"
    id = db.Column(db.Integer, primary_key=True)
    mydata = db.Column(db.Text())

    def __init__(self, mydata):
        self.mydata = mydata

session = {}

#main

@app.route("/submit", methods=["POST"])
def post_to_db():
    indata = Dataentry(request.form['mydata'])
    data = indata.__dict__.copy()
    del data["_sa_instance_state"]
    try:
        db.session.add(indata)
        db.session.commit()
    except Exception as e:
        print("\n FAILED entry: {}\n".format(json.dumps(data)))
        print(e)
        sys.stdout.flush()
    return 'Success! To enter more data, <a href="{}">click here!</a>'.format(url_for("homepage"))

@app.route('/', methods=["GET","POST"])
def homepage():
    if request.method == 'POST' and 'photo' in request.files:
        photo = request.files['photo']
        photo.filename = secure_filename(photo.filename)
        output = upload_file_to_s3(photo, S3_BUCKET)
        session['image_link'] = str(output)
        return redirect(url_for('newcabinetpage'))
    return render_template("home.html")

@app.route('/cabinet', methods=["GET","POST"])
def cabinetpage():
    return render_template("cabinet.html")

@app.route('/newcabinet', methods=["GET","POST"])
def newcabinetpage():
    image_link = session.get('image_link', None)
    return render_template("newcabinet.html", image_link=image_link)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
