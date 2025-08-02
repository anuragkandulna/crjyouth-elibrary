from flask_argon2 import Argon2
from zxcvbn import zxcvbn
from typing import Optional

# Initialize Argon2 (to be called from app.py)
argon2 = Argon2()


def generate_password_hash(password: str) -> str:
    return argon2.generate_password_hash(password)


def check_password_hash(hashed_password: str, password: str) -> bool:
    return argon2.check_password_hash(hashed_password, password)


def verify_strong_password(password1: str,
                           first_name: str, last_name: str,
                           email: str, phone_number: str,
                           password2: Optional[str] = None) -> tuple:
    """
    Take password and other variables and verify if it is strong.
    """
    if password2:
        if password1 != password2:
            return (False, "Password and confirm password do not match.")
        
        if not (12 <= len(password1) <= 20 and 12 <= len(password2) <= 20):
            return (False, "Password length must be between 12 and 20 characters.")
    else:
        if not (12 <= len(password1) <= 20):
            return (False, "Password length must be between 12 and 20 characters.")

    # Test password strength
    result = zxcvbn(password=password1, user_inputs=[first_name, last_name, email, phone_number])
    if result['score'] <= 2:
        return (False, "Password must not contain your name, email or phone number.")
    
    return (True, "Password meets all security policy requirements.")
