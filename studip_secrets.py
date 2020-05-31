from cryptography.fernet import Fernet
import os
import sqlite3
import datetime

key_file = 'fernet_key.key'
directory = 'studip/secrets/'
db_file = 'secrets.db'
try:
    file = open(directory + key_file, 'r')
    key = file.read().encode()
except FileNotFoundError:
    file = open(directory + key_file, 'w')
    key = Fernet.generate_key()
    file.write(key.decode())


def init():
    os.makedirs(directory, exist_ok=True)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS studip_users (id integer primary key, user text,username text, password text, UNIQUE(username))')
        conn.commit()
    except sqlite3.Error as error:
        print(error)
    finally:
        if conn:
            conn.close()


def input_user(user, username, password):
    f = get_fernet()
    encrypted_pwd = f.encrypt(password.encode())
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('REPLACE INTO studip_users(user,username,password) VALUES (?,?,?)',
                       (user, username, encrypted_pwd))
        conn.commit()
    except sqlite3.Error as error:
        print(error)
    finally:
        if conn:
            conn.close()


def get_user_login(user):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username,password FROM studip_users WHERE user = ?', (user,))
        userdata = cursor.fetchall()[0]
        userdata = (userdata[0], get_fernet().decrypt(userdata[1]).decode())
        conn.commit()
    except sqlite3.Error as error:
        print(error)
        userdata = None
    finally:
        if conn:
            conn.close()
            return userdata


def get_fernet():
    return Fernet(key)


def get_db_connection():
    return sqlite3.connect(directory + db_file)
