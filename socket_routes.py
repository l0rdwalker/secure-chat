'''
socket_routes
file containing all the routes related to socket.io
'''

from flask_socketio import emit, leave_room, disconnect
from flask import request
import models
from userManager.manager import user_manager
import json
import common

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

import db
user_aggregator = user_manager()

def validate_user_content(user_name, user_hash):
    potential_user = db.get_user_by_username(user_name)
    if (potential_user == None):
        raise Exception("No user of given name.")
    if common.compare_hash(user_hash,potential_user.salt,potential_user.user_hash) == False:
        raise Exception("Invalid password")
    return True

def validate_user(user_name,user_hash):
    try: #So like, I need to show a warning message for the login attempts. But, I also use the validate user in other functions.
        return validate_user_content(user_name,user_hash) #Why create two nearly identical functions, when you can bridge the two with terrible design decisions? 
    except Exception as e:
        return False

def relay_friend_requests(user_name:str):
    request = {"requests":db.get_friend_requests(user_name)}
    emit("update_friend_requests",json.dumps(request),room=user_aggregator.get_relay_connection_reference(user_name))

def relay_online_friends_list(user_name:str,notify_friends=True,on_disconnect=False):
    all_friends = db.get_friends_by_username(user_name)
    online_friends = []
    for friend in all_friends:
        if (user_aggregator.is_online(friend)):
            online_friends.append([friend,True])
            if (notify_friends):
                relay_online_friends_list(friend,notify_friends=False)
        else:
            online_friends.append([friend,False])
    if (on_disconnect == False):
        emit("update_friends_list",json.dumps({"friends_list":online_friends}),room=user_aggregator.get_relay_connection_reference(user_name))
    
def inform_error(error_msg:str, user_name:str, registered=True):
    if (registered):
        emit("error",error_msg,room=user_aggregator.get_relay_connection_reference(user_name))
    else:
        emit("error",error_msg,room=user_name)
        
def security_check(user_name,connection_id):
    if (db.is_valid_username(user_name) and user_aggregator.is_online(user_name) and user_aggregator.get_relay_connection_reference(user_name) == connection_id):
        return True
    inform_error("Invalid credentials",connection_id,registered=False)

@socketio.on('connect')
def connect():
    user_name = request.cookies.get("username")
    user_hash = request.cookies.get("user_hash")
    
    if (validate_user(user_name,user_hash)):
        if (user_aggregator.is_online(user_name)):
            user_aggregator.unrecognise_user(user_name)
        else:
            connection_reference = request.sid
            user_aggregator.recognise_user(user_name, connection_reference)
            
            relay_friend_requests(user_name)
            relay_online_friends_list(user_name)
    else:
        inform_error("Invalid connection credentials",request.sid,registered=False)
    
@socketio.on('disconnect')
def manage_disconnect():
    user_name = request.cookies.get("username")
    if (user_aggregator.is_online(user_name)):
        user_aggregator.unrecognise_user(user_name)
        relay_online_friends_list(user_name,on_disconnect=True)

@socketio.on("relay")
def relay(message):
    message_json = json.loads(message)
    message_content_json = json.loads(message_json['message'])
    
    if (security_check(message_json['sender'],request.sid)):
        recipient_connection_reference = user_aggregator.get_relay_connection_reference(message_json["recipient"])
        if (message_content_json['type'] == "ciphertext"):
            db.record_message(message_json['sender'],message_json['recipient'],message_content_json['content'])
        emit("incoming",message,room=recipient_connection_reference)
    
@socketio.on("get_message_history")
def get_message_history(message):
    message_json = json.loads(message)
    if (security_check(message_json['sender'],request.sid)):
        history = db.get_message_history_db(message_json['sender'],message_json['recipient'])
        emit("message_history",history,room=user_aggregator.get_relay_connection_reference(message_json['sender']))

@socketio.on("send_friend_request") 
def send_friend_request(message):
    message_json = json.loads(message)
    if (security_check(message_json['sender'],request.sid)):
        if db.is_valid_username(message_json['sender']) and db.is_valid_username(message_json['recipient']):
            db.send_friend_request(message_json['sender'],message_json['recipient'])
            if (user_aggregator.is_online(message_json['recipient'])):
                relay_friend_requests(message_json['recipient'])
            relay_friend_requests(message_json['sender'])
            
@socketio.on("send_friend_request_response") 
def send_friend_request_response(message):
    message_json = json.loads(message)
    if (security_check(message_json['sender'],request.sid)):
        if db.is_valid_username(message_json['sender']) and db.is_valid_username(message_json['recipient']):
            if (message_json['message']):
                db.append_friends_relationship(message_json['sender'],message_json['recipient'])
            db.delete_friend_request(message_json['sender'],message_json['recipient'])
            
            relay_online_friends_list(message_json['sender'])
            relay_online_friends_list(message_json['recipient'])
            
            relay_friend_requests(message_json['sender'])
            relay_friend_requests(message_json['recipient'])