# -*- coding: utf-8 -*-

import logging
import os
import binascii

from passlib.hash import pbkdf2_sha512
from sqlalchemy.orm.exc import NoResultFound

from aetherguild.listener_service.tables import User, Session
from aetherguild.listener_service.session import UserSession
from basehandler import BaseHandler

log = logging.getLogger(__name__)


class AuthHandler(BaseHandler):
    def login(self, track_route, message):
        username = message['data']['username']
        password = message['data']['password']
        key = binascii.hexlify(os.urandom(16))

        # Find the user by username, fail with error if not found
        try:
            user = User.get_one(self.db, username=username, active=True)
        except NoResultFound:
            # Attempt to protect against timing attacks
            pbkdf2_sha512.verify(password, password)
            self.send_error(401, "Wrong username and/or password")
            return

        # Make sure password matches
        if pbkdf2_sha512.verify(password, user.password):
            # Create a new session to database
            # TODO: CLEANUP OLD SESSIONS
            s = Session()
            s.user = user.id
            s.session_key = key
            self.db.add(s)
            self.db.commit()

            # Send control packet for the socket server
            self.send({'session_key': key}, is_control=True)

            # Send authentication successful packet to the web client
            self.send_message({
                'session_key': key,
                'user': user.serialize()
            })
            log.info("Login OK for user %s", username)
        else:
            self.send_error(401, "Wrong username and/or password")
            log.warning("Login failed for user %s", username)

    def authenticate(self, track_route, message):
        key = message['data']['session_key']
        user_session = UserSession(self.db, key)
        if user_session.is_valid():
            user_session.update()

            # Send control packet for the socket server
            self.send({'session_key': key}, is_control=True)

            # Send authentication successful packet to the web client
            self.send_message({
                'session_key': key,
                'user': user_session.user.serialize()
            })
        else:
            self.send_error(401, "Invalid session key")

    def handle(self, track_route, message):
        # If we fail here, it's fine. An exception handler in upwards takes care of the rest.
        cbs = {
            'login': self.login,
            'authenticate': self.authenticate
        }
        cbs[track_route.pop(0)](track_route, message)
