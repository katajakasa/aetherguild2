# -*- coding: utf-8 -*-

import logging
from copy import copy
from cerberus import Validator

from handlers.authhandler import AuthHandler
from handlers.forumhandler import ForumHandler
from handlers.adminhandler import AdminHandler
from user_session import UserSession
from mq_session import MQSession
from schemas import base_request

log = logging.getLogger(__name__)


class MessageRouter(object):
    def __init__(self, db_connection, mq_connection):
        self.db_connection = db_connection
        self.mq_connection = mq_connection
        self.handlers = {
            'auth': AuthHandler,
            'forum': ForumHandler,
            'admin': AdminHandler,
            None: None
        }

    def handle(self, head, body):
        connection_id = head['connection_id']
        session_key = head.get('session_key')

        # Validate the incoming base message first
        v = Validator(base_request)
        if not v.validate(body):
            error_data = {
                'error': True,
                'data': {
                    'error_code': 400,
                    'error_messages': [{'message': u'Bad Request'}]
                }
            }
            if body.get('receipt'):
                error_data['receipt'] = body['receipt']
            if body.get('route'):
                error_data['route'] = body['route']
            MQSession(self.mq_connection).publish(error_data, connection_id=connection_id)
            log.warning(u"MessageRouter: Invalid packet received from %s", connection_id)
            return

        # Sort out some vars
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
                    mq_session.publish({
                        'error': True,
                        'receipt': receipt_id,
                        'route': full_route,
                        'data': {
                            'error_code': 500,
                            'error_messages': [{'message': u'Server error'}]
                        }
                    }, connection_id=connection_id)
                    log.exception("Server error while running message handler")
                raise
            finally:
                user_session.close()
                db_session.close()
                mq_session.close()
