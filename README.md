# WikimediaMeetAuth
This Flask app allows creating accounts in Jitsi used by Wikimedia Meet.

## Server
The server part allows users to create tokens and use a token to create an account.


# Installation

You can install the `.deb` package using:
```

```

You will also need to add the following to a nginx.conf file:
```
    location ^~ /accountmanager/ {
      rewrite /accountmanager/(.*) /$1  break;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header Host $http_host;
      # we don't want nginx trying to do something clever with
      # redirects, we set the Host: header above already.
      proxy_redirect ~^https:\/\/[^/]*/(.*) /accountmanager/$1;
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

