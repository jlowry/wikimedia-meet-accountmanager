from hashlib import pbkdf2_hmac
from os import urandom
from getpass import getpass

def main():
    token = getpass(prompt='Enter new token: ')

    with open('salt', 'w') as f:
        salt = urandom(16)
        f.write(salt.hex())

    with open('salt', 'r') as s:
        salt = bytes.fromhex(s.read())
        with open('token', 'w') as f:
            f.write(pbkdf2_hmac('sha256', bytes(token, 'utf-8'), salt, 100000).hex())

if __name__ == "__main__":
    main()

