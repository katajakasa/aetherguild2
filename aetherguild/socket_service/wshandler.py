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

    def check_origin(self, origin):
        return True

    def open(self):
        """ Handler for opened websocket connections """
        self.id = uuid.uuid4().hex
        self.connections[self.id] = self
        log.info("Sock: Connection opened (%s)", self.id)

    def handle_control_packet(self, message):
        pass

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
                'connection_id': self.id
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
        connection_id = header.get('connection_id')
        avoid_self = header.get('avoid_self', False)
        broadcast = header.get('broadcast', False)
        is_control = header.get('is_control', False)

        # Handle it!!1
        if broadcast:
            for key, connection in cls.connections.items():
                if avoid_self and key == connection_id:
                    continue
                if is_control:
                    connection.handle_control_packet(body)
                else:
                    connection.write_message(body)
        else:
            connection = cls.connections.get(connection_id)
            if connection:
                if is_control:
                    connection.handle_control_packet(body)
                else:
                    connection.write_message(body)
