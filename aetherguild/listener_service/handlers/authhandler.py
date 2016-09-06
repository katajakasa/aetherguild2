# -*- coding: utf-8 -*-

import logging
import os
import binascii

import bleach
from passlib.hash import pbkdf2_sha512
from sqlalchemy.orm.exc import NoResultFound

from aetherguild.listener_service.tables import User, Session
from aetherguild.listener_service.user_session import UserSession, LEVEL_USER, LEVEL_GUEST
from basehandler import BaseHandler, ErrorList, is_authenticated, validate_message_schema
from aetherguild.listener_service.schemas import login_request, register_request, profile_request, authenticate_request
from utils import validate_str_length, validate_required_field, validate_password_field

log = logging.getLogger(__name__)


class AuthHandler(BaseHandler):
    @validate_message_schema(login_request)
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

    @validate_message_schema(register_request)
    def register(self, track_route, message):
        username = message['data']['username']
        password = message['data']['password']
        nickname = bleach.clean(message['data']['nickname'])
        errors_list = ErrorList()

        validate_str_length('username', username, errors_list, 4, 32)
        validate_str_length('password', password, errors_list, 8)
        validate_str_length('nickname', nickname, errors_list, 2, 32)

        # got validation errors, fail here. Only hit DB checks if everything else is fine
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        # Make sure the username is not yet reserved
        try:
            User.get_one(self.db, username=username)
            errors_list.add_error(u"Username is already reserved!", 'username')
        except NoResultFound:
            pass

        # Make sure the nickname is not yet reserved
        try:
            User.get_one(self.db, nickname=nickname)
            errors_list.add_error(u"Nickname is already reserved!", 'nickname')
        except NoResultFound:
            pass

        # got validation errors, fail here
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        user = User()
        user.username = username
        user.nickname = nickname
        user.level = LEVEL_GUEST
        user.active = True
        user.password = pbkdf2_sha512.encrypt(password)
        self.db.add(user)

        self.send_message({})
        log.info(u"New user '%s' registered!", username)

    @is_authenticated
    @validate_message_schema(profile_request)
    def update_profile(self, track_route, message):
        new_password = message['data'].get('new_password')
        old_password = message['data'].get('old_password')
        nickname = message['data'].get('nickname')
        errors_list = ErrorList()

        # If user wants to change password, handle the checks
        if new_password:
            validate_str_length('new_password', new_password, errors_list, 8)
            validate_required_field('old_password', old_password, errors_list)

            # Only run this check if no other errors were detected
            if not errors_list.get_list():
                validate_password_field('old_password', self.session.user.password, old_password, errors_list)

            # Don't change anything if there are errors
            if not errors_list.get_list():
                self.session.user.password = pbkdf2_sha512.encrypt(new_password)
                self.db.add(self.session.user)

        # If nickname is being changed, make sure to clean and validate it thoroughly
        if nickname:
            nickname = bleach.clean(nickname)
            validate_str_length('nickname', nickname, errors_list, 2, 32)

            # Make sure the nickname is not yet reserved
            # Only run if the previous checks didn't fail
            if not errors_list.get_list():
                try:
                    User.get_one(self.db, nickname=nickname)
                    errors_list.add_error(u"Nickname is already reserved!", 'nickname')
                except NoResultFound:
                    pass

            # Don't change anything if there are errors
            if not errors_list.get_list():
                self.session.user.nickname = nickname
                self.db.add(self.session.user)

        # got validation errors, fail here
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        # On success, return the current user object
        self.send_message({
            'user': self.session.user.serialize()
        })

    @is_authenticated
    def get_profile(self, track_route, message):
        self.send_message({
            'user': self.session.user.serialize()
        })

    @is_authenticated
    def logout(self, track_route, message):
        self.session.invalidate()
        self.send_control({'loggedout': True})
        self.send_message({})
        self.broadcast_message({
            'user': self.session.user.serialize()
        }, req_level=LEVEL_USER, avoid_self=True)
        log.info(u"Logout OK for user %s", self.session.user.username)

    @validate_message_schema(authenticate_request)
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
            self.send_error(450, u"Invalid session key")

    def get_routes(self):
        return {
            'login': self.login,
            'logout': self.logout,
            'authenticate': self.authenticate,
            'register': self.register,
            'update_profile': self.update_profile,
            'get_profile': self.get_profile
        }
