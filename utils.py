import hashlib
import os

def generate_key_IV(username):
    # Use the username as a seed to generate a key
    seed = username.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', seed, os.urandom(16), 100000)
    IV = hashlib.pbkdf2_hmac('sha256', seed, os.urandom(16), 100000)
    return key, IV