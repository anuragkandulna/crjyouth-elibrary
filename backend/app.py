"""
Start application here.
"""

from flask import Flask
from flask_cors import CORS
from utils.security import argon2
from utils.my_logger import CustomLogger
from utils.mail_setup import mail
from routes.auth import auth_bp
from constants.constants import APP_LOG_FILE
from constants.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, CRJYOUTH_MAIL_SUPPORT, LOG_LEVEL


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
app.config['MAIL_DEFAULT_SENDER'] = CRJYOUTH_MAIL_SUPPORT

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
CORS(app, resources={r"/*": {"origins": "*"}})

# -------------------------------
# Register Blueprints
# -------------------------------
app.register_blueprint(auth_bp)
# app.register_blueprint(project_bp)

# -------------------------------
# Start Application
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)
