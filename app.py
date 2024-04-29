# Import necessary modules
from extensions import db, login_manager, UPLOAD_FOLDER
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from models import User
from flask import Flask, render_template
from flask_login import current_user
from routes.main import main
from routes.auth import auth
import random
import string
from generate_dummies import generate_dummy_users

import logging

# Set up logging
logging.basicConfig(level=logging.ERROR)  # Log all errors

# Configure app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize CSRF protection
csrf = CSRFProtect(app)

# initialize the database and login manager extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Creating tables
with app.app_context():
    db.create_all()


# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def page_not_found(error):
    return render_template('403.html'), 404



# Registering Blueprints
app.register_blueprint(auth)
app.register_blueprint(main)


if __name__ == '__main__':
    with app.app_context():
        generate_dummy_users(app, num_users=100)
    app.run(debug=True)

