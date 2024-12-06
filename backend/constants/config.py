import os
from dotenv import load_dotenv

# Load environment variables at once
load_dotenv()

# Database Keys
# DB_CONNECTION_STR = os.getenv('DB_CONNECTION_STR')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

# JWT keys
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

# if not DB_CONNECTION_STR:
#     raise ValueError('DB_CONNECTION_STR not found in .env file.')

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
