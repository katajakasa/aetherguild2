# -*- coding: utf-8 -*-

import logging
import pika
import json
from aetherguild import config

log = logging.getLogger(__name__)


class MQConnection(object):
    def __init__(self, io_loop, msg_handler=None):
        self.connection = None
        self.channel = None
        self.consumer = None
        self.connected = False
        self._closing = False
        self.io_loop = io_loop
        self._on_message_handler = msg_handler

    # ------------------------ Connections ------------------------

    def set_msg_handler(self, msg_handler):
        self._on_message_handler = msg_handler

    def connect(self):
        self.connection = pika.adapters.TornadoConnection(
            pika.URLParameters(config.MQ_CONFIG),
            on_open_callback=self.on_connection_opened,
            on_open_error_callback=self.on_connection_error)

    def on_connection_opened(self, connection):
        log.info(u"MQ: Connected to AMQP server")
        self.connection = connection
        self._closing = False
        self.connected = True
        self.connection.add_on_close_callback(self.on_connection_closed)
        self.connection.channel(self.on_channel_open)

    def on_connection_error(self, connection, error_message=None):
        log.info(u"MQ: Connection error: %s", error_message)
        self.on_connection_closed(connection, 0, error_message)

    def on_connection_closed(self, connection, reply_code, reply_text):
        if self._closing:
            self.connected = False
            self.io_loop.stop()
            log.info(u'MQ: Connection closed (%d): %s.', reply_code, reply_text)
        else:
            connection.add_timeout(5, self.connect)
            log.info(u'MQ: Connection closed (%d): %s. Reconnecting.', reply_code, reply_text)

    def close(self):
        self._closing = True
        self.stop_consumer()
        self.connection.close()

    def is_connected(self):
        return self.connected

    # ------------------------ Channels ------------------------

    def on_channel_open(self, channel):
        log.info(u'MQ: Channel opened.')
        self.channel = channel
        self.channel.exchange_declare(self.on_exchange_ok, config.MQ_EXCHANGE, 'direct', durable=True)

    # ------------------------ Exchanges ------------------------

    def on_exchange_ok(self, method_frame):
        log.info(u'MQ: Exchange %s open.', config.MQ_EXCHANGE)
        self.channel.queue_declare(self.on_queue_from_declare_ok, config.MQ_FROM_LISTENER, durable=True)
        self.channel.queue_declare(self.on_queue_to_declare_ok, config.MQ_TO_LISTENER, durable=True)

    # ------------------------ Queues ------------------------

    def on_queue_from_declare_ok(self, method_frame):
        log.info(u'MQ: Queue %s declared.', config.MQ_FROM_LISTENER)
        self.channel.queue_bind(self.on_queue_from_bound_ok, config.MQ_FROM_LISTENER, config.MQ_EXCHANGE)

    def on_queue_to_declare_ok(self, method_frame):
        log.info(u'MQ: Queue %s declared.', config.MQ_TO_LISTENER)
        self.channel.queue_bind(self.on_queue_to_bound_ok, config.MQ_TO_LISTENER, config.MQ_EXCHANGE)

    def on_queue_from_bound_ok(self, method_frame):
        log.info(u'MQ: Queue %s bound to exchange %s.', config.MQ_FROM_LISTENER, config.MQ_EXCHANGE)
        self.start_consumer()

    def on_queue_to_bound_ok(self, method_frame):
        log.info(u'MQ: Queue %s bound to exchange %s.', config.MQ_TO_LISTENER, config.MQ_EXCHANGE)

    # ------------------------ Consumers ------------------------

    def stop_consumer(self):
        if self.channel:
            log.info(u'MQ: Sending RPC Cancel.')
            self.channel.basic_cancel(consumer_tag=self.consumer)

    def start_consumer(self):
        log.info("MQ: Starting consumer for queue %s", config.MQ_FROM_LISTENER)
        self.consumer = self.channel.basic_consume(self.on_message, config.MQ_FROM_LISTENER)

    def on_message(self, unused_channel, basic_deliver, properties, body):
        log.info(u"MQ: Queue %s => %s", config.MQ_FROM_LISTENER, body)
        try:
            data = json.loads(body)
        except ValueError:
            self.channel.basic_nack(basic_deliver.delivery_tag, requeue=False)
            log.warning(u"MQ: NACK %s", basic_deliver.delivery_tag)
            return

        if self._on_message_handler:
            try:
                self._on_message_handler(data)
                self.channel.basic_ack(basic_deliver.delivery_tag)
                log.info(u"MQ: ACK %s", basic_deliver.delivery_tag)
            except Exception as e:
                self.channel.basic_nack(basic_deliver.delivery_tag, requeue=False)
                log.error(u"MQ: NACK %s", basic_deliver.delivery_tag, exc_info=e)
        else:
            self.channel.basic_ack(basic_deliver.delivery_tag)

    # ------------------------ Messaging ------------------------

    def publish(self, data):
        log.info(u"MQ: Queue %s <= %s", config.MQ_TO_LISTENER, data)
        self.channel.basic_publish(
            exchange=config.MQ_EXCHANGE,
            routing_key=config.MQ_TO_LISTENER,
            body=json.dumps(data),
            properties=pika.spec.BasicProperties(
                content_type="application/json",
                delivery_mode=2))
