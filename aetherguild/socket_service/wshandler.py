# -*- coding: utf-8 -*-

from aetherguild import config
import logging
import uuid
import json
from tornado.websocket import WebSocketHandler

log = logging.getLogger(__name__)


class WsHandler(WebSocketHandler):
    mq = None
    connections = {}

    def __init__(self, application, request, **kwargs):
        super(WsHandler, self).__init__(application, request, **kwargs)
        self.id = None
        self.session_key = None
        self.user_level = 0

    def check_origin(self, origin):
        if config.DEBUG:
            return True
        else:
            return super(WsHandler, self).check_origin(origin)

    def open(self):
        """ Handler for opened websocket connections """
        self.id = uuid.uuid4().hex
        self.connections[self.id] = self
        log.info("Sock: Connection opened (%s)", self.id)

    def handle_control_packet(self, message):
        route = message['route']
        if route == 'auth.authenticate' or route == 'auth.login':
            self.session_key = message['session_key']
            self.user_level = message['level']
        elif route == 'auth.logout':
            self.session_key = None
            self.user_level = 0

    def on_message(self, message):
        """ Handler for messages coming from websocket """
        try:
            decoded_data = json.loads(message)
        except ValueError:
            self.close()
            return

        # Publish our data to outgoing MQ pipe
        publish_data = {
            'head': {
                'connection_id': self.id,
                'session_key': self.session_key
            },
            'body': decoded_data
        }
        self.mq.publish(publish_data)

    def on_close(self):
        """ Handler for closed websocket connections """
        log.info("Sock: Connection closed (%s)", self.id)
        del self.connections[self.id]

    @classmethod
    def on_queue_message(cls, message):
        """ Handler for messages coming from MQ queue """
        header = message['head']
        body = message['body']
        connection_id = header['connection_id']
        avoid_self = header['avoid_self']
        broadcast = header['broadcast']
        is_control = header['is_control']
        req_level = header['req_level']

        # Many whelps! Handle it!!1
        if broadcast:
            for key, connection in cls.connections.items():
                # If broadcasting but avoiding self, skip connection if required
                if avoid_self and key == connection_id:
                    continue
                # Make sure client has sufficient privileges
                if connection.user_level >= req_level:
                    # If packet is control, handle it as such.
                    # Otherwise broadcast standard message.
                    if is_control:
                        connection.handle_control_packet(body)
                    else:
                        connection.write_message(body)
        else:
            connection = cls.connections.get(connection_id)
            if connection:
                # Make sure client has sufficient privileges
                if connection.user_level >= req_level:
                    # If packet is control, handle it as such
                    # Otherwise broadcast standard message.
                    if is_control:
                        connection.handle_control_packet(body)
                    else:
                        connection.write_message(body)
