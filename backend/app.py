"""
Start application here.
"""

from flask import Flask
from flask_cors import CORS
from utils.security import argon2
from utils.my_logger import CustomLogger
from utils.mail_setup import mail
from routes.auth_routes import auth_bp
from routes.profile_routes import profile_bp
from routes.transaction_routes import transaction_bp
from constants.constants import APP_LOG_FILE
from constants.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, CRJYOUTH_MAIL_NO_REPLY, LOG_LEVEL


# -------------------------------
# Initialize Flask app
# -------------------------------
app = Flask(__name__)

# -------------------------------
# Mail Configuration (default: support)
# -------------------------------
if SMTP_PORT == 465:
    SMTP_USE_SSL = True
    SMTP_USE_TLS = False
else:
    SMTP_USE_SSL = False
    SMTP_USE_TLS = True

app.config['MAIL_SERVER'] = SMTP_HOST
app.config['MAIL_PORT'] = SMTP_PORT
app.config['MAIL_USE_SSL'] = SMTP_USE_SSL
app.config['MAIL_USE_TLS'] = SMTP_USE_TLS
app.config['MAIL_USERNAME'] = SMTP_USER
app.config['MAIL_PASSWORD'] = SMTP_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = CRJYOUTH_MAIL_NO_REPLY

# -------------------------------
# Initialize Mail
# -------------------------------
mail.init_app(app)

# -------------------------------
# Argon2 Configuration (4GB RAM, 1-core CPU)
# -------------------------------
app.config['ARGON2_TIME_COST'] = 2             # Number of iterations
app.config['ARGON2_MEMORY_COST'] = 65536       # 64 MB memory (in KiB)
app.config['ARGON2_PARALLELISM'] = 1           # Parallel threads
app.config['ARGON2_HASH_LENGTH'] = 32
app.config['ARGON2_SALT_LENGTH'] = 16

# -------------------------------
# Initialize Argon2
# -------------------------------
argon2.init_app(app)

# -------------------------------
# Logger and CORS Setup
# -------------------------------
LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=APP_LOG_FILE).get_logger()
CORS(app, 
     resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Set-Cookie"])

# -------------------------------
# Security Checks
# -------------------------------
# Verify database connection on startup
try:
    from utils.sqlite_database import get_db_session, get_database_connection
    from sqlalchemy import text
    
    # Get database connection (this initializes the pool)
    db_connection = get_database_connection()
    
    # Verify database connection on startup
    with get_db_session() as session:
        # Simple connection test
        session.execute(text("SELECT 1"))
    
    # Log pool statistics
    pool_stats = db_connection.get_pool_stats()
    LOGGER.info(f"Database connection pool verified. Pool stats: {pool_stats}")
except Exception as ex:
    LOGGER.critical(f"Database connection failed - {ex}")
    raise RuntimeError(f"Application startup failed: {ex}")

# -------------------------------
# Register Blueprints
# -------------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(transaction_bp)

# -------------------------------
# Start Application
# -------------------------------
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5001, debug=True)
