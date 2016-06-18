# -*- coding: utf-8 -*-

import logging
import json

from pika import BlockingConnection, URLParameters
from pika.spec import BasicProperties

from aetherguild import config

log = logging.getLogger(__name__)


class MQConnection(object):
    def __init__(self):
        self.connection = None
        self.channel = None
        pika_logger = logging.getLogger('pika')
        pika_logger.setLevel(logging.CRITICAL)

    def connect(self):
        self.connection = BlockingConnection(URLParameters(config.MQ_CONFIG))
        self.channel = self.connection.channel()
        self.channel.confirm_delivery()
        log.info("MQ: Connected")

    def is_closed(self):
        return self.connection.is_closed

    def publish(self, message):
        self.channel.basic_publish(
            exchange=config.MQ_EXCHANGE,
            routing_key=config.MQ_FROM_LISTENER,
            body=json.dumps(message),
            properties=BasicProperties(
                content_type="application/json",
                delivery_mode=1))

    def consume(self):
        return self.channel.consume(config.MQ_TO_LISTENER, inactivity_timeout=0.1)

    def cancel_consumer(self):
        self.channel.cancel()

    def ack(self, tag):
        self.channel.basic_ack(tag)

    def nack(self, tag):
        self.channel.basic_nack(tag, requeue=False)

    def close(self):
        self.channel.close()
        self.connection.close()
        log.info("MQ: Connection closed")
