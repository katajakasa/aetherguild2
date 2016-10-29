# -*- coding: utf-8 -*-

import logging

from sqlalchemy.orm.exc import NoResultFound

from aetherguild.listener_service.tables import User, Session
from aetherguild.listener_service.user_session import LEVEL_ADMIN
from .basehandler import BaseHandler, validate_message_schema, has_level
from aetherguild.listener_service.schemas.admin import *

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

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_user_request)
    def delete_user(self, track_route, message):
        user_id = message['data']['user']

        # Make sure the user exists and get the reference
        try:
            user = User.get_one(self.db, id=user_id, deleted=False)
        except NoResultFound:
            self.send_error(404, u"User not found")
            return

        # Set deleted flag
        user.deleted = True
        self.db.add(user)

        # Invalidate sessions where user is the owner
        Session.delete(self.db, user=user.id)

        # Just send an empty notification
        self.send_message({})

    def get_routes(self):
        return {
            'get_users': self.get_users,
            'delete_user': self.delete_user
        }
