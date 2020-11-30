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

from settings import (ALLOWED_EXTENSIONS, DEFAULT_AVATAR, TIME_FORMAT, app, db,
                      salt)
from models import Event, Team, User, Bet


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


# возвращает индекс, если надо чето добавить, дергай
@app.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        return render_template('index.html', key='You are authenticated')
    else:
        return render_template('index.html', key='Fuck you')


# логин
# на GET возвращает страничку с логином
# на POST кушает login и password
# соответственно логинит
# погляди на код, увидь flash и почекай доку про него
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


# логаут, тут нечего сказать
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# регистрация
# на GET возвращает страницу
# на POST кушает login, password и password2
# причем password == password2, иначе не регнет
# обрати внимание на flash, почитай в доке че это
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


# возвращает админку и может обрабатывать какие-то ивенты
# напишу ивенты и норм возвращение после того как сделаешь
# темплейт и скажешь че надо туда
@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_login():
    return render_template('admin.html')


# делает админом
# на вход кушает login
# метод POST
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


# создает команду
# на вход принимает параметр name и файл
# файл опциональный, в случае его отсутствия
# будет установлена стандартная аватарка
# метод POST
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


# создает ивент
# принимает на вход параметры t1
# t2 и time
# лефт и райт это имена команд, которые должны
# быть предварительно созданы
# метод POST
@app.route('/api/add_event', methods=['POST'])
@login_required
@admin_required
def add_event():
    t1_name = request.form.get('t1')
    t2_name = request.form.get('t2')
    time = request.form.get('time')

    t1 = Team.query.filter_by(name=t1_name).first()
    t2 = Team.query.filter_by(name=t2_name).first()

    if not t1:
        return 'Team one don\'t exists!'
    if not t2:
        return 'Team two don\'t exists!'
    try:
        time = datetime.datetime.strptime(time, TIME_FORMAT)
    except:
        return 'Time format exception!'

    new_event = Event(time=time,
                      team_1=t1.id,
                      team_2=t2.id)

    db.session.add(new_event)
    db.session.commit()

    return 'Ok!'


# устанавливает деньги определенному юзеру
# кушает параметр login и amount
# принимается только от админа
# метод POST
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


# устанавливает деньги определенному юзеру
# кушает параметр event_id, amount и team_1
# event_id айди евента для ставки
# amount число ставки
# team_1 булевая переменная, ставим ли
# мы на первую команду
# метод POST
@app.route('/api/set_bet', methods=['POST'])
@login_required
def set_bet():
    event_id = int(request.form.get('event_id'))
    amount = int(request.form.get('amount'))
    team_1 = request.form.get('team_1')

    user = current_user
    event = Event.query.filter_by(id=event_id).first()

    if team_1:
        team_1 = True
    else:
        team_1 = False

    if not event:
        return 'Bad event id!'
    if amount < 1:
        return 'Fuck you'
    if amount > user.money:
        return 'Not enough money :('

    single_bet_test = Bet.query.filter(Bet.user_id == user.id).filter(Bet.event_id == event_id).first()
    if single_bet_test:
        return 'You already have a bet!'

    new_bet = Bet(amount=amount,
                  team_1=team_1,
                  user_id=user.id,
                  event_id=event.id)
    user.money = user.money - amount

    db.session.add(new_bet)
    db.session.commit()

    return 'Ok!'


@app.route('/favicon.ico')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
