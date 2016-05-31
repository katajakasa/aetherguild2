# -*- coding: utf-8 -*-

import logging
import pika

log = logging.getLogger(__name__)


class Consumer(object):
    def __init__(self, url):
        self.connection = pika.BlockingConnection(pika.URLParameters(url))
        self.channel = self.connection.channel()

    def handle(self):
        """ Handle stuff from queue """
        pass

    def close(self):
        self.channel.close()
        self.connection.close()
