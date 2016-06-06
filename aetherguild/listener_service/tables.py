# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class User(object):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True)
    password = Column(String(256))
    alias = Column(String(32))
    level = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_contact = Column(DateTime, default=datetime.utcnow)


@as_declarative()
class Session(object):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True)
    session_key = Column(String(32), unique=True)
    created = Column(DateTime, default=datetime.utcnow)
    user = Column(ForeignKey('user.id'))


@as_declarative()
class NewsItem(object):
    __tablename__ = "newsitem"
    id = Column(Integer, primary_key=True)
    alias = Column(String(32))
    post = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


@as_declarative()
class ForumSection(object):
    __tablename__ = "forum_section"
    id = Column(Integer, primary_key=True)
    title = Column(String(64))
    sort_index = Column(Integer, default=0)


@as_declarative()
class ForumBoard(object):
    __tablename__ = "forum_board"
    id = Column(Integer, primary_key=True)
    section = Column(ForeignKey('forum_section.id'))
    title = Column(String(64))
    description = Column(Text)
    min_read_level = Column(Integer)
    min_write_level = Column(Integer)
    sort_index = Column(Integer, default=0)


@as_declarative()
class ForumThread(object):
    __tablename__ = "forum_thread"
    id = Column(Integer, primary_key=True)
    board = Column(ForeignKey('forum_board.id'))
    user = Column(ForeignKey('user.id'))
    title = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    sticky = Column(Boolean, default=False)
    closed = Column(Boolean, default=False)


@as_declarative()
class ForumPost(object):
    __tablename__ = "forum_post"
    id = Column(Integer, primary_key=True)
    thread = Column(ForeignKey('forum_thread.id'))
    user = Column(ForeignKey('user.id'))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


@as_declarative()
class ForumPostEdit(object):
    __tablename__ = "forum_edit"
    id = Column(Integer, primary_key=True)
    post = Column(ForeignKey('forum_post.id'))
    user = Column(ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    message = Column(Text)


@as_declarative()
class ForumLastRead(object):
    __tablename__ = "forum_last_read"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    thread = Column(ForeignKey('forum_thread.id'))
    user = Column(ForeignKey('user.id'))
    UniqueConstraint('thread', 'user', name='unique_thread_user_constraint')
