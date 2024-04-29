from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# create a login manager instance
login_manager = LoginManager()
# create a db instance
db = SQLAlchemy()

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/users_pictures')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("firebase_key.json")
app = firebase_admin.initialize_app(cred, {'storageBucket': 'fir-storeprojectteachme.appspot.com'})

bucket = storage.bucket()
