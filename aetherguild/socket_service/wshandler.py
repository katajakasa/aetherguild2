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
        try:
            if message['head']['broadcast']:
                for key, connection in cls.connections.items():
                    connection.write_message(message['body'])
            else:
                connection_id = message['head']['connection_id']
                connection = cls.connections.get(connection_id)
                if connection:
                    connection.write_message(message['body'])
            return True
        except TypeError:
            log.info("Sock: Dropped bad message: %s", message)
            return True

