import hashlib
import json
import time
import os
import subprocess
from subprocess import STDOUT, PIPE
from secrets import token_hex
from logging.handlers import RotatingFileHandler
import requests
from flask import Flask, render_template, request, redirect, url_for
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
tokens_path = os.path.join(state_dir, 'tokens.json')

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
    time.sleep(2)
    with open(tokens_path, 'r') as f:
        tokens = json.loads(f.read())
    if token not in tokens:
        return False
    tokens.remove(token)
    with open(tokens_path, 'w') as f:
        f.write(json.dumps(tokens))
    return True


def gen_token():
    token = token_hex(32)
    with open(tokens_path, 'a+') as f:
        f.seek(0)
        tokens = json.loads(f.read())
        tokens.append(token)
        f.seek(0)
        f.write(json.dumps(tokens))
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
    if not auth_token(request.form['token'].strip()):
        time.sleep(10)
        return render_template('create.html', invalid_token=True)

    user = request.form['user']
    password = request.form['password']
    register_account(user, password)

    return render_template('success.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
