# -*- coding: utf-8 -*-

from datetime import datetime
import arrow
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ModelHelperMixin(object):
    @classmethod
    def get_one(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs).one()

    @classmethod
    def get_one_or_none(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs).one_or_none()

    @classmethod
    def get_many(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs).all()

    @classmethod
    def delete(cls, session, **kwargs):
        session.query(cls).filter_by(**kwargs).delete()


class ModelFormatMixin(object):
    mysql_engine = 'InnoDB',
    mysql_charset = 'utf8mb4'


class User(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    nickname = Column(String(32), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_contact = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    def serialize(self, include_username=False, include_deleted=False):
        out = {
            'id': self.id,
            'nickname': self.nickname,
            'level': self.level,
            'created_at': arrow.get(self.created_at).isoformat(),
            'last_contact': arrow.get(self.last_contact).isoformat()
        }
        if include_username:
            out['username'] = self.username
        if include_deleted:
            out['deleted'] = self.deleted
        return out


class Session(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True)
    user = Column(ForeignKey('user.id'), nullable=False)
    session_key = Column(String(32), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    activity_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

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
    nickname = Column(String(32), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

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
    title = Column(String(64), nullable=False)
    sort_index = Column(Integer, default=0, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'sort_index': self.sort_index
        }


class ForumBoard(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "forum_board"
    id = Column(Integer, primary_key=True)
    section = Column(ForeignKey('forum_section.id'), nullable=False)
    title = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    req_level = Column(Integer, default=0, nullable=False)
    sort_index = Column(Integer, default=0, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'section': self.section,
            'title': self.title,
            'description': self.description,
            'req_level': self.req_level,
            'sort_index': self.sort_index
        }


class ForumThread(Base, ModelHelperMixin, ModelFormatMixin):
    __tablename__ = "forum_thread"
    id = Column(Integer, primary_key=True)
    board = Column(ForeignKey('forum_board.id'), nullable=False)
    user = Column(ForeignKey('user.id'), nullable=False)
    title = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    views = Column(Integer, default=0, nullable=False)
    sticky = Column(Boolean, default=False, nullable=False)
    closed = Column(Boolean, default=False, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

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
    thread = Column(ForeignKey('forum_thread.id'), nullable=False)
    user = Column(ForeignKey('user.id'), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

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
    post = Column(ForeignKey('forum_post.id'), nullable=False)
    user = Column(ForeignKey('user.id'), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

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
    thread = Column(ForeignKey('forum_thread.id'), nullable=False)
    user = Column(ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    UniqueConstraint('thread', 'user', name='unique_thread_user_constraint')

    def serialize(self):
        return {
            'id': self.id,
            'thread': self.thread,
            'user': self.user,
            'created_at': arrow.get(self.created_at).isoformat()
        }
