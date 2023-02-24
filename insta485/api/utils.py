import hashlib
import logging
import sqlite3
import uuid

import flask

import insta485


def encrypt_new_password(password):
    """Generate the encrypted password from the new password."""
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    password_hash = encrypt_with_salt_password(password, salt)
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def encrypt_with_salt_password(password, salt):
    """Generate the encrypted password with the salt."""
    algorithm = 'sha512'
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    return password_hash


def check_password(password, password_db_string):
    """Check the validation of the password."""
    [algorithm, salt, password_hash] = password_db_string.split("$")
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    return hash_obj.hexdigest() == password_hash


def update_db(operation, args=()):
    """Update db record."""
    try:
        insta485.model.get_db().execute(operation, args)
        insta485.model.close_db(None)
    except sqlite3.Error as err:
        logging.error(msg="DB UPDATE FAILED", exc_info=err)


def query_db(query, args=(), one=False):
    """Perform db query."""
    cur = insta485.model.get_db().execute(query, args)
    res = cur.fetchall()
    insta485.model.close_db(None)
    return (res[0] if res else None) if one else res


def get_logname():
    """Check if user log in and return logname."""
    if 'username' not in flask.session:
        return None
    logname = flask.session['username']
    return logname


def check_auth():
    """Check http basic auth if existed."""
    if not flask.request.authorization:
        return None
    username = flask.request.authorization['username']
    password = flask.request.authorization['password']
    password_db = query_db("select password from users where username=?",
                           (username,))
    if check_password(password, password_db[0]["password"]):
        return username
    else:
        return None
