# -*- coding: utf-8 -*-

import logging
import os
import binascii

from passlib.hash import pbkdf2_sha512
from sqlalchemy.orm.exc import NoResultFound

from aetherguild.listener_service.tables import User, Session
from aetherguild.listener_service.user_session import UserSession, LEVEL_USER
from basehandler import BaseHandler, is_authenticated

log = logging.getLogger(__name__)


class AuthHandler(BaseHandler):
    def login(self, track_route, message):
        username = message['data']['username']
        password = message['data']['password']
        key = binascii.hexlify(os.urandom(16))

        # Find the user by username, fail with error if not found
        try:
            user = User.get_one(self.db, username=username, deleted=False)
        except NoResultFound:
            # Attempt to protect against timing attacks
            pbkdf2_sha512.verify(password, '$pbkdf2-sha512$25000$/d8bg5CSUuq9lxLCm'
                                           'PNeCw$v8i0AT1iLaj77KSY15JwjzGX/JY.RvZJ'
                                           'ACYqGO96gRdGX.8TicEfEidec/1zfuWh961kqa'
                                           'v0osbPglBV/z.F6Q')
            self.send_error(401, u"Wrong username and/or password")
            log.warning(u"Login failed for user %s", username)
            return

        # Make sure password matches
        if pbkdf2_sha512.verify(password, user.password):
            # Create a new session to database
            # TODO: CLEANUP OLD SESSIONS
            s = Session()
            s.user = user.id
            s.session_key = key
            self.db.add(s)

            # Send control packet for the socket server
            self.send_control({
                'session_key': key,
                'level': user.level
            })

            # Send authentication successful packet to the web client
            self.send_message({
                'session_key': key,
                'user': user.serialize()
            })

            # Broadcast to other users that this one has logged in
            self.broadcast_message({
                'user': user.serialize()
            }, req_level=LEVEL_USER, avoid_self=True)
            log.info(u"Login OK for user %s", username)
        else:
            self.send_error(401, u"Wrong username and/or password")
            log.warning(u"Login failed for user %s", username)

    @is_authenticated
    def logout(self, track_route, message):
        self.session.invalidate()
        self.send_control({'loggedout': True})
        self.send_message({'loggedout': True})
        self.broadcast_message({
            'user': self.session.user.serialize()
        }, req_level=LEVEL_USER, avoid_self=True)
        log.info(u"Logout OK for user %s", self.session.user.username)

    def authenticate(self, track_route, message):
        key = message['data']['session_key']
        user_session = UserSession(self.db, key)
        if user_session.is_valid():
            user_session.close()

            # Send control packet for the socket server
            self.send_control({
                'session_key': key,
                'level': user_session.user.level
            })

            # Send authentication successful packet to the web client
            self.send_message({
                'session_key': key,
                'user': user_session.user.serialize()
            })

            # Broadcast to other users that this one has logged in
            self.broadcast_message({
                'user': user_session.user.serialize()
            }, req_level=LEVEL_USER, avoid_self=True)
        else:
            self.send_error(401, u"Invalid session key")

    def handle(self, track_route, message):
        # If we fail here, it's fine. An exception handler in upwards takes care of the rest.
        cbs = {
            'login': self.login,
            'logout': self.logout,
            'authenticate': self.authenticate
        }
        cbs[track_route.pop(0)](track_route, message)
