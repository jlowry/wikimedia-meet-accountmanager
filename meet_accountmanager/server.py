import hashlib
import json
import time
import os
import subprocess
from subprocess import STDOUT, PIPE
from datetime import datetime, timedelta, timezone
import sqlite3
from contextlib import closing
from secrets import token_hex
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, g
from flask.logging import default_handler
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, HiddenField, PasswordField
from wtforms.validators import DataRequired, InputRequired, EqualTo, ValidationError
import re

class ValidUsernameCharacters:
    def __init__(self):
        self.re = re.compile("""^\w[\w.-_]{2,64}$""")

    def __call__(self, form, field):
        if not self.re.match(field.data):
            raise ValidationError("Username must contain only word characters and period '.', hyphen '-', and underscore '_'.")


class StartWithAWordCharacter:
    def __init__(self):
        self.re = re.compile("""^\w""")

    def __call__(self, form, field):
        if not self.re.match(field.data):
            raise ValidationError("Username must be start with a word character.")


class UsernameIsAvailable:
    def __init__(self):
        self.re = re.compile("""^\s""")

    def __call__(self, form, field):
        if not self.re.match(field.data):
            raise ValidationError("Please choose a different username this one is not available.")


class CreateUserForm(FlaskForm):
    username = StringField('Login Id', validators=[DataRequired(), StartWithAWordCharacter(), ValidUsernameCharacters(), UsernameIsAvailable()], description="Use only letters, numbers, period, hypthen, and underscore. Must be at least 3 characters. Must not start with a period.")
    password = PasswordField('New Password', [InputRequired(), EqualTo('confirm', message='Passwords must match')], description='Choose a strong password not used elsewhere. Must be at least 8 characters.')
    confirm = PasswordField('Repeat Password')
    token = HiddenField('token', [InputRequired()])


class GenerateTokenForm(FlaskForm):
    token = StringField('token', validators=[DataRequired()])

app = Flask(__name__)
if 'APP_SETTINGS' in os.environ:
    app.config.from_envvar('APP_SETTINGS')
    if 'LOG_FILE' in app.config:
        app.logger.removeHandler(default_handler)
        app.logger.addHandler(RotatingFileHandler(app.config['LOG_FILE'], maxBytes=2000, backupCount=10))

config_dir = os.path.realpath(app.config.get('CONFIG_DIR', '/etc/meet-accountmanager'))
state_dir = os.path.realpath(app.config.get('STATE_DIR', '/var/lib/meet-accountmanager'))

with open(os.path.join(config_dir, 'key'), 'r') as key_file:
    app.secret_key = bytes.fromhex(key_file.read())

csrf = CSRFProtect(app)

password_path = os.path.join(config_dir, 'password')
salt_path = os.path.join(config_dir, 'salt')
db_path = os.path.join(state_dir, 'state.sqlite3')

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

def get_db():
    app.logger.debug(f"db_path: {db_path}") 
    if 'db' not in g:
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def register_account(user, password):
    completed_process = subprocess.run(['/usr/bin/sudo', '-u', 'prosody', '/usr/bin/prosodyctl', '--config', '/etc/prosody/prosody.cfg.lua', 'register', user, 'jitsi.localdev', password], stdout=PIPE, stderr=STDOUT, encoding="utf-8")
    if completed_process.returncode == 0:
        app.logger.info(f"registered user: {user}")
    else:
        app.logger.error(f"Problem creating user: {user} with prosodyctl register")
        app.logger.error(f"prosodyctl output:\n{completed_process.stdout}")

def auth_ticketmaster(password):
    time.sleep(2)
    with open(password_path, 'r') as password_file, open(salt_path, 'r') as salt_file:
        ticketmaster_password = bytes.fromhex(password_file.read())
        salt = bytes.fromhex(salt_file.read())
    dk = hashlib.pbkdf2_hmac('sha256', bytes(password, 'utf-8'), salt, 100000)
    return dk == ticketmaster_password


def auth_token(token):
    db = get_db()
    results = db.execute("""SELECT expiry as "expiry [timestamp]" FROM tokens WHERE token = ?""", (token,)).fetchall()
    for result in results:
        if result[0] > datetime.utcnow():
            return True
        else:
            # delete expired token
            delete_token(token)

    return False

def delete_token(token):
    with db:
        db.execute("DELETE FROM tokens WHERE token = ?", (token,))

def gen_token():
    token = token_hex(32)
    expiry = datetime.utcnow() + timedelta(days=7)
    db = get_db()
    with db:
        db.execute("INSERT INTO tokens (token, expiry) VALUES (?, ?)", (token, expiry))
    return token


@app.route("/")
def hello():
    return redirect(url_for('create_user'))


@app.route("/generate_token", methods=['GET'])
def generate_token():
    form = GenerateTokenForm()
    return render_template('generate.html', form=form)


@app.route("/generate_token", methods=['POST'])
def generate_token_post():
    if not auth_ticketmaster(request.form['token'].strip()):
        time.sleep(10)
        return 'Not allowed'
    return render_template('token_generated.html', token=gen_token())


@app.route("/create", methods=['GET'])
def create_user():
    token = request.args.get('token', '')
    if not auth_token(token):
        return render_template('invalidinvite.html', invalid_token=True)
    
    form = CreateUserForm(token=token)
    
    return render_template('create.html', form=form)


@app.route("/create", methods=['POST'])
def create_user_post():
    token = request.form.get('token', '')
    if not auth_token(token):
        return render_template('invalidinvite.html', invalid_token=True)

    form = CreateUserForm()
    if form.validate_on_submit():
        register_account(form.username, form.password)
        delete_token(form.token)
        return render_template('success.html')
    
    return render_template('create.html', form=form)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
