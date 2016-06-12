# -*- coding: utf-8 -*-

import logging
from copy import copy

from handlers.authhandler import AuthHandler
from handlers.pinghandler import PingHandler
from session import UserSession

log = logging.getLogger(__name__)


class MessageRouter(object):
    def __init__(self, db_connection, mq_session):
        self.db_connection = db_connection
        self.mq_session = mq_session
        self.handlers = {
            'auth': AuthHandler,
            'ping': PingHandler,
            None: None
        }

    def handle(self, connection_id, session_key, message):
        if len(message['route']) > 32:
            log.warning("Route field was too long!")
            return
        full_route = copy(message['route'])
        track_route = full_route.split('.')
        receipt_id = copy(message.get('receipt'))

        # Select a correct handler according to the first entry in the route
        r = track_route.pop(0)
        try:
            handler = self.handlers[r]
        except KeyError:
            log.warning(u"MessageRouter: No handler found for packet route %s.", full_route)
            return

        # If handler for the route was found, use it.
        if handler:
            # 1. Make a new database session for the use of this handler
            # 2. Create an object of the handler and pass some important vars, then call its handle method
            # 3. If client is expecting a response to receipt and we fail, send a response just in case
            # 4. Update user session data and Make sure database session is closed (!!!)
            log.info(u"MessageRouter: Packet route %s => %s", full_route, handler.__name__)
            db_session = self.db_connection()
            user_session = UserSession(db_session, session_key)
            try:
                o = handler(db_session, self.mq_session, user_session, connection_id, receipt_id, full_route)
                o.handle(track_route, message)
            except:
                if receipt_id:
                    self.mq_session.publish({
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
                user_session.update()
                db_session.close()
