'''
socket_routes
file containing all the routes related to socket.io
'''

from flask_socketio import join_room, emit, leave_room
from flask import request
import models
from userManager.manager import user_manager
import json

# encryption libraries
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

KEY = b'sixteen byte key' # key for encryption/ decryption
IV = b'sixteen bytes IV' # AES initialisation vector

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

import db
user_aggregator = user_manager()

    #{
    #    "message":"messageSTR", //contents should be encrypted
    #    "sender":"senderHash",
    #    "recipient":"recipientUsername or hash",
    #}

def relay_friend_requests(user_name:str):
    request = {"requests":db.get_friend_requests(user_name)}
    emit("update_friend_requests", json.dumps(request), room=user_aggregator.get_relay_connection_reference(user_name))

def relay_friends_list(user_name:str):
    request = {"friends_list":db.get_friends_by_username(user_name)}
    emit("update_friends_list", json.dumps(request), room=user_aggregator.get_relay_connection_reference(user_name))
    
def inform_error(error_msg:str, user_name:str):
    emit("error", error_msg, user_aggregator.get_relay_connection_reference(user_name))

@socketio.on('connect')
def connect():
    user_name = request.cookies.get("username")
    connection_reference = request.sid
    user_aggregator.recognise_user(user_name, connection_reference)
    
    relay_friend_requests(user_name)
    relay_friends_list(user_name)

def encrypt_message(message):
    cipher = AES.new(KEY, AES.MODE_CBC, IV=IV)
    padded_message = pad(message.encode(), AES.block_size)
    encrypted_message = cipher.encrypt(padded_message)
    return base64.b64encode(encrypted_message).decode()

def decrypt_message(message):
    cipher = AES.new(KEY, AES.MODE_CBC, IV=IV)
    decrypted_message = cipher.decrypt(base64.b64decode(encrypt_message)) # decrypt using same base
    return unpad(decrypted_message, AES.block_size).decode() # unpad padded message

@socketio.on("relay")
def relay(message):
    message_json = json.loads(message)
    encrypted_message = encrypt_message(message_json["message"]) # encrypt message
    message_json["message"] = encrypted_message # re-assign it
    recipient_connection_reference = user_aggregator.get_relay_connection_reference(message_json["recipient"])
    emit("incoming", json.dumps(message_json), room=recipient_connection_reference)
    print(f"encrypted: {encrypt_message}")

@socketio.on("incoming")
def incoming(message):
    message_json = json.loads(message)
    decrypted_message = decrypt_message(message_json["message"]) # decryption
    message_json["message"] = decrypted_message # re-assign message
    # print decrypted message
    print("decrypted message: ", decrypted_message)

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
            db.append_friends_relationship(message_json['sender'],message_json['recipient'])
        db.delete_friend_request(message_json['sender'],message_json['recipient'])
        
        relay_friends_list(message_json['sender'])
        relay_friends_list(message_json['recipient'])
        
        relay_friend_requests(message_json['sender'])
        relay_friend_requests(message_json['recipient'])

@socketio.on('disconnect')
def disconnect():
    user_name = request.cookies.get("username")
    user_aggregator.unrecognise_user(user_name)
