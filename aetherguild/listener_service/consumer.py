# -*- coding: utf-8 -*-

import logging
import pika
import json

from aetherguild import config
from messages import MessageHandler

log = logging.getLogger(__name__)


class Consumer(object):
    def __init__(self, db_session):
        self.db_session = db_session
        self.message_handler = MessageHandler(db_session, self)
        self.connection = pika.BlockingConnection(pika.URLParameters(config.MQ_CONFIG))
        self.channel = self.connection.channel()

    def publish(self, message, connection_id=None, broadcast=False):
        publish_data = {
            'head': {
                'connection_id': connection_id,
                'broadcast': broadcast,
            },
            'body': message
        }
        self.channel.basic_publish(
            exchange=config.MQ_EXCHANGE,
            routing_key=config.MQ_FROM_LISTENER,
            body=json.dumps(publish_data),
            properties=pika.spec.BasicProperties(
                content_type="application/json",
                delivery_mode=1))
        log.info(u"MQ: Queue %s <= %s", config.MQ_FROM_LISTENER, publish_data)

    def handle(self):

        try:
            for method_frame, properties, body in self.channel.consume(config.MQ_TO_LISTENER):
                # Extract message and make sure it's good. If it's not, just dump the message and remove it from queue.
                try:
                    data = json.loads(body)
                    connection_id = data['head']['connection_id']
                    message_data = data['body']
                except ValueError:
                    self.channel.basic_ack(method_frame.delivery_tag)
                    continue

                # Load the data and extract body + connection_id.
                # self.publish(body, message_data)
                self.message_handler.handle(connection_id, message_data)
                self.channel.basic_ack(method_frame.delivery_tag)
        except KeyboardInterrupt:
            return

    def close(self):
        self.channel.close()
        self.connection.close()
