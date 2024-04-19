'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for
from flask_socketio import SocketIO
import db
import secrets
import common
import os

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
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

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    
    username = request.json.get("username")    
    user_hash = request.json.get("user_hash")
    if db.get_user_refactored(user_hash) == None:
        db.insert_user_refactored(user_hash,username)
        return url_for('home')   
    else:
        return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
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
    