# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, Binary
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(32))
    password = Column(Binary(32))
    alias = Column(String(32))
    level = Column(Integer)
    active = Column(Boolean)
    registered = Column(DateTime)
    lastcontact = Column(DateTime)
    lastlogoffpoint = Column(DateTime)
    spambot = Column(Boolean)

