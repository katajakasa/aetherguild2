# -*- coding: utf-8 -*-

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aetherguild import config
from consumer import Consumer
import logging

if __name__ == '__main__':
    log = logging.getLogger(__name__)

    session = sessionmaker()
    engine = create_engine(config.DATABASE_CONFIG, pool_recycle=3600)
    session.configure(bind=engine)

    consumer = Consumer(config.MQ_CONFIG)
    consumer.handle()
    consumer.close()

    # All done. Close.

