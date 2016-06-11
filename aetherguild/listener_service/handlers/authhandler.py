# -*- coding: utf-8 -*-

import logging

from passlib.hash import pbkdf2_sha512

from aetherguild.listener_service.tables import User, Session
from basehandler import BaseHandler

log = logging.getLogger(__name__)


class AuthHandler(BaseHandler):
    def handle(self, route, connection_id, message):
        # Just ping back the data for now
        self.mq_session.publish(message=message, connection_id=connection_id)
