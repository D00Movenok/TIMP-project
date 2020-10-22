from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


salt = 'Qwerty1337'

app = Flask(__name__, static_folder='static')
app.secret_key = salt
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)

import models
import routes

db.create_all()
