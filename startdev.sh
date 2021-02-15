#!/bin/sh

. venv/bin/activate

export FLASK_ENV=development
export FLASK_APP=meet_accountmanager/server.py
export APP_SETTINGS=../settings.cfg.dev

flask run

