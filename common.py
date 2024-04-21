from hashlib import sha256
import hashlib

def salt_hash(original_hash,salt):
    return sha256((f"{original_hash}{salt}").encode('utf-8')).hexdigest()

def compare_hash(original_hash,salt,salted_hash):
    check_hash_salt = salt_hash(original_hash,salt)
    return (check_hash_salt == salted_hash)

def hash_string(string):
    hash_object = hashlib.sha256()
    hash_object.update(string.encode('utf-8'))
    hashed_string = hash_object.hexdigest()
    return hashed_string


