# -*- coding: utf-8 -*-

import logging
import sys
import signal

from pika.exceptions import ConnectionClosed
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from aetherguild import config
from consumer import Consumer


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

    db_connection = sessionmaker()
    engine = create_engine(config.DATABASE_CONFIG, pool_recycle=3600)
    db_connection.configure(bind=engine)

    consumer = Consumer(db_connection)

    def sig_handler(signal, frame):
        consumer.close()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    consumer.handle()
    consumer.close()

    # All done. Close.

