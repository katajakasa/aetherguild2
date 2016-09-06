# -*- coding: utf-8 -*-

import logging

from aetherguild.listener_service.tables import User
from aetherguild.listener_service.user_session import LEVEL_ADMIN
from basehandler import BaseHandler, validate_message_schema, has_level
from aetherguild.listener_service.schemas import get_users_request

log = logging.getLogger(__name__)


class AdminHandler(BaseHandler):
    @has_level(LEVEL_ADMIN)
    @validate_message_schema(get_users_request)
    def get_users(self, track_route, message):
        include_deleted = message['data']['include_deleted']
        start = message['data'].get('start')
        count = message['data'].get('count')

        # Form the query
        query = self.db.query(User)
        if not include_deleted:
            query = query.filter(User.deleted == False)
        users_count = query.count()
        query = query.order_by(User.username.asc())
        if start:
            query = query.offset(start)
        if count:
            query = query.limit(count)

        # Serialize objects
        out_list = []
        for user in query:
            out_list.append(user.serialize(include_username=True, include_deleted=True))

        # Dump out the object list
        self.send_message({
            'users_count': users_count,
            'users': out_list
        })

    def get_routes(self):
        return {
            'get_users': self.get_users,
        }
