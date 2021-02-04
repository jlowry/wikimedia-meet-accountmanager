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
import requests
from flask import Flask, render_template, request, redirect, url_for, g
from flask.logging import default_handler

app = Flask(__name__)
if 'APP_SETTINGS' in os.environ:
    app.config.from_envvar('APP_SETTINGS')
    if 'LOG_FILE' in app.config:
        app.logger.removeHandler(default_handler)
        app.logger.addHandler(RotatingFileHandler(app.config['LOG_FILE'], maxBytes=2000, backupCount=10))

clients = ['http://jitsi.meet.eqiad.wmflabs:4000']
config_dir = os.path.realpath('/etc/meet-accountmanager')
password_path = os.path.join(config_dir, 'password')
salt_path = os.path.join(config_dir, 'salt')
state_dir = os.path.realpath('/var/lib/meet-accountmanager')
db_path = os.path.join(state_dir, 'state.sqlite3')


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

def get_db():
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
    results = db.execute("SELECT * FROM tokens WHERE token = ?", (token,)).fetchall()
    if len(results) > 0:
        with db:
            db.execute("DELETE FROM tokens WHERE token = ?", (token,))
        return True
    time.sleep(2)
    return False


def gen_token():
    token = token_hex(32)
    expiry = datetime.now() + timedelta(days=7)
    db = get_db()
    with db:
        db.execute("INSERT INTO tokens (token, expiry) VALUES (?, ?)", (token, expiry))
    return token


@app.route("/")
def hello():
    return redirect(url_for('create_user'))


@app.route("/generate_token", methods=['GET'])
def generate_token():
    return render_template('generate.html')


@app.route("/generate_token", methods=['POST'])
def generate_token_post():
    if not auth_ticketmaster(request.form['token'].strip()):
        time.sleep(10)
        return 'Not allowed'
    return render_template('token_generated.html', token=gen_token())


@app.route("/create", methods=['GET'])
def create_user():
    return render_template('create.html')


@app.route("/create", methods=['POST'])
def create_user_post():
    token = request.form['token'].strip()
    if not auth_token(token):
        time.sleep(10)
        return render_template('create.html', invalid_token=True)

    user = request.form['user']
    password = request.form['password']
    register_account(user, password)

    return render_template('success.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
