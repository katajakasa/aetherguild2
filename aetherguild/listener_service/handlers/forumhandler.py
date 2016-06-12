# -*- coding: utf-8 -*-

import logging
from basehandler import BaseHandler, has_level
from aetherguild.listener_service.tables import ForumBoard, ForumSection, ForumPost, ForumThread,\
    ForumLastRead, ForumPostEdit
from aetherguild.listener_service.session import LEVEL_USER

log = logging.getLogger(__name__)


class ForumHandler(BaseHandler):
    def get_sections(self, track_route, message):
        out = []
        for section in ForumSection.get_many(self.db):
            out.append(section.serialize())
        self.send_message({'sections': out})

    def handle(self, track_route, message):
        # If we fail here, it's fine. An exception handler in upwards takes care of the rest.
        cbs = {
            'get_sections': self.get_sections,
        }
        cbs[track_route.pop(0)](track_route, message)
