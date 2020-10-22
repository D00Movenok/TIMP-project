from flask import (render_template, redirect, url_for, request, flash,
                   send_from_directory)
from flask_login import login_user, login_required, logout_user, current_user
from hashlib import sha256
from random import randint

from models import User
from __init__ import app, salt, db


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
        if not ((login != '') or password or password2):
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
def admin_login():
    return render_template('admin.html')


@app.route('/favicon.ico')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login') + '?next=' + request.url)
    return response
