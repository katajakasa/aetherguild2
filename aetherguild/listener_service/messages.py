# -*- coding: utf-8 -*-

import logging
from handlers.testhandler import TestHandler

log = logging.getLogger(__name__)


class MessageHandler(object):
    def __init__(self, db_session, mq_session):
        self.db_session = db_session
        self.mq_session = mq_session

    def handle(self, connection_id, message):
        message_type = message.get('type')
        handler = {
            'test': TestHandler(self.db_session, self.mq_session),
            None: None
        }[message_type]
        if handler:
            handler.handle(connection_id, message)
