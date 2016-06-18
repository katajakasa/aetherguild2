# -*- coding: utf-8 -*-

import logging
import pika
import json
import time
from pika.exceptions import ConnectionClosed

from aetherguild import config
from router import MessageRouter

log = logging.getLogger(__name__)


class Consumer(object):
    def __init__(self, db_connection):
        self.router = MessageRouter(db_connection, self)
        self.connection = None
        self.channel = None
        self._run = True

    def _connect(self):
        """ Attempts to connect to the AMQP server
        """
        self.connection = pika.BlockingConnection(pika.URLParameters(config.MQ_CONFIG))
        self.channel = self.connection.channel()
        self.channel.confirm_delivery()

    def publish(self, message, connection_id=None, broadcast=False, avoid_self=False, is_control=False, req_level=0):
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
                'is_control': is_control,
                'req_level': req_level
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

    def _listen(self):
        """ Handle incoming packets from the MQ queue

        Accept any incoming packets from the MQ queue. If the packet looks good, handle it and ACK it. This removes
        the packet from the queue. If the packet doesn't go through the handler without exceptions however, NACK the
        packet. This _should_ remove the packet from the queue and optionally add it to Dead Letter Queue in rabbitmq.
        This, of course, depends on how your rabbitmq is configured.
        """
        for method_frame, properties, body in self.channel.consume(config.MQ_TO_LISTENER):
            log.info(u"MQ: Received %s", method_frame.delivery_tag)
            log.info(u"MQ: Queue %s => %s", config.MQ_TO_LISTENER, body)
            try:
                data = json.loads(body)
                head = data['head']
                body = data['body']
                connection_id = head['connection_id']
                session_key = head.get('session_key')
                self.router.handle(connection_id, session_key, body)
                self.channel.basic_ack(method_frame.delivery_tag)
                log.info(u"MQ: ACK %s", method_frame.delivery_tag)
            except KeyboardInterrupt:
                return
            except Exception as e:
                # Something about this packet causes trouble; NACK it.
                self.channel.basic_nack(method_frame.delivery_tag, requeue=False)
                log.error(u"MQ: NACK %s", method_frame.delivery_tag, exc_info=e)

    def handle(self):
        """ Connects to the server and runs the listener. Reconnects if necessary.
        """
        while self._run:
            try:
                self._connect()
                self._listen()
            except ConnectionClosed as e:
                if self._run:
                    time.sleep(5)

    def close(self):
        """ Closes connection to the server
        """
        self._run = False
        self.channel.close()
        self.connection.close()
