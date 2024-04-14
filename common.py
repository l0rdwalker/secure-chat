from hashlib import sha256

def salt_hash(original_hash,salt):
    return sha256((f"{original_hash}{salt}").encode('utf-8')).hexdigest()

def compare_hash(original_hash,salt,salted_hash):
    check_hash_salt = salt_hash(original_hash,salt)
    return (check_hash_salt == salted_hash)

