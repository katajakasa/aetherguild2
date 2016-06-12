# -*- coding: utf-8 -*-

import os
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aetherguild.listener_service.tables import Base


class DatabaseTestHelper(object):
    engine = None
    session = None

    def init_database(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.session = sessionmaker()
        self.session.configure(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def close_database(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
