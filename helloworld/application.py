#!flask/bin/python
import json, requests
from flask import Flask, Response, request
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy

from helloworld.Constants import Constants
from helloworld.flaskrun import flaskrun
from datetime import datetime

application = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(application)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(200), nullable=False)
    msg = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def serialized(self):
        return {
                "id": self.id,
                "status": self.status,
                "msg": self.msg,
                "date_createdd": str(self.date_created)
            }
    def __repr__(self):
        return '<Task %r>' % self.id


class Asset_Management_Config():
    assets = {}


def update_assets_from_config():
    with open('asset_management_config') as f:
        Asset_Management_Config.assets = json.load(f)


@application.route('/', methods=['GET'])
def get():
    return Response(json.dumps({'Output': 'get request response'}), mimetype='application/json', status=200)


@application.route('/', methods=['POST'])
def post():
    return Response(json.dumps({'Output': 'post request response'}), mimetype='application/json', status=200)


def validate(req):
    try:
        if not req or not req["msg"]:
            return False
    except:
        return False
    return True


def populate_asset(asset_name, req):
    pass


def get_asset_url(asset_name):
    if Constants.is_running_locally:
        url = Asset_Management_Config.assets[asset_name]["local_url"]
    else:
        url = Asset_Management_Config.assets[asset_name]["service_host_url"]

    return url + Asset_Management_Config.assets[asset_name]["fixing_api"]


@application.route('/new_request', methods=['POST'])
def new_request():
    req = request.json
    if not validate(req):
        return Response(json.dumps({'ERROR': 'bad request'}), mimetype='application/json', status=400)
    new_task = Task(msg=req["msg"])
    for asset_name in Asset_Management_Config.assets.keys():
        if asset_name not in req.keys():
            response = requests.post(get_asset_url(asset_name), data={"id": new_task.id})
            new_task.msg += " - " + asset_name + " fixed val = " + response.json()["a1"]
    new_task.status = "complete"
    try:
        db.session.add(new_task)
        db.session.commit()
    except:
        return Response(json.dumps({'ERROR': 'could not store in db'}), mimetype='application/json', status=500)
    return Response(json.dumps({'task id ': new_task.id, "msg ": new_task.msg}), mimetype='application/json', status=200)


@application.route('/callA1', methods=['POST'])
def callA1FixerService():
    if not request.json:
        return Response(json.dumps({'ERROR': 'bad req : input not found'}), mimetype='application/json', status=500)
    response = requests.post("http://127.0.0.1:5002/populateA1Asset", data=request.json)
    return Response(json.dumps({'a1 resp': str(response.json())}), mimetype='application/json', status=200)


@application.route('/update_config', methods=['GET'])
def update_config():
    update_assets_from_config()
    return Response(json.dumps({'config': Asset_Management_Config.assets}), mimetype='application/json', status=200)

@application.route('/show_all', methods=['GET'])
def show_all():
    return Response(json.dumps([result.serialized for result in Task.query.order_by(Task.date_created).all()]), mimetype='application/json', status=200)


if __name__ == '__main__':
    update_assets_from_config()
    # db.create_all()
    flaskrun(application)
