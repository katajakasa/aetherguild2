# -*- coding: utf-8 -*-

import logging
import sys
import signal

from aetherguild import config
from consumer import Consumer
from mq_connection import MQConnection
from db_connection import DBConnection


if __name__ == '__main__':
    # Find correct log level
    level = {
        0: logging.DEBUG,
        1: logging.INFO,
        2: logging.WARNING,
        3: logging.ERROR,
        4: logging.CRITICAL
    }[config.LOG_LEVEL]

    # Set up the global log
    log_format = '[%(asctime)s] %(message)s'
    log_datefmt = '%d.%m.%Y %I:%M:%S'
    logging.basicConfig(stream=sys.stderr,
                        level=level,
                        format=log_format,
                        datefmt=log_datefmt)
    log = logging.getLogger(__name__)
    log.info("Starting MQ listener")

    # Set up DB connection and connect
    db_connection = DBConnection()
    db_connection.connect()

    # Set up MQ connection and connect
    mq_connection = MQConnection()
    mq_connection.connect()

    # Create a message consumer. This handles message consumption and handling
    consumer = Consumer(db_connection, mq_connection)

    def sig_handler(signal, frame):
        consumer.close()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        consumer.handle()
    except KeyboardInterrupt:
        pass
    consumer.close()

    mq_connection.close()
    db_connection.close()

    # All done. Close.
    log.info(u"All done. Shutdown.")

