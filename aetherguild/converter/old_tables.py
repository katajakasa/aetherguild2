# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, Binary
from sqlalchemy.ext.declarative import declarative_base

from aetherguild.listener_service.tables import ModelHelperMixin


Base = declarative_base()


class User(Base, ModelHelperMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(32))
    password = Column(Binary(32))
    alias = Column(String(32))
    level = Column(Integer)
    active = Column(Integer)
    registered = Column(DateTime)
    lastcontact = Column(DateTime)
    lastlogoffpoint = Column(DateTime)
    spambot = Column(Boolean)


class OldUser(Base, ModelHelperMixin):
    __tablename__ = "old_users"
    uid = Column(Integer, primary_key=True)
    password = Column(String(40))
    salt = Column(String(12))


class ForumSection(Base, ModelHelperMixin):
    __tablename__ = "forum_sections"
    id = Column(Integer, primary_key=True)
    title = Column(String(64))
    sort_index = Column(Integer)


class ForumBoard(Base, ModelHelperMixin):
    __tablename__ = "forum_boards"
    id = Column(Integer, primary_key=True)
    sid = Column(ForeignKey('forum_sections.id'))
    title = Column(String(64))
    description = Column(String(256))
    min_read_level = Column(Integer)
    min_write_level = Column(Integer)
    sort_index = Column(Integer)


class ForumThread(Base, ModelHelperMixin):
    __tablename__ = "forum_threads"
    id = Column(Integer, primary_key=True)
    bid = Column(ForeignKey('forum_boards.id'))
    uid = Column(ForeignKey('user.id'))
    title = Column(String(64))
    post_time = Column(DateTime)
    views = Column(Integer)
    sticky = Column(Boolean)
    closed = Column(Boolean)


class ForumPost(Base, ModelHelperMixin):
    __tablename__ = "forum_posts"
    id = Column(Integer, primary_key=True)
    tid = Column(ForeignKey('forum_threads.id'))
    uid = Column(ForeignKey('user.id'))
    message = Column(Text)
    post_time = Column(DateTime)
    ip = Column(String(15))


class NewsModel(Base, ModelHelperMixin):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    header = Column(String(64))
    message = Column(Text)
    time = Column(DateTime)
