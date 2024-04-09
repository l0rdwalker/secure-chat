'''
socket_routes
file containing all the routes related to socket.io
'''

from flask_socketio import join_room, emit, leave_room
from flask import request
import models
from userManager.manager import user_manager
import json

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

import db
user_aggregator = user_manager()

    #{
    #    "message":"messageSTR",
    #    "sender":"senderHash",
    #    "recipient":"recipientUsername or hash",
    #}

def relay_friend_requests(user_name:str):
    requests = {"requests":db.get_friend_requests(user_name)}
    emit("update_friend_requests",json.dumps(requests),room=user_aggregator.get_relay_connection_reference(user_name))
    
def inform_error(error_msg:str, user_name:str):
    emit("error",error_msg,user_aggregator.get_relay_connection_reference(user_name))

@socketio.on('connect')
def connect():
    user_name = request.cookies.get("username")
    connection_reference = request.sid
    user_aggregator.recognise_user(user_name, connection_reference)
    
    relay_friend_requests(user_name)

@socketio.on("relay")
def relay(message):
    message_json = json.loads(message)
    recipient_connection_reference = user_aggregator.get_relay_connection_reference(message_json["recipient"])
    emit("incoming",message,room=recipient_connection_reference)

@socketio.on("send_friend_request") 
def send_friend_request(message):
    message_json = json.loads(message)
    if db.is_valid_username(message_json['sender']) and db.is_valid_username(message_json['recipient']):
        db.send_friend_request(message_json['sender'],message_json['recipient'])
        if (user_aggregator.is_online(message_json['recipient'])):
            relay_friend_requests(message_json['recipient'])
            
@socketio.on("send_friend_request_response") 
def send_friend_request_response(message):
    message_json = json.loads(message)
    if db.is_valid_username(message_json['sender']) and db.is_valid_username(message_json['recipient']):
        if (message_json['message']):
            pass #acceptence
        db.delete_friend_request(message_json['sender'],message_json['recipient'])
        relay_friend_requests(message_json['sender'])
        relay_friend_requests(message_json['recipient'])

@socketio.on('disconnect')
def disconnect():
    user_name = request.cookies.get("username")
    user_aggregator.unrecognise_user(user_name)
