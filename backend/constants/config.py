import os
from dotenv import load_dotenv

# Load environment variables at once
load_dotenv()

# Database
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

# JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL')

# SMTP 
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USE_SSL = os.getenv('SMTP_USE_SSL')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# IMAP
IMAP_HOST = os.getenv('IMAP_HOST')
IMAP_PORT = os.getenv('IMAP_PORT')

# Emails
CRJYOUTH_MAIL_ADMIN = os.getenv('CRJYOUTH_MAIL_ADMIN')
CRJYOUTH_MAIL_SUPPORT = os.getenv('CRJYOUTH_MAIL_SUPPORT')
CRJYOUTH_MAIL_NO_REPLY = os.getenv('CRJYOUTH_MAIL_NO_REPLY')
CRJYOUTH_MAIL_INFO = os.getenv('CRJYOUTH_MAIL_INFO')

# Raise exceptions if variable not found
if not DB_NAME:
    raise ValueError('DB_NAME not found in .env file.')

if not DB_USER:
    raise ValueError('DB_USER not found in .env file.')

if not DB_PASSWORD:
    raise ValueError('DB_PASSWORD not found in .env file.')

if not DB_HOST:
    raise ValueError('DB_HOST not found in .env file.')

if not JWT_SECRET_KEY:
    raise ValueError('JWT_SECRET_KEY not found in .env file.')

if not LOG_LEVEL:
    raise ValueError('LOG_LEVEL not found in .env file.')

if not SMTP_HOST:
    raise ValueError('SMTP_HOST not found in .env file.')

if not SMTP_PORT:
    raise ValueError('SMTP_PORT not found in .env file.')

if not SMTP_USE_SSL:
    raise ValueError('SMTP_USE_SSL not found in .env file.')

if not SMTP_USE_TLS:
    raise ValueError('SMTP_USE_TLS not found in .env file.')

if not SMTP_USER:
    raise ValueError('SMTP_USER not found in .env file.')

if not SMTP_PASSWORD:
    raise ValueError('SMTP_PASSWORD not found in .env file.')

if not IMAP_HOST:
    raise ValueError('IMAP_HOST not found in .env file.')

if not IMAP_PORT:
    raise ValueError('IMAP_PORT not found in .env file.')

if not CRJYOUTH_MAIL_ADMIN:
    raise ValueError('CRJYOUTH_MAIL_ADMIN not found in .env file.')

if not CRJYOUTH_MAIL_SUPPORT:
    raise ValueError('CRJYOUTH_MAIL_SUPPORT not found in .env file.')

if not CRJYOUTH_MAIL_NO_REPLY:
    raise ValueError('CRJYOUTH_MAIL_NO_REPLY not found in .env file.')

if not CRJYOUTH_MAIL_INFO:
    raise ValueError('CRJYOUTH_MAIL_INFO not found in .env file.')
