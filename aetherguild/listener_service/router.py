# -*- coding: utf-8 -*-

import logging
from copy import copy

from handlers.authhandler import AuthHandler
from handlers.forumhandler import ForumHandler
from user_session import UserSession
from mq_session import MQSession

log = logging.getLogger(__name__)


class MessageRouter(object):
    def __init__(self, db_connection, mq_connection):
        self.db_connection = db_connection
        self.mq_connection = mq_connection
        self.handlers = {
            'auth': AuthHandler,
            'forum': ForumHandler,
            None: None
        }

    def handle(self, head, body):
        route = body['route']
        if len(route) > 32:
            log.warning("Route field was too long!")
            return
        connection_id = head['connection_id']
        session_key = head.get('session_key')
        full_route = copy(body['route'])
        track_route = full_route.split('.')
        receipt_id = copy(body.get('receipt'))

        # Select a correct handler according to the first entry in the route
        r = track_route.pop(0)
        try:
            handler = self.handlers[r]
        except KeyError:
            log.warning(u"MessageRouter: No handler found for packet route %s.", full_route)
            return

        # If handler for the route was found, use it.
        if handler:
            log.info(u"MessageRouter: Packet route %s => %s", full_route, handler.__name__)

            # Start a database session and transaction
            db_session = self.db_connection.get_session()

            # Start an MQ session and transaction
            mq_session = MQSession(self.mq_connection)
            mq_session.begin()

            # Find a User session from database matching users session key
            user_session = UserSession(db_session, session_key)

            # Attempt to handle operation. If success, commit transactions. If failure, send fail packet and rollback.
            try:
                o = handler(db_session, mq_session, user_session, connection_id, receipt_id, full_route)
                o.handle(track_route, body)
                db_session.commit()
                mq_session.commit()
            except:
                db_session.rollback()
                mq_session.rollback()
                if receipt_id:
                    self.mq_connection.publish({
                        'error': True,
                        'receipt': receipt_id,
                        'route': full_route,
                        'data': {
                            'error_code': 500,
                            'error_message': 'Server error'
                        }
                    }, connection_id=connection_id)
                raise
            finally:
                user_session.close()
                db_session.close()
                mq_session.close()
