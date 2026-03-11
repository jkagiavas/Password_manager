import bcrypt
import os

# The file where the hashed master password is stored locally
MASTER_PASSWORD_FILE = "master.key"

def set_master_password(password):
    # bcrypt.gensalt() generates a random salt - this makes every hash unique
    # even if two users have the same password
    # hashpw() combines the password with the salt and creates a secure hash
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    with open(MASTER_PASSWORD_FILE, "wb") as f:
        f.write(hashed)

def verify_master_password(password):
    # If no master password has been set yet, return False
    if not os.path.exists(MASTER_PASSWORD_FILE):
        return False
    with open(MASTER_PASSWORD_FILE, "rb") as f:
        hashed = f.read()
    # checkpw() hashes the input and compares it to the stored hash
    # we never store the plain password - only the hash
    return bcrypt.checkpw(password.encode(), hashed)

def master_password_exists():
    # Simply checks if the master.key file exists on disk
    return os.path.exists(MASTER_PASSWORD_FILE)