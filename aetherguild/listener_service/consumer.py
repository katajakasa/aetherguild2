# -*- coding: utf-8 -*-

import logging
import json
import time

from pika.exceptions import ConnectionClosed as MQConnectionClosed
from sqlalchemy.exc import DisconnectionError as DBConnectionClosed

from router import MessageRouter

log = logging.getLogger(__name__)


class Consumer(object):
    def __init__(self, db_connection, mq_connection):
        self.db_connection = db_connection
        self.mq_connection = mq_connection
        self.router = MessageRouter(db_connection, mq_connection)
        self._run = True

    def _listen(self):
        """ Handle incoming packets

        Accept any incoming packets from the MQ queue. If the packet looks good, handle it and ACK it. This removes
        the packet from the queue. If the packet doesn't go through the handler without exceptions however, NACK the
        packet. This _should_ remove the packet from the queue and optionally add it to Dead Letter Queue in rabbitmq.
        This, of course, depends on how your rabbitmq is configured.
        """
        for packet in self.mq_connection.consume():
            if packet:
                method_frame, _, body = packet
                log.info(u"MQ: Consumed packet, delivery_tag = %s", method_frame.delivery_tag)
                try:
                    data = json.loads(body)
                    self.router.handle(data['head'], data['body'])
                    self.mq_connection.ack(method_frame.delivery_tag)
                    log.info(u"MQ: ACK delivery_tag = %s", method_frame.delivery_tag)
                except Exception as e:
                    self.mq_connection.nack(method_frame.delivery_tag)
                    log.error("MQ: NACK delivery_tag = %s", method_frame.delivery_tag, exc_info=e)

            # Stop here if close has been called
            if not self._run:
                return

    def handle(self):
        """ Connects to the server and runs the listener. Reconnects to servers if necessary.
        """
        while self._run:
            try:
                if self.mq_connection.is_closed():
                    self.mq_connection.connect()
                if self.db_connection.is_closed():
                    self.db_connection.connect()
                self._listen()
                self.mq_connection.cancel_consumer()
            except MQConnectionClosed:
                if self._run:
                    time.sleep(5)
            except DBConnectionClosed:
                self.db_connection.invalidate()
                if self._run:
                    time.sleep(5)

    def close(self):
        """ Closes consumer
        """
        self._run = False
