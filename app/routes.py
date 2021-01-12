import datetime
import os
from functools import wraps
from hashlib import sha256
from math import floor
from random import randint

from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from models import Bet, Event, Team, User
from settings import (ALLOWED_EXTENSIONS, DEFAULT_AVATAR, TIME_FORMAT, app, db,
                      salt)


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


def bet_iter(bets, coef):
    for bet in bets:
        bet.ended = True
        user = User.query.filter_by(id=bet.user_id).first()
        user.money = user.money + bet.amount * coef


# возвращает индекс, если надо чето добавить, дергай
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


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
def admin():
    if request.method == 'POST':
        id = int(request.form.get('id'))
        if not id:
            return 'wtf'
        elif id == 1:
            # проверяет ивенты на их прошедшесть
            # выставляет победителя (рандомно) и раздает деньги
            now = datetime.datetime.now()
            done = Event.query.filter(Event.ended == False)\
                              .filter(Event.time <= now).all()
            if done:
                for thing in done:
                    thing.ended = True
                    thing.winner = bool(randint(0,1))
                    if thing.bets:
                        bets = thing.bets
                        if len(bets) > 1:
                            if thing.winner == False:
                                coef = round(thing.amount2 / thing.amount1, 2) + 1
                                bets = Bet.query.filter_by(id=thing.bets).filter_by(team_1=True).all()
                                bet_iter(bets, coef)
                            else:
                                coef = round(thing.amount1 / thing.amount2, 2) + 1
                                bets = Bet.query.filter_by(id=thing.bets).filter_by(team_1=False).all()
                                bet_iter(bets, coef)
                        else:
                            bet_iter(bets, 1)

                db.session.commit()
                flash('Updated!')
            else:
                flash('Nothing to update(')
        elif id == 2:
            # создает ивент
            # принимает на вход параметры t1
            # t2 и time
            # лефт и райт это имена команд, которые должны
            # быть предварительно созданы
            # метод POST
            t1_name = request.form.get('t1')
            t2_name = request.form.get('t2')
            time = request.form.get('time')

            t1 = Team.query.filter_by(name=t1_name).first()
            t2 = Team.query.filter_by(name=t2_name).first()

            if not t1:
                flash('Team ' + t1_name + ' don\'t exists!')
            elif not t2:
                flash('Team ' + t2_name + ' don\'t exists!')
            elif t1 == t2:
                flash('Teamnames must not be equal!')
            else:
                try:
                    time = datetime.datetime.strptime(time, TIME_FORMAT)
                    new_event = Event(time=time,
                                      team_1=t1.id,
                                      team_2=t2.id)

                    db.session.add(new_event)
                    db.session.commit()

                    flash('Event created')
                except:
                    flash('Time format exception!')
        elif id == 3:
            # делает админом
            # на вход кушает login
            # метод POST
            login = request.form.get('login')
            user = User.query.filter_by(login=login).first()
            if user:
                user.is_admin = True
                db.session.commit()
                flash('User ' + login + ' added to admins')
            else:
                flash('User ' + login + ' not found!')
        elif id == 4:
            # создает команду
            # на вход принимает параметр name и файл
            # файл опциональный, в случае его отсутствия
            # будет установлена стандартная аватарка
            # метод POST
            name = request.form.get('name')
            if Team.query.filter_by(name=name).first():
                flash('Teamname is busy!')
            else:
                print(request.files)
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

                flash('Team ' + name + ' has created!')
        else:
            # устанавливает деньги определенному юзеру
            # кушает параметр login и amount
            # принимается только от админа
            # метод POST
            login = request.form.get('login')
            amount = request.form.get('amount')

            user = User.query.filter_by(login=login).first()

            if not user:
                return 'Wrong username!'
            else:
                try:
                    user.money = int(amount)
                    db.session.commit()
                    flash('Setted ' + amount + ' money to ' + login)
                except:
                    flash('Bad amount!')

    teams = Team.query.with_entities(Team.name).all()
    not_admins = User.query.with_entities(User.login).filter_by(is_admin=False).all()
    users = User.query.with_entities(User.login).all()
    return render_template('admin.html',
                           team_list = teams,
                           user_list = users,
                           not_admins = not_admins)


