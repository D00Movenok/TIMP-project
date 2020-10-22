from flask_login import UserMixin

from __init__ import db, login_manager


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    money = db.Column(db.Integer, nullable=False, default=0)
    bets = db.Column(db.Text, nullable=False, default='[]')
    m_per_bets = db.Column(db.Integer, nullable=False, default=0)
    is_admin = db.Column(db.Boolean, nullable=False)


class Event(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    right_team = db.Column(db.Integer, nullable=False)
    right_bets = db.Column(db.Text, nullable=False, default='[]')
    left_team = db.Column(db.Integer, nullable=False)
    left_bets = db.Column(db.Text, nullable=False, default='[]')
    amount_money = db.Column(db.Integer, nullable=False, default=0)
    time = db.Column(db.DateTime, nullable=False)


class Team(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    avatar_uri = db.Column(db.String(128))
    games = db.Column(db.Text, nullable=False, default='[]')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
