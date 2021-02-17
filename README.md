# WikimediaMeetAuth
This Flask app allows creating accounts in Jitsi used by Wikimedia Meet.

## Server
The server part allows users to create tokens and use a token to create an account.


# Installation
Install dependencies. We do this through the package manager so they benefit from
security updates:
```
apt install gunicorn python3-flask python3-flaskext.wtf
```

Get package from GitHub releases:
```
curl -LO https://github.com/jlowry/wikimedia-meet-accountmanager/releases/download/0.1.0-1/python3-meet-accountmanager_0.1.0-1_all.deb
```

You can install the `.deb` package using:
```
sudo apt install ./python3-meet-accountmanager_0.1.0-1_all.deb
```
You will be asked to enter a password for that is used for
creating invitations.

You will also need to add the following two snippets to the  nginx conf file for your site.

Outside a `server` block:
```
upstream accountmanager {
    # fail_timeout=0 means we always retry an upstream even if it failed
    # to return a good HTTP response
    server unix:/run/meet-accountmanager.sock fail_timeout=0;
}
```

Inside the server block:
```
    location ^~ /accountmanager/ {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        # we don't want nginx trying to do something clever with
        # redirects, we set the Host: header above already.
        proxy_set_header SCRIPT_NAME /accountmanager;
        proxy_redirect off;
        proxy_pass http://accountmanager;
    }
```

### Creating a ticketmaster token
Run the python code in a python shell to set ticketmaster token to `test`:
```python
import hashlib
salt = 'this is an example salt'
token = 'test'
with open('salt', 'w') as f:
    f.write(salt)
with open('token', 'w') as f:
    f.write(hashlib.pbkdf2_hmac('sha256', bytes(token, 'utf-8'), bytes(salt + "\n", 'utf-8'), 100000).hex())
```



### Developing the application

#### Installing dependencies
This application uses Python 3 and Flask. Using a virtual environment is recommended:

```
# Unix-based systems
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Windows systems
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Starting a development server
You can use the `flask` command line utility to start the app:

```
# Unix-based systems
source venv/bin/activate
export FLASK_ENV=development
export FLASK_APP=server
flask run

# Windows systems
venv\Scripts\activate
set FLASK_ENV=development
set FLASK_APP=server
flask run
```

