#!/usr/bin/env python3
import argparse
import datetime
import csv
import os

from realtek_reglist import app
from realtek_reglist.models import db
from realtek_reglist.models.auth import User

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage user whitelist')
    parser.add_argument('-a', '--add', help='Add github username')
    args = parser.parse_args()

    with app.app_context():
        if args.add:
            user = User(username=args.add)
            print('Adding user {}'.format(user.username))
            db.session.add(user)
            db.session.commit()
        else:
            users = db.session.query(User.username)

            print('Current users:')
            for entry in users.all():
                print(entry[0])
