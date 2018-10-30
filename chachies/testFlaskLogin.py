from flask import Flask
from flask import session
from flask_session import Session
from flask import Flask,render_template, flash,url_for,redirect,request,Response
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from flask_login import LoginManager,login_user,logout_user,login_required
import sys,traceback
import datetime

server = Flask(__name__, static_url_path='',static_folder='static_files')

server.secret_key = 'j@i%^i@$tg$jij#$&*()^&'

class LoginForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.Required(),
    ])

class User():
    username=None
    password=None
    defaultdb=None
    def __init__(self, username,  password=None, defaultdb=None):
        self.username = username
        self.password = password
        self.defaultdb = defaultdb
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_credential(self):
        return self.username,self.password
    def get_defaultdb(self):
        return self.defaultdb
    def get_id(self):
        return self.username

@server.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('login')

@server.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'GET':
        return render_template('login.html', form=form)
    elif request.method == 'POST':
        if form.validate():
            # Login and validate the user.
            # user should be an instance of your `User` class
            username = form.username.data
            password = form.password.data

            user = User(username,password,default_db)
            login_user(user)
            flash('Logged in successfully.')
            next = request.args.get('next')
            return redirect(next or 'odorLiveUpdate')
        return render_template('login.html', form=form)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(server)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)