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

    def publish(self, message, connection_id=None, broadcast=False, avoid_self=False, is_control=False):
        """ Publish a message to the outgoing queue

        :param message: Message to be sent to the client
        :param connection_id: ID for this connection (should match ID on socket handler)
        :param broadcast: Whether this packet should be broadcast to all listening clients
        :param avoid_self: When broadcasting, only broadcast to *other* clients
        :param is_control: Whether this packet is a control packet. If True, body is considered internal data.
        """
        publish_data = {
            'head': {
                'connection_id': connection_id,
                'avoid_self': avoid_self,
                'broadcast': broadcast,
                'is_control': is_control
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
        """ Handle incoming packets from the MQ queue

        Accept any incoming packets from the MQ queue. If the packet looks good, handle it and ACK it. This removes
        the packet from the queue. If the packet doesn't go through the handler without exceptions however, NACK the
        packet. This _should_ remove the packet from the queue and optionally add it to Dead Letter Queue in rabbitmq.
        This, of course, depends on how your rabbitmq is configured.
        """
        for method_frame, properties, body in self.channel.consume(config.MQ_TO_LISTENER):
            log.info(u"MQ: Received %s", method_frame.delivery_tag)
            try:
                data = json.loads(body)
                log.debug(u"MQ: Queue %s => %s", config.MQ_TO_LISTENER, data)
                connection_id = data['head']['connection_id']
                message_data = data['body']
                self.message_handler.handle(connection_id, message_data)
                self.channel.basic_ack(method_frame.delivery_tag)
                log.info(u"MQ: ACK %s", method_frame.delivery_tag)
            except KeyboardInterrupt:
                return
            except Exception as e:
                # Something about this packet causes trouble; NACK it.
                self.channel.basic_nack(method_frame.delivery_tag, requeue=False)
                log.error(u"MQ: NACK %s", method_frame.delivery_tag, exc_info=e)

    def close(self):
        self.channel.close()
        self.connection.close()
