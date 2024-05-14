'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *
import datetime
import random #Should probably select something more secure
import sys
import os
import datetime
import json
import common

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str):
    with Session(engine) as session:
        user = User(username=username, password=password)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)
    
def get_user_refactored(user_hash: str):
    with Session(engine) as session:
        return session.get(user_refactored,user_hash)
    
def get_user_by_username(user_name: str):
    with Session(engine) as session:
        return session.query(user_refactored_salted).filter(user_refactored_salted.user_name == user_name).first()
    
def insert_user_refactored(user_hash,user_name):
    salt = int.from_bytes(os.urandom(8), byteorder="big") & ((1 << 63) - 1)
    salted_hash = common.salt_hash(user_hash,salt)

    with Session(engine) as session:
        user = user_refactored_salted(user_hash=salted_hash, user_name=user_name, salt=salt)
        session.add(user)
        session.commit()

def duplicate_friend_request_check(sender_user_name,receiver_user_name):
    with Session(engine) as session:
        sender_to_reciever = session.query(friend_request).filter(friend_request.sender == sender_user_name).filter(friend_request.receiver == receiver_user_name).first()
        reciever_to_sender = session.query(friend_request).filter(friend_request.sender == receiver_user_name).filter(friend_request.receiver == sender_user_name).first()
        
        return not (sender_to_reciever == reciever_to_sender == None)
    
def get_friend_requests(user_name):
    with Session(engine) as session:
        requests = session.query(friend_request).filter(friend_request.receiver == user_name).all()
        sent_requests = session.query(friend_request).filter(friend_request.sender == user_name).all()
        just_names = []
        for request in requests:
            just_names.append([request.sender,'request'])
        for request in sent_requests:
            just_names.append([request.sender,'pending'])
        return just_names
    
def get_friend_sent_requests(user_name):
    with Session(engine) as session:
        requests = session.query(friend_request).filter(friend_request.receiver == user_name).all()
        sent_requests = session.query(friend_request).filter(friend_request.sender == user_name).all()
        just_names = []
        for request in requests:
            just_names.append(request.receiver)
        for request in sent_requests:
            just_names.append(request.receiver)
        return just_names
    
def delete_friend_request(sender_user_name,receiver_user_name):
    with Session(engine) as session:
        sender_to_reciever = session.query(friend_request).filter(friend_request.sender == sender_user_name).filter(friend_request.receiver == receiver_user_name).first()
        reciever_to_sender = session.query(friend_request).filter(friend_request.sender == receiver_user_name).filter(friend_request.receiver == sender_user_name).first()
        
        if not (sender_to_reciever == None):
            session.delete(sender_to_reciever)
        if not (reciever_to_sender == None):
            session.delete(reciever_to_sender)
        session.commit()
    
def is_valid_username(user_name):
    return not get_user_by_username(user_name) == None

def send_friend_request(sender_user_name,receiver_user_name):
    if (duplicate_friend_request_check(sender_user_name,receiver_user_name) == False):
        request = friend_request(sender=sender_user_name,receiver=receiver_user_name)
        with Session(engine) as session:
            session.add(request)
            session.commit()
            
def existing_friend_relationship(user_name_one,user_name_two):
    with Session(engine) as session:
        one_to_two = session.query(friends_list).filter(friends_list.user_one == user_name_one).filter(friends_list.user_two == user_name_two).first()
        two_to_one = session.query(friends_list).filter(friends_list.user_two == user_name_one).filter(friends_list.user_one == user_name_two).first()
        return one_to_two == two_to_one == None
            
def append_friends_relationship(user_name_one,user_name_two):
    if (is_valid_username(user_name_one) and is_valid_username(user_name_two)):
        if (existing_friend_relationship(user_name_one,user_name_two)):
            with Session(engine) as session:
                friend_relationship = friends_list(user_one=user_name_one,user_two=user_name_two)
                session.add(friend_relationship)
                session.commit()
                
def get_all_users():
    with Session(engine) as session:
        all_users = session.query(user_refactored).all()
        return all_users
        
def get_friends_by_username(user_name:str):
    if (is_valid_username(user_name)):
        with Session(engine) as session:
            left_column_detection = session.query(friends_list).filter(friends_list.user_one == user_name).all()
            right_column_detection = session.query(friends_list).filter(friends_list.user_two == user_name).all()

            just_names = []
            for relationship in left_column_detection:
                just_names.append(relationship.user_two)
            for relationship in right_column_detection:
                just_names.append(relationship.user_one)
            return just_names
        
