"""
Start application here.
"""

from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from utils.security import argon2
from utils.my_logger import CustomLogger
from routes.auth import auth_bp
from constants.constants import (
    APP_LOG_FILE,
    CRJYOUTH_MAIL_SUPPORT,
)

# -------------------------------
# Initialize Flask app
# -------------------------------
app = Flask(__name__)

# -------------------------------
# Mail Configuration (default: support)
# -------------------------------
app.config['MAIL_SERVER'] = 'smtpout.secureserver.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USERNAME'] = 'akandulna@crjyouth.in'
app.config['MAIL_PASSWORD'] = 'some_pass'
app.config['MAIL_DEFAULT_SENDER'] = CRJYOUTH_MAIL_SUPPORT

# -------------------------------
# Initialize Mail
# -------------------------------
from routes.auth import mail
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
LOGGER = CustomLogger(__name__, level=20, log_file=APP_LOG_FILE).get_logger()
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
