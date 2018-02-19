from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import sys
import json
from flask_heroku import Heroku
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
heroku = Heroku(app)
db = SQLAlchemy(app)

class Dataentry(db.Model):
    __tablename__ = "dataentry"
    id = db.Column(db.Integer, primary_key=True)
    mydata = db.Column(db.Text())

    def __init__(self, mydata):
        self.mydata = mydata

@app.route("/submit", methods=["POST"])
def post_to_db():
    indata = Dataentry(request.form['mydata'])
    data = copy(indata.__dict__)
    del data["_sa_instance_state"]
    try:
        db.session.add(indata)
        db.session.commit()
    except Exception as e:
        print("\n FAILED entry: {}\n".format(json.dumps(data)))
        print(e)
        sys.stdout.flush()
    return 'Success! To enter more data, <a href="{}">click here!</a>'.format(url_for("enter_data"))

@app.route('/')
def homepage():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