def create_new_chatroom(user_name:str):
    try:
        with Session(engine) as session:
            chat_room = chat_room_obj(chat_name=f'{user_name}s chat room')
            session.add(chat_room)
            session.commit()
            
            user_chat = user_chat_obj(chat_id=chat_room.chat_id,user_name=user_name)
            session.add(user_chat)
            session.commit()
            
            return user_chat.chat_id
    except Exception as e:
        return None
        
def get_chat_room_by_id(chat_room_id: int):
    with Session(engine) as session:
        chat_room = session.query(chat_room_obj).filter(chat_room_obj.chat_id == chat_room_id).first()
        if not (chat_room == None):
            chat_room_json_obj = {"chat_name":None,"chat_id":None,"members":[],"messages":[]}
            chat_room_json_obj['chat_name'] = chat_room.chat_name
            chat_room_json_obj['chat_id'] = chat_room_id
            
            users_in_chat = session.query(user_chat_obj).filter(user_chat_obj.chat_id == chat_room_id).all()
            for user in users_in_chat:
                chat_room_json_obj['members'].append(user.user_name)
            
            chat_room_messages = []
            chat_room_message_obj = session.query(message_obj).filter(message_obj.chat_id == chat_room_id).all()
            for message_instance in chat_room_message_obj:
                chat_room_messages.append({
                    'from' : message_instance.user_name,
                    'Time' : message_instance.time_sent,
                    'message' : message_instance.message
                })
                
            chat_room_json_obj['messages'] = chat_room_messages
            return chat_room_json_obj
    return None
        
def add_message_to_chat(user_name,message,chat_id):
    with Session(engine) as session:
        message_instance = message_obj(user_name=user_name,chat_id=chat_id,time_sent=datetime.datetime.now().isoformat(),message=message)
        session.add(message_instance)
        session.commit()

def is_valid_chatroomid(chatroom_id):
    return not get_chat_room_by_id(chatroom_id) == None

def get_chats_by_username(user_name):
    with Session(engine) as session:
        chat_room_objs = session.query(user_chat_obj).filter(user_chat_obj.user_name == user_name).all()
        
        chat_room_json = []
        for chat_room in chat_room_objs:
            chat_room_name = session.query(chat_room_obj).filter(chat_room_obj.chat_id == chat_room.chat_id).first()
            chat_room_json.append({
                'chat_name' : chat_room_name.chat_name,
                'chat_id' : chat_room.chat_id
            })
        return chat_room_json
    
def set_chat_name(chat_id, new_name):
    with Session(engine) as session:
        chat_room = session.query(chat_room_obj).filter(chat_room_obj.chat_id == chat_id).first()
        chat_room.chat_name = new_name
        session.commit()
        
def get_random_chatroom_for_user(username):
    try: 
        with Session(engine) as session:
            chat_room = session.query(user_chat_obj).filter(user_chat_obj.user_name == username).first()
            return chat_room.chat_id
    except:
        return None
        
def delete_chat_by_id(chat_id):
    with Session(engine) as session:
        chat_room = session.query(chat_room_obj).filter(chat_room_obj.chat_id == chat_id).first()
        session.delete(chat_room)

        users_to_update = []
        user_chat_associations = session.query(user_chat_obj).filter(user_chat_obj.chat_id == chat_id).all()
        for chat_user in user_chat_associations:
            users_to_update.append(chat_user.user_name)
            session.delete(chat_user)
        
        messages = session.query(message_obj).filter(message_obj.chat_id == chat_id).all()
        for message in messages:
            session.delete(message)
        
        session.commit()
        
        return users_to_update
    
def get_user_suggestion(entered_text,user_name):
    try:
        with Session(engine) as session:
            #input = f'{entered_text}%'
            #user = session.query(user_refactored).filter(user_refactored.user_name.like(input)).first()
            friends = get_friends_by_username(user_name)
            user = None
            for friend in friends:
                if friend.startswith(entered_text):
                    user = friend
                    break
            return user
    except:
        return None

def add_user_to_chat(user_name, chat_id):
    with Session(engine) as session:
        existing_user = session.query(user_chat_obj).filter(user_chat_obj.user_name == user_name).filter(user_chat_obj.chat_id == chat_id).first()
        if (existing_user == None):
            message_instance = user_chat_obj(user_name=user_name,chat_id=chat_id)
            session.add(message_instance)
            session.commit()
        