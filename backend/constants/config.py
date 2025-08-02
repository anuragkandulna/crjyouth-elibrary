import os
from dotenv import load_dotenv

# Load environment variables at once
load_dotenv()

# Database
DB_NAME = os.getenv('DB_NAME')

# JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
TIMED_SECRET_KEY = os.getenv('TIMED_SECRET_KEY')

# Logging
LOG_LEVEL = int(os.getenv('LOG_LEVEL', '20'))
APP_ENV = os.getenv('APP_ENV')

# SMTP 
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

CRJYOUTH_MAIL_NO_REPLY = os.getenv('CRJYOUTH_MAIL_NO_REPLY')

# Raise exceptions if variable not found
if not DB_NAME:
    raise ValueError('DB_NAME not found in .env file.')

if not JWT_SECRET_KEY:
    raise ValueError('JWT_SECRET_KEY not found in .env file.')

if not TIMED_SECRET_KEY:
    raise ValueError('TIMED_SECRET_KEY not found in .env file.')

if not LOG_LEVEL:
    raise ValueError('LOG_LEVEL not found in .env file.')

if not SMTP_HOST:
    raise ValueError('SMTP_HOST not found in .env file.')

if not SMTP_PORT:
    raise ValueError('SMTP_PORT not found in .env file.')

if not SMTP_USER:
    raise ValueError('SMTP_USER not found in .env file.')

if not SMTP_PASSWORD:
    raise ValueError('SMTP_PASSWORD not found in .env file.')

if not CRJYOUTH_MAIL_NO_REPLY:
    raise ValueError('CRJYOUTH_MAIL_NO_REPLY not found in .env file.')

if not APP_ENV:
    raise ValueError('APP_ENV not found in .env file.')
