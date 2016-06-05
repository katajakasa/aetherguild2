# -*- coding: utf-8 -*-


class BaseHandler(object):
    def __init__(self, db_session, mq_session):
        self.db_session = db_session
        self.mq_session = mq_session

    def handle(self, connection_id, message):
        pass
