# -*- coding: utf-8 -*-

import logging
import signal
from logging.config import dictConfig

from aetherguild import config
from aetherguild.listener_service.consumer import Consumer
from aetherguild.listener_service.mq_connection import MQConnection
from aetherguild.listener_service.db_connection import DBConnection


if __name__ == '__main__':
    # Set up the global log
    dictConfig(config.LOGGING)
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
    except:
        log.exception("Error while running MQ listener")
    consumer.close()

    mq_connection.close()
    db_connection.close()

    # All done. Close.
    log.info(u"All done. Shutdown.")
