# -*- coding: utf-8 -*-

import logging
import sys

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

    db_session = sessionmaker()
    engine = create_engine(config.DATABASE_CONFIG, pool_recycle=3600)
    db_session.configure(bind=engine)

    consumer = Consumer(db_session)
    try:
        consumer.handle()
    except KeyboardInterrupt:
        pass
    consumer.close()

    # All done. Close.

