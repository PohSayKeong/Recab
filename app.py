from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import sys
import json
from flask_heroku import Heroku
from werkzeug.utils import secure_filename
import os
import config
import flask_login
import flask
from flask_session import Session
from config import SECRET_KEY, SESSION_TYPE
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
heroku = Heroku(app)
db = SQLAlchemy(app)
db.init_app(app)

from helpers import *

class UserLog(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text())
    password = db.Column(db.Text())

    def __init__(self, username, password):
        self.username = username
        self.password= password

class Cabinet(db.Model):
    __tablename__ = "cabinets"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    user = db.Column(db.Text())
    description = db.Column(db.Text())
    image = db.Column(db.Text())

    def __init__(self, name, user, description, image):
        self.name = name
        self.user = user
        self.description = description
        self.image = image

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.Text())
    user = db.Column(db.Text())

    def __init__(self, item, user):
        self.item = item
        self.user = user

class User(flask_login.UserMixin):
    pass

users = {}

login_manager = flask_login.LoginManager()
login_manager.login_view = "/login"
login_manager.init_app(app)
app.secret_key = SECRET_KEY


@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return

    user = User()
    user.id = username
    return user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in users:
        return

    user = User()
    user.id = username

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[username]['password']

    return user

#main

@app.route('/login', methods=['GET', 'POST'])
def login():
    for u in db.session.query(UserLog).all():
        data = u.__dict__.copy()
        del data["_sa_instance_state"]
        users[data['username']] = data
    if request.method == 'POST' and flask.request.form["password"] == users[flask.request.form["username"]]['password']:
        username = flask.request.form["username"]
        user = User()
        user.id = username
        flask_login.login_user(user)
        return flask.redirect(url_for('homepage'))
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST' and request.form['password']==request.form['repassword']:
        indata = UserLog(request.form['username'],request.form['password'])
        data = indata.__dict__.copy()
        del data["_sa_instance_state"]
        try:
            db.session.add(indata)
            db.session.commit()
        except Exception as e:
            print("\n FAILED entry: {}\n".format(json.dumps(data)))
            print(e)
            sys.stdout.flush()
        for u in db.session.query(UserLog).all():
            data = u.__dict__.copy()
            del data["_sa_instance_state"]
            users[data['username']] = data
        user = User()
        user.id = flask.request.form["username"]
        flask_login.login_user(user)
        return flask.redirect(url_for('homepage'))
    return render_template("signup.html")

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(url_for('login'))

@app.route('/', methods=["GET","POST"])
@flask_login.login_required
def homepage():
    return render_template("home.html")

@app.route('/cabinet', methods=["GET","POST"])
@flask_login.login_required
def cabinetpage():
    return render_template("cabinet.html")

@app.route('/newcabinet', methods=["GET","POST"])
@flask_login.login_required
def newcabinetpage():
    if request.method == 'POST' and 'photo' in request.files:
        photo = request.files['photo']
        photo.filename = secure_filename(photo.filename)
        output = upload_file_to_s3(photo, S3_BUCKET)
        session['image_link'] = str(output)
        return render_template("newcabinet.html", image_link=str(output), display="", method = 'GET')
    if request.method == 'POST' and 'description' in request.files:
        return flask.redirect(url_for('homepage'))
    return render_template("newcabinet.html", display="display:none;")

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
