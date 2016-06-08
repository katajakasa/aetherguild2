# -*- coding: utf-8 -*-

from datetime import datetime
import arrow
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ModelHelperMixin(object):
    @classmethod
    def get_one(cls, session, **kwargs):
        session.query(cls).filter_by(**kwargs).one()


class ModelFormatMixin(object):
    mysql_engine = 'InnoDB',
    mysql_charset = 'utf8mb4'


class User(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True)
    password = Column(String(256))
    alias = Column(String(32))
    level = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_contact = Column(DateTime(timezone=True), default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'alias': self.alias,
            'level': self.level,
            'active': self.active,
            'created_at': arrow.get(self.created_at).isoformat(),
            'last_contact': arrow.get(self.last_contact).isoformat()
        }


class Session(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True)
    session_key = Column(String(32), unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    activity_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user = Column(ForeignKey('user.id'))

    def serialize(self):
        return {
            'session_key': self.session_key,
            'created_at': arrow.get(self.created_at).isoformat(),
            'activity_at': arrow.get(self.activity_at).isoformat(),
            'user': self.user
        }


class NewsItem(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "news_item"
    id = Column(Integer, primary_key=True)
    alias = Column(String(32))
    post = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'alias': self.alias,
            'post': self.post,
            'created_at': arrow.get(self.created_at).isoformat()
        }


class ForumSection(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "forum_section"
    id = Column(Integer, primary_key=True)
    title = Column(String(64))
    sort_index = Column(Integer, default=0)

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'sort_index': self.sort_index
        }


class ForumBoard(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "forum_board"
    id = Column(Integer, primary_key=True)
    section = Column(ForeignKey('forum_section.id'))
    title = Column(String(64))
    description = Column(Text)
    min_read_level = Column(Integer)
    min_write_level = Column(Integer)
    sort_index = Column(Integer, default=0)

    def serialize(self):
        return {
            'id': self.id,
            'section': self.section,
            'title': self.title,
            'description': self.description,
            'min_read_level': self.min_read_level,
            'min_write_level': self.min_write_level,
            'sort_index': self.sort_index
        }


class ForumThread(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "forum_thread"
    id = Column(Integer, primary_key=True)
    board = Column(ForeignKey('forum_board.id'))
    user = Column(ForeignKey('user.id'))
    title = Column(String(64))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    views = Column(Integer, default=0)
    sticky = Column(Boolean, default=False)
    closed = Column(Boolean, default=False)

    def serialize(self):
        return {
            'id': self.id,
            'board': self.board,
            'user': self.user,
            'title': self.title,
            'created_at': arrow.get(self.created_at).isoformat(),
            'views': self.views,
            'sticky': self.sticky,
            'closed': self.closed
        }


class ForumPost(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "forum_post"
    id = Column(Integer, primary_key=True)
    thread = Column(ForeignKey('forum_thread.id'))
    user = Column(ForeignKey('user.id'))
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'thread': self.thread,
            'user': self.user,
            'message': self.message,
            'created_at': arrow.get(self.created_at).isoformat()
        }


class ForumPostEdit(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "forum_edit"
    id = Column(Integer, primary_key=True)
    post = Column(ForeignKey('forum_post.id'))
    user = Column(ForeignKey('user.id'))
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'post': self.post,
            'user': self.user,
            'message': self.message,
            'created_at': arrow.get(self.created_at).isoformat()
        }


class ForumLastRead(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "forum_last_read"
    id = Column(Integer, primary_key=True)
    thread = Column(ForeignKey('forum_thread.id'))
    user = Column(ForeignKey('user.id'))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    UniqueConstraint('thread', 'user', name='unique_thread_user_constraint')

    def serialize(self):
        return {
            'id': self.id,
            'thread': self.thread,
            'user': self.user,
            'created_at': arrow.get(self.created_at).isoformat()
        }
