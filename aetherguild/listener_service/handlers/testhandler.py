# -*- coding: utf-8 -*-

import logging
from basehandler import BaseHandler

log = logging.getLogger(__name__)


class TestHandler(BaseHandler):
    def handle(self, connection_id, message):
        # Just ping back the data for now
        self.mq_session.publish(message=message, connection_id=connection_id)
