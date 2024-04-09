import sys
import os
from userManager.user_obj import user
basePath = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
sys.path.append(basePath)
import models
import db

class user_manager:
    def __init__(self) -> None:
        self.online_users = {}
        
    def is_online(self,user_name:str):
        return user_name in self.online_users
        
    def get_relay_connection_reference(self,user_name:str):
        if (user_name in self.online_users):
            return self.online_users[user_name].get_connection_ref()
        
    def recognise_user(self, user_name: str, connection_reference):
        orm_user = db.get_user_by_username(user_name)
        if not (orm_user == None):
            if not user_name in self.online_users:
                self.online_users[user_name] = user(orm_user, connection_reference)
            else:
                print("User already connected")
            
    def unrecognise_user(self, user_name):
        if user_name in self.online_users:
            del self.online_users[user_name]
        else:
            print("User not found")
    
    