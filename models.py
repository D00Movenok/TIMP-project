from flask_login import UserMixin

from settings import db, login_manager


# юзер создает ставку, ставка добавляется в ивент

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    money = db.Column(db.Integer, nullable=False, default=0)
    bets = db.relationship('Bet', backref='user', lazy=True)
    is_admin = db.Column(db.Boolean, nullable=False)


class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    team_1 = db.Column(db.Boolean, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_1 = db.Column(db.Integer, nullable=False)
    team_2 = db.Column(db.Integer, nullable=False)
    bets = db.relationship('Bet', backref='event', lazy=True)
    # amount_money = db.Column(db.Integer, nullable=False, default=0)
    time = db.Column(db.DateTime, nullable=False)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    avatar_uri = db.Column(db.String(128))
    # events = db.relationship('Event', backref='teams', lazy=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
