import json

from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello!"


@app.route("/create", methods=['POST'])
def create_user_post():
    with open('users_to_create.json', 'r') as f:
        users_to_create = json.loads(f.read())
    users_to_create.append(
        {'user': request.form['user'], 'password': request.form['password']})
    with open('users_to_create.json', 'w') as f:
        f.write(json.dumps(users_to_create))
    return 'Done!'


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000)
