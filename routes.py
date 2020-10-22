import datetime
import os
from ast import literal_eval
from functools import wraps
from hashlib import sha256
from random import randint

from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from __init__ import (ALLOWED_EXTENSIONS, DEFAULT_AVATAR, TIME_FORMAT, app, db,
                      salt)
from models import Event, Team, User


def admin_required(response):
    @wraps(response)
    def decorated_function(*args, **kwargs):
        if current_user.is_admin:
            return response(*args, **kwargs)
        return redirect(url_for('index'))
    return decorated_function


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login') + '?next=' + request.url)
    return response


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        return render_template('index.html', key='You are authenticated')
    else:
        return render_template('index.html', key='Fuck you')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        if login and password:
            user = User.query.filter_by(login=login).first()
            password = sha256((password+salt).encode()).hexdigest()
            if user and user.password == password:
                login_user(user)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('index'))
            else:
                flash('Incorrect login or password')
        else:
            flash('Please enter login and password')
    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if not (login and password and password2):
            flash('Please fill all fields')
        elif password != password2:
            flash('Passwords are not equal!')
        elif User.query.filter_by(login=login).first():
            flash('Login is busy')
        else:
            password = sha256((password+salt).encode()).hexdigest()
            new_user = User(login=login,
                            password=password,
                            is_admin=False)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_login():
    return render_template('admin.html')


@app.route('/api/add_admin', methods=['POST'])
@login_required
@admin_required
def add_admin():
    login = request.form.get('login')
    user = User.query.filter_by(login=login).first()
    if user:
        user.is_admin = True
        db.session.commit()
        return 'Ok!'
    else:
        return 'User not found!'


@app.route('/api/add_team', methods=['POST'])
@login_required
@admin_required
def add_team():
    name = request.form.get('name')
    if Team.query.filter_by(name=name).first():
        return 'Teamname is busy!'

    if 'file' not in request.files:
        avatar_uri = DEFAULT_AVATAR
    else:
        file = request.files['file']
        if file and allowed_file(file.filename) and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            avatar_uri = filename
        else:
            avatar_uri = DEFAULT_AVATAR

    new_team = Team(name=name,
                    avatar_uri=avatar_uri)
    db.session.add(new_team)
    db.session.commit()

    return 'Ok!'


@app.route('/api/add_event', methods=['POST'])
@login_required
@admin_required
def add_event():
    right_team = request.form.get('right_team')
    left_team = request.form.get('left_team')
    time = request.form.get('time')

    right_team = Team.query.filter_by(name=right_team).first()
    left_team = Team.query.filter_by(name=left_team).first()

    if not right_team:
        return 'Right team don\'t exists!'
    if not left_team:
        return 'Left team don\'t exists!'
    try:
        time = datetime.datetime.strptime(time, TIME_FORMAT)
    except:
        return 'Time format exception!'
    
    new_event = Event(right_team=right_team.id,
                      left_team=left_team.id,
                      time=time)

    db.session.add(new_event)
    db.session.flush()

    _games = literal_eval(right_team.games)
    _games.append(new_event.id)
    right_team.games = str(_games)

    _games = literal_eval(left_team.games)
    _games.append(new_event.id)
    left_team.games = str(_games)

    db.session.commit()

    return 'Ok!'


@app.route('/api/set_money', methods=['POST'])
@login_required
@admin_required
def set_money():
    login = request.form.get('login')
    amount = request.form.get('amount')
    
    user = User.query.filter_by(login=login).first()

    if not user:
        return 'Wrong username!'
    
    try:
        user.money = int(amount)
    except:
        return 'Bad amount!'
    db.session.commit()

    return 'Ok!'


@app.route('/favicon.ico')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
