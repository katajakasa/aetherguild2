# -*- coding: utf-8 -*-

import argparse
from getpass import getpass

from listener_service.tables import User
import config

import tabulate
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from passlib.hash import pbkdf2_sha512


def check_args(a):
    if not a.username:
        print("Username parameter is required for this operation.")
        return 1

    if a.username:
        if len(a.username) > 32 or len(a.username) < 4:
            print("Username must be between 4 and 32 characters long")
            return 1

    if a.password:
        if len(a.password) < 8:
            print("Password must at least 8 characters long")
            return 1

    if a.nick:
        if len(a.nick) > 32 or len(a.nick) < 2:
            print("Nickname must be between 4 and 32 characters long")
            return 1
    else:
        a.nick = a.username

    return 0


def add_user(a):
    # Require password for new users. If one is not given vie commandline, get it here.
    if not a.password or a.password == '':
        a.password = getpass("Password: ")

    # Check inputs
    ret_val = check_args(a)
    if ret_val != 0:
        return ret_val

    s = db_session()

    user = User()
    user.username = a.username
    user.nickname = a.nick
    user.level = userlevels_choices.index(a.level)
    user.password = pbkdf2_sha512.encrypt(a.password)

    s.add(user)
    try:
        s.commit()
    except User.IntegrityError as e:
        print("Error: {}".format(e.message))
        return 1
    finally:
        s.close()

    print("User {} succesfully added!".format(a.username))
    return 0


def del_user(a):
    ret_val = check_args(a)
    if ret_val != 0:
        return ret_val

    s = db_session()
    user = User.get_one(s, username=a.username)
    user.deleted = True
    s.add(user)
    s.commit()
    s.close()

    print("User {} deleted".format(a.username))
    return 0


def edit_user(a):
    # Check if user wants to give password but not via commandline
    if a.password == '':
        a.password = getpass("Password: ")

    ret_val = check_args(a)
    if ret_val != 0:
        return ret_val

    s = db_session()
    try:
        user = User.get_one(s, username=a.username)
        if a.nick:
            user.nickname = a.nick
        if a.level:
            user.level = userlevels_choices.index(a.level)
        if a.password:
            user.password = pbkdf2_sha512.encrypt(a.password)
        s.add(user)
        s.commit()
    except User.NoResultFound:
        print("User {} not found.".format(a.username))
        return 1
    finally:
        s.close()

    print("User {} edited".format(a.username))
    return 0


def list_users(a):
    s = db_session()
    userlist = []
    for user in User.get_many(s):
        ser = user.serialize()
        ser['level'] = userlevels_choices[ser['level']]
        userlist.append(ser)
    s.close()
    headers = {
        'id': 'ID',
        'username': 'Username',
        'nickname': 'Nickname',
        'level': 'Level',
        'created_at': 'Created At',
        'last_contact': 'Last Contact At'
    }
    print(tabulate.tabulate(userlist, headers, tablefmt="grid"))
    return 0


if __name__ == '__main__':
    userlevels_choices = ['guest', 'user', 'admin']
    ops_choices = ['add', 'delete', 'edit', 'list']

    # Form the argument parser (first argument is positional and required)
    parser = argparse.ArgumentParser(description='Manage users for the website')
    parser.add_argument('operation', nargs='+', choices=ops_choices, help='Operation')
    parser.add_argument('--username', type=str, help='Username')
    parser.add_argument('--password', type=str, nargs='?', help='Password', default='')
    parser.add_argument('--nick', type=str, help='User nickname')
    parser.add_argument('--level', type=str, choices=userlevels_choices, help='User privilege level', default='user')
    args = parser.parse_args()

    # Initialize a database session
    db_session = sessionmaker()
    engine = create_engine(config.DATABASE_CONFIG, pool_recycle=3600)
    db_session.configure(bind=engine)

    # Find the correct operation function and call it with arguments as a parameter
    op = {
        'add': add_user,
        'delete': del_user,
        'edit': edit_user,
        'list': list_users
    }[args.operation[0]]
    exit(op(args))
