import sys
import os
basePath = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
sys.path.append(basePath)
import models

class user:
    def __init__(self,user_details:models.user_refactored,connection_ref) -> None:
        self.user_details = user_details
        self.connection_ref = connection_ref
        
    def get_connection_ref(self):
        return self.connection_ref
    
    def get_user_hash(self):
        return self.user_details.user_hash
    
    def get_user_name(self):
        return self.user_details.user_name
        