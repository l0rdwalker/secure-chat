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
        
def record_message(user_one,user_two,message):
    if (is_valid_username(user_one) == is_valid_username(user_two) == True):
        with Session(engine) as session:
            message_instance = message_history(user_one = user_one, user_two = user_two, message = message, time_stamp = int(datetime.datetime.now().timestamp()))
            session.add(message_instance)
            session.commit()
            
def get_message_history_db(user_one, user_two):
    if (is_valid_username(user_one) == is_valid_username(user_two) == True):
        with Session(engine) as session:
            left_comumn_detection = session.query(message_history).filter(message_history.user_one == user_one).filter(message_history.user_two == user_two).all()
            right_column_detection = session.query(message_history).filter(message_history.user_two == user_one).filter(message_history.user_one == user_two).all()
            
            left_comumn_detection.extend(right_column_detection)
            left_comumn_detection = sorted(left_comumn_detection, key=lambda friends_list:friends_list.time_stamp)
            
            formatted_messages = []
            for message in left_comumn_detection:
                formatted_messages.append(
                    json.dumps(
                        {
                            "user":message.user_one,
                            "message":message.message
                        }
                    )
                )
            
            return json.dumps(
                {
                    "messages" : formatted_messages
                }
            )