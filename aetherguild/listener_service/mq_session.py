# -*- coding: utf-8 -*-

import logging

log = logging.getLogger(__name__)


class MQSession(object):
    def __init__(self, mq_connection):
        self.mq_connection = mq_connection
        self.is_transaction = False
        self.messages = []

    def begin(self):
        """
        Begin MQ transaction
        """
        self.is_transaction = True
        self.messages = []

    def commit(self):
        """
        Commit MQ transaction
        """
        self._publish_tx_queue()
        self.messages = []
        self.is_transaction = False

    def rollback(self):
        """
        Rollback MQ transaction
        """
        self.messages = []
        self.is_transaction = False

    def _publish_tx_queue(self):
        """
        Publish all messages in transaction queue
        """
        for message in self.messages:
            self.mq_connection.publish(message)

    def publish(self, message, connection_id=None, broadcast=False, avoid_self=False, is_control=False, req_level=0):
        """ Publish a message to the outgoing queue

        :param message: Message to be sent to the client
        :param connection_id: ID for this connection (should match ID on socket handler)
        :param broadcast: Whether this packet should be broadcast to all listening clients
        :param avoid_self: When broadcasting, only broadcast to *other* clients
        :param is_control: Whether this packet is a control packet. If True, body is considered internal data.
        """
        data = {
            'head': {
                'connection_id': connection_id,
                'avoid_self': avoid_self,
                'broadcast': broadcast,
                'is_control': is_control,
                'req_level': req_level
            },
            'body': message
        }
        if self.is_transaction:
            self.messages.append(data)
        else:
            self.mq_connection.publish(data)

    def close(self):
        self.messages = []
