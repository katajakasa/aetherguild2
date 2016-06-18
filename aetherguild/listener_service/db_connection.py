# -*- coding: utf-8 -*-

import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from aetherguild import config

log = logging.getLogger(__name__)


class DBConnection(object):
    def __init__(self):
        self.connection = None
        self.engine = None
        self._is_closed = True

    def connect(self):
        if self.engine:
            self.engine.connect()
        else:
            self.engine = create_engine(config.DATABASE_CONFIG, pool_recycle=3600)
        self.connection = sessionmaker(bind=self.engine, autoflush=True)
        self._is_closed = False
        log.info("DB: Connected")

    def is_closed(self):
        return self._is_closed

    def invalidate(self):
        self.engine.dispose()
        self._is_closed = True

    def get_session(self):
        return self.connection()

    def close(self):
        self.connection.close_all()
        self.engine.dispose()
        self._is_closed = True
        log.info("DB: Connection closed")
