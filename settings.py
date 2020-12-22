from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from hashlib import sha256


salt = 'Qwerty1337'
admin_password = 'admin'

app = Flask(__name__, static_folder='static')
app.secret_key = salt
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)

UPLOAD_FOLDER = 'static/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DEFAULT_AVATAR = 'default.png'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

TIME_FORMAT = '%Y-%m-%dT%H:%M'

import models
import routes

db.create_all()

if not models.User.query.filter_by(login='admin').first():
    password = sha256((admin_password+salt).encode()).hexdigest()
    new_user = models.User(login='admin',
                        password=password,
                        is_admin=True)
    db.session.add(new_user)
    db.session.commit()