@app.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', amount = current_user.money)


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')


# снимает денег с карты
# кушает параметр amount
# прибавляет деньги на карту юзверя
# метод POST
@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'GET':
        return render_template('withdraw.html')
    else:
        try:
            amount = int(request.form.get('amount'))

            if amount < 1:
                flash('Amount must be greater than 0')
                return render_template('withdraw.html')

            user = current_user
            user.money = user.money - amount

            db.session.commit()

            return redirect(url_for('profile'))
        except:
            flash('Something get wrong')
            return render_template('withdraw.html')


# пополнение денег на карту
# кушает параметр amount
# прибавляет деньги на карту юзверя
# метод POST
@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'GET':
        return render_template('deposit.html')
    else:
        try:
            amount = int(request.form.get('amount'))
            if amount < 1:
                flash('Amount must be greater than 0')
                return render_template('deposit.html')

            user = current_user
            user.money = user.money + amount

            db.session.commit()

            return redirect(url_for('profile'))
        except:
            flash('Something get wrong')
            return render_template('deposit.html')


# устанавливает деньги определенному юзеру
# кушает параметр event_id, amount и team_1
# event_id айди евента для ставки
# amount число ставки
# team_1 булевая переменная, ставим ли
# мы на первую команду
# метод POST
# на GET возвращает страничку
@app.route('/bets', methods=['GET', 'POST'])
@login_required
def bets():
    if request.method == 'POST':
        event_id = int(request.form.get('event_id'))
        amount = int(request.form.get('amount'))
        team_1 = bool(int(request.form.get('team_1')))

        user = current_user
        event = Event.query.filter_by(id=event_id).first()

        if not event:
            flash('Bad event id!')
        elif amount < 1:
            flash('Go away, hacker')
        elif amount > user.money:
            flash('Not enough money :(')
        elif event.ended == True or event.time <= datetime.datetime.now():
            flash('Go away, cheater')
        else:
            single_bet_test = Bet.query.filter(Bet.user_id == user.id)\
                                    .filter(Bet.event_id == event_id).first()
            if single_bet_test:
                flash('You already have a bet!')
            else:
                new_bet = Bet(amount=amount,
                            team_1=team_1,
                            user_id=user.id,
                            event_id=event.id)
                if team_1:
                    event.amount1 = event.amount1 + amount
                else:
                    event.amount2 = event.amount2 + amount

                user.money = user.money - amount

                db.session.add(new_bet)
                db.session.commit()

                flash('Bet is successfully created')


    events = Event.query.order_by(Event.id.desc()).all()
    event_list = []
    for event in events:
        if event.time <= datetime.datetime.now():
            is_betted = True
        else:
            is_betted = False
        amount = 0
        team_1 = False
        bet = Bet.query.filter(Bet.user_id == current_user.id)\
                       .filter(Bet.event_id == event.id).first()
        if bet:
            is_betted = True
            amount = bet.amount
            team_1 = bet.team_1
        t1 = Team.query.filter_by(id=event.team_1).one()
        t2 = Team.query.filter_by(id=event.team_2).one()
        if event.amount1 and event.amount2:
            coef1 = round(event.amount2 / event.amount1, 2) + 1
            coef2 = round(event.amount1 / event.amount2, 2) + 1
        else:
            coef1 = 2
            coef2 = 2
        event_list.append([coef1, t1.avatar_uri, t1.name, t2.name, t2.avatar_uri, coef2, event.id, is_betted, amount, team_1])
    print(event_list)
    return render_template('bets.html',
                           event_list=event_list)


@app.route('/favicon.ico')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
