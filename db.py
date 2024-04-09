'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *
import random #Should probably select something more secure
import sys
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
    salt = random.randint(0, sys.maxsize)
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
        just_names = []
        for request in requests:
            just_names.append(request.sender)
        return just_names
    
def delete_friend_request(sender_user_name,receiver_user_name):
    with Session(engine) as session:
        sender_to_reciever = session.query(friend_request).filter(friend_request.sender == sender_user_name).filter(friend_request.receiver == receiver_user_name).first()
        reciever_to_sender = session.query(friend_request).filter(friend_request.sender == receiver_user_name).filter(friend_request.receiver == sender_user_name).first()
        
        if not (sender_to_reciever == None):
            session.delete(sender_to_reciever)
        if not (reciever_to_sender == None):
            session.delete(reciever_to_sender)
    
def is_valid_username(user_name):
    return not get_user_by_username(user_name) == None

def send_friend_request(sender_user_name,receiver_user_name):
    if (duplicate_friend_request_check(sender_user_name,receiver_user_name) == False):
        request = friend_request(sender=sender_user_name,receiver=receiver_user_name)
        with Session(engine) as session:
            session.add(request)
            session.commit()