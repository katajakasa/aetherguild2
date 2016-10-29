# -*- coding: utf-8 -*-

import logging
import tempfile
import json
import binascii
import hashlib

import requests
from PIL import Image
import bleach
from passlib.hash import pbkdf2_sha512
from sqlalchemy.orm.exc import NoResultFound

from aetherguild.listener_service.tables import User, Session, File, OldUser
from aetherguild.listener_service.user_session import UserSession, LEVEL_USER, LEVEL_GUEST
from aetherguild.listener_service.handlers.basehandler import BaseHandler, ErrorList, is_authenticated,\
    validate_message_schema
from aetherguild.listener_service.schemas.auth import *
from aetherguild.common.utils import generate_random_key
from aetherguild.listener_service.handlers.utils import validate_str_length, validate_required_field,\
    validate_password_field
from aetherguild import config

log = logging.getLogger(__name__)


class AuthHandler(BaseHandler):
    @validate_message_schema(login_request)
    def login(self, track_route, message):
        username = message['data']['username']
        password = message['data']['password']
        key = generate_random_key()

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

        # If user has password set to None, the user is a migrated user.
        # Attempt to find OldUser data.
        old_user = None
        if not user.password:
            try:
                old_user = OldUser.get_one(self.db, user=user.id)
            except NoResultFound:
                self.send_error(401, u"Wrong username and/or password")
                log.warning(u"Login failed for user %s", username)
                return

        # Verify password
        password_matches = False

        # If we have OldUser, try logging with that first
        if old_user:
            old_hash = hashlib.sha256()
            old_hash.update(password)
            old_hash.update(config.OLD_FORUM_SALT)
            new_hash = binascii.hexlify(old_user.password)
            if old_hash.hexdigest() == new_hash:
                # Save password to new user, delete OldUser
                user.password = pbkdf2_sha512.encrypt(password)
                OldUser.delete(self.db, id=old_user.id)
                self.db.add(user)
                password_matches = True

        # ... otherwise just use the normal password.
        if not old_user and pbkdf2_sha512.verify(password, user.password):
            password_matches = True

        # If password is OK, boot up a session
        if password_matches:
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
                'user': user.serialize(include_profile=True, include_username=True)
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
        profile_data = json.dumps(message['data']['profile_data'])
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
        user.profile_data = profile_data
        user.level = LEVEL_GUEST
        user.active = True
        user.password = pbkdf2_sha512.encrypt(password)
        self.db.add(user)

        self.send_message({})
        log.info(u"New user '%s' registered!", username)

    @is_authenticated
    @validate_message_schema(update_profile_request)
    def update_profile(self, track_route, message):
        new_password = message['data'].get('new_password')
        old_password = message['data'].get('old_password')
        nickname = message['data']['nickname']
        profile_data = json.dumps(message['data']['profile_data'])
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

        # Nickname is mandatory
        nickname = bleach.clean(nickname)
        validate_str_length('nickname', nickname, errors_list, 2, 32)

        # Make sure the nickname is not yet reserved
        # Only run if the previous checks didn't fail
        if not errors_list.get_list():
            try:
                user = User.get_one(self.db, nickname=nickname)
                if user.id != self.session.user.id:
                    errors_list.add_error(u"Nickname is already reserved!", 'nickname')
            except NoResultFound:
                pass

        # got validation errors, fail here
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        # Save changes
        self.session.user.nickname = nickname
        self.session.user.profile_data = profile_data
        self.db.add(self.session.user)

        # On success, return the current user object
        self.send_message({
            'user': self.session.user.serialize(include_profile=True)
        })

    @is_authenticated
    @validate_message_schema(set_avatar_request)
    def update_avatar(self, track_route, message):
        avatar_url = message['data']['url']

        try:
            r = requests.get(avatar_url, stream=True, timeout=config.AVATAR_REQUIREMENTS['connection_timeout'])
        except requests.exceptions.ConnectionError as ex:
            self.send_error(450, ErrorList(u"Unable to fetch the image: Unable to connect to host", 'url'))
            log.exception(u"Unable to fetch the image: Unable to connect to host", exc_info=ex)
            return
        except requests.exceptions.Timeout as ex:
            self.send_error(450, ErrorList(u"Unable to fetch the image: Connection timeout", 'url'))
            log.exception(u"Unable to fetch the image: Connection timeout", exc_info=ex)
            return
        except (requests.exceptions.URLRequired,
                requests.exceptions.MissingSchema,
                requests.exceptions.InvalidSchema,
                requests.exceptions.InvalidURL) as ex:
            self.send_error(450, ErrorList(u"Unable to fetch the image: Invalid URL", 'url'))
            log.exception(u"Unable to fetch the image: Invalid URL", exc_info=ex)
            return
        except requests.exceptions.RequestException as ex:
            self.send_error(450, ErrorList(u"Unable to fetch the image", 'url'))
            log.exception(u"Unable to fetch the image", exc_info=ex)
            return

        # Attempt to fetch the image content to a temp file
        max_size = config.AVATAR_REQUIREMENTS['max_size']
        done_size = 0
        chunk_size = 1024
        with tempfile.NamedTemporaryFile() as tmp:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if done_size > max_size:
                    self.send_error(450, ErrorList(u"Unable to fetch the image: File size exceeds 5 megabytes", 'url'))
                    log.warning(u"Unable to fetch the image: File size exceeds 5 megabytes")
                    break
                if chunk:
                    done_size += chunk_size
                    tmp.write(chunk)
            r.close()

            # Open up the image and detect type
            tmp.seek(0)
            try:
                img = Image.open(tmp)
            except IOError as ex:
                self.send_error(450, ErrorList(u"Given URL does not contain a valid imagefile", 'url'))
                log.exception(u"Given URL does not contain a valid imagefile", exc_info=ex)
                return

            # Make sure somebody is not size/decompression bombing us
            max_input_size = [
                config.AVATAR_REQUIREMENTS['max_input_width'],
                config.AVATAR_REQUIREMENTS['max_input_height']
            ]
            if img.width >= max_input_size[0] or img.height >= max_input_size[1]:
                self.send_error(450, ErrorList(u"Image is too large; Maximum size is 2048x2048", 'url'))
                return

            # Thumbnail it
            max_output_size = [
                config.AVATAR_REQUIREMENTS['max_output_width'],
                config.AVATAR_REQUIREMENTS['max_output_height']
            ]
            if img.width >= max_output_size[0] or img.height >= max_output_size[1]:
                img.thumbnail(max_output_size)

            # Create a new database entry
            ext = img.format.lower()
            db_file = File(ext)
            self.db.add(db_file)
            self.db.flush()

            # Update user, too
            self.session.user.avatar = db_file.key
            self.db.add(self.session.user)

            # Save file to final destination
            out_format = 'PNG' if img.format == 'PNG' else 'JPEG'
            try:
                img.save(db_file.get_local_path(), out_format)
            except IOError as ex:
                self.db.rollback()
                log.exception("Unable to save image.", exc_info=ex)
                self.send_error(450, ErrorList(u"Unable to save image; try again later", 'url'))
                return

            # Things have come this far, everything must be okay. Re-send user information.
            self.send_message({
                'user': self.session.user.serialize(include_profile=True)
            })

    @is_authenticated
    def get_profile(self, track_route, message):
        self.send_message({
            'user': self.session.user.serialize(include_profile=True)
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
                'user': user_session.user.serialize(include_profile=True, include_username=True)
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
            'get_profile': self.get_profile,
            'update_avatar': self.update_avatar
        }
