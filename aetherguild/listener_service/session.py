# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from aetherguild.listener_service.tables import User, Session
from sqlalchemy.orm.exc import NoResultFound

log = logging.getLogger(__name__)

LEVEL_GUEST = 0
LEVEL_USER = 1
LEVEL_ADMIN = 2


class UserSession(object):
    def __init__(self, db_session, session_key):
        self.db = db_session
        self.user = None
        self.session = None

        # Looks for existing session if session_key is not None
        if session_key:
            try:
                self.session = Session.get_one(db_session, session_key=session_key)
            except NoResultFound:
                pass

        # Find user associated with the session. If no user exists, then invalidate the session too.
        if self.session:
            try:
                self.user = User.get_one(db_session, id=self.session.user)
            except NoResultFound:
                Session.delete(db_session, session_key=session_key)
                self.session = None

    def is_valid(self):
        """ Checks if this is a valid session for authenticated user """
        return self.session is not None

    def has_level(self, level):
        if level == LEVEL_GUEST:
            return True
        if self.user is not None:
            return level <= self.user.level
        return False

    def update(self):
        if self.session:
            self.db.query(Session).filter_by(id=self.session.id).update({'activity_at': datetime.utcnow()})
