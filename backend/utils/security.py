from flask_argon2 import Argon2
# from flask import current_app

# Initialize Argon2 (to be called from app.py)
argon2 = Argon2()

def generate_password_hash(password: str) -> str:
    return argon2.generate_password_hash(password)

def check_password_hash(hashed_password: str, password: str) -> bool:
    return argon2.check_password_hash(hashed_password, password)
