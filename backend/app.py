"""
Start application here.
"""

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from routes.auth import auth_bp
# from routes.project import project_bp
from utils.my_logger import CustomLogger


# Initialize Flask app
app = Flask(__name__)
bcrypt = Bcrypt(app)
LOGGER = CustomLogger(__name__, level=20).get_logger()
CORS(app, resources={r"/*": {"origins": "*"}})


# Register Blueprints to access routes
app.register_blueprint(auth_bp)
# app.register_blueprint(project_bp)


if __name__ == '__main__':
    app.run(debug=True)