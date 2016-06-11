# -*- coding: utf-8 -*-

import logging
from copy import copy

from handlers.authhandler import AuthHandler

log = logging.getLogger(__name__)


class MessageHandler(object):
    def __init__(self, db_session, mq_session):
        self.db_session = db_session
        self.mq_session = mq_session

    def handle(self, connection_id, message):
        route = copy(message.get('route', [None]))
        if type(route) != list:
            log.warning(u"Route entry in message body is not a list!")
            return
        if len(route) == 0:
            log.warning(u"Route list in message body is empty!")
            return
        handler = {
            'auth': AuthHandler(self.db_session, self.mq_session),
            None: None
        }[route.pop()]
        if handler:
            handler.handle(route, connection_id, message)
