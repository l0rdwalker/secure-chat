'''
socket_routes
file containing all the routes related to socket.io
'''

from flask_socketio import emit
from flask import request
from userManager.manager import user_manager
from flask_jwt_extended import decode_token
from flask import current_app
import jwt
import json
import common

try:
    from __main__ import socketio
    from __main__ import app
except ImportError:
    from app import socketio
import db

user_aggregator = user_manager()

def validate_user_content(user_name, user_hash): #Foundational security check, used in the the login process. 
    potential_user = db.get_user_by_username(user_name)
    if (potential_user == None):
        raise Exception("No user of given name.") #These errors are relayed and displayed onscreen
    if common.compare_hash(user_hash,potential_user.salt,potential_user.user_hash) == False:
        raise Exception("Invalid password")
    return True

def validate_user(user_name,user_hash): #Wpr for validate_user_content, allows other functions to use the same logic without faultering due to the flipped error
    try: 
        return validate_user_content(user_name,user_hash) 
    except Exception as e:
        return False

def relay_friend_requests(user_name:str): 
    request = {"requests":db.get_friend_requests(user_name)}
    emit("update_friend_requests",json.dumps(request),room=user_aggregator.get_relay_connection_reference(user_name))

def relay_online_friends_list(user_name:str,notify_friends=True,on_disconnect=False):
    all_friends = db.get_friends_by_username(user_name)
    online_friends = []
    for friend in all_friends:
        if (user_aggregator.is_online(friend)): #Main logic to determin if a user should be labelled online or offline
            online_friends.append([friend,True]) 
            if (notify_friends):
                relay_online_friends_list(friend,notify_friends=False)
        else:
            online_friends.append([friend,False])
    if (on_disconnect == False):
        emit("update_friends_list",json.dumps({"friends_list":online_friends}),room=user_aggregator.get_relay_connection_reference(user_name))
    
def inform_error(error_msg:str, user_name:str, registered=True): ##Allows us to inform the frontend of any error which might occur. 
    if (registered): 
        emit("error",error_msg,room=user_aggregator.get_relay_connection_reference(user_name)) #if user_name doesn't store connection reference, we must return the connection reference
    else:
        emit("error",error_msg,room=user_name) #Otherwise, the user_name is just the connection reference itself

def jwt_token_check(token):
    try:
        decode_token(token,allow_expired=False)
        return True
    except Exception as e:
        return False

def security_check(message_obj,connection_id): #Generic security check that is referred to by many other functions.
    if (jwt_token_check(message_obj['token']) and db.is_valid_username(message_obj['sender']) and user_aggregator.is_online(message_obj['sender']) and user_aggregator.get_relay_connection_reference(message_obj['sender']) == connection_id):
        return True
    inform_error("Invalid credentials",connection_id,registered=False)

@socketio.on('user_search_get_all')
def user_search_list(message):
    message_json = json.loads(message)
    
    user_name = message_json["sender"]
    
    existing_friends = db.get_friends_by_username(user_name)
    all_users_objs = db.get_all_users()
    all_users_array = []
    sent_requests = db.get_friend_sent_requests(user_name)
    
    for x in range(0,len(all_users_objs)):
        if not (all_users_objs[x].user_name in existing_friends) and not (all_users_objs[x].user_name == user_name):
            all_users_array.append([all_users_objs[x].user_name,all_users_objs[x].user_name in sent_requests])
    
    emit("user_search_get_all",json.dumps({"users":all_users_array}),room=user_aggregator.get_relay_connection_reference(user_name))

@socketio.on('connect')
def connect(): #Main method which establishes connection to oncoming users
    user_name = request.cookies.get("username")
    user_hash = request.cookies.get("user_hash")
    
    if (validate_user(user_name,user_hash)):
        if (user_aggregator.is_online(user_name)):
            inform_error("No dual account use",request.sid,registered=False)
        else:
            connection_reference = request.sid
            user_aggregator.recognise_user(user_name, connection_reference)
            
            relay_friend_requests(user_name)
            relay_online_friends_list(user_name)
    else:
        inform_error("Invalid connection credentials",request.sid,registered=False)
    
@socketio.on('disconnect')
def manage_disconnect(): #Manages user disconnections
    user_name = request.cookies.get("username")
    if (user_aggregator.is_online(user_name)):
        user_aggregator.unrecognise_user(user_name)
        relay_online_friends_list(user_name,on_disconnect=True)

@socketio.on("relay")
def relay(message): #The main function which allows user-to-user communications
    message_json = json.loads(message)
    message_content_json = json.loads(message_json['message'])
    
    if (security_check(message_json,request.sid) and db.is_valid_username(message_json['sender'])):
        recipient_connection_reference = user_aggregator.get_relay_connection_reference(message_json["recipient"])
        if (message_content_json['type'] == "ciphertext"):
            db.record_message(message_json['sender'],message_json['recipient'],message_content_json['content'])
        if (user_aggregator.is_online(message_json['sender'])):
            emit("incoming",message,room=recipient_connection_reference)
    
@socketio.on("get_message_history")
def get_message_history(message): #Gets the convo history for two users, accessed when users open a chat. 
    message_json = json.loads(message)
    if (security_check(message_json,request.sid) and db.is_valid_username(message_json['sender'])):
        history = db.get_message_history_db(message_json['sender'],message_json['recipient'])
        emit("message_history",history,room=user_aggregator.get_relay_connection_reference(message_json['sender']))

@socketio.on("cancel_friend_request") 
def cancel_friend_request(message):
    message_json = json.loads(message)
    if db.is_valid_username(message_json['sender']) and db.is_valid_username(message_json['recipient']):
        if not message_json['sender']==message_json['recipient']: 
            db.delete_friend_request(message_json['sender'],message_json['recipient'])
            if (user_aggregator.is_online(message_json['recipient'])):
                relay_friend_requests(message_json['recipient'])
            user_search_list(message)
            relay_friend_requests(message_json['sender'])   

@socketio.on("send_friend_request") 
def send_friend_request(message):
    message_json = json.loads(message)
    if db.is_valid_username(message_json['sender']) and db.is_valid_username(message_json['recipient']):
        if not message_json['sender']==message_json['recipient']: 
            db.send_friend_request(message_json['sender'],message_json['recipient'])
            if (user_aggregator.is_online(message_json['recipient'])):
                relay_friend_requests(message_json['recipient'])
            user_search_list(message)
            relay_friend_requests(message_json['sender'])   
            
@socketio.on("send_friend_request_response") 
def send_friend_request_response(message):
    message_json = json.loads(message)
    if db.is_valid_username(message_json['sender']) and db.is_valid_username(message_json['recipient']):
        if (message_json['message']):
            db.append_friends_relationship(message_json['sender'],message_json['recipient'])
        db.delete_friend_request(message_json['sender'],message_json['recipient'])
        
        if (user_aggregator.is_online(message_json['sender'])):
            relay_online_friends_list(message_json['sender'])
            relay_friend_requests(message_json['sender'])
        if (user_aggregator.is_online(message_json['recipient'])):
            relay_online_friends_list(message_json['recipient'])
            relay_friend_requests(message_json['recipient'])