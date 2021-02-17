from os import urandom

def main():
    with open('key', 'w') as f:
        salt = urandom(32)
        f.write(salt.hex())

if __name__ == "__main__":
    main()

