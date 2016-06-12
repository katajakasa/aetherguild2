# -*- coding: utf-8 -*-

import logging
from basehandler import BaseHandler, has_level
from aetherguild.listener_service.session import LEVEL_USER

log = logging.getLogger(__name__)


class PingHandler(BaseHandler):
    @has_level(LEVEL_USER)
    def handle(self, track_route, message):
        self.send({'ping': 'pong'})
