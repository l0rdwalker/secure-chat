'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, Response
from flask_socketio import SocketIO
import db
import secrets
import common
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

import socket_routes

@app.route("/")
def index():
    return render_template("index.jinja")

@app.route("/login")
def login():    
    return render_template("login.jinja")

@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    user_hash = request.json.get("user_hash")
    username = request.json.get("username")

    try:
        socket_routes.validate_user_content(username,user_hash)
        return url_for('home')
    except Exception as e:
        return str(e)

@app.route("/signup")
def signup():
    return render_template("signup.jinja")

@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")    
    user_hash = request.json.get("user_hash")
    
    if username.strip() == "":
        return "No empty space username"
     
    if db.get_user_refactored(user_hash) == None and db.get_user_by_username(username) == None:
        db.insert_user_refactored(user_hash,username)
        return url_for('home')   
    else:
        return "Please select a unique username"

@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

@app.route("/home")
def home():
    return render_template("home.jinja")

script_dir = os.path.dirname(os.path.abspath(__file__))
certificate = os.path.join(script_dir,"certs/flaskapp.crt")
certificatePrivateKey = os.path.join(script_dir,"certs/flaskapp.key")

if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    socketio.run(app,ssl_context=(certificate, certificatePrivateKey))
    