# -*- coding: utf-8 -*-

import os
import ujson

import bleach
import arrow
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Boolean, UniqueConstraint, Binary, Index, Unicode
from sqlalchemy.ext.declarative import declarative_base

from aetherguild.common.utils import generate_random_key
from aetherguild import config

Base = declarative_base()


def utc_now():
    return arrow.utcnow().datetime


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


class OldUser(Base, ModelHelperMixin):
    __tablename__ = "old_user"
    id = Column(Integer, primary_key=True)
    user = Column(ForeignKey('new_user.id'), nullable=False)
    password = Column(Binary(32), nullable=False)


class User(Base, ModelHelperMixin):
    __tablename__ = "new_user"
    id = Column(Integer, primary_key=True)
    avatar = Column(ForeignKey('file.key'), default=None, nullable=True)
    username = Column(Unicode(64), unique=True, nullable=False)
    password = Column(Unicode(256), nullable=True, default=None)
    nickname = Column(Unicode(64), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_contact = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    profile_data = Column(Text, default=u'{}', nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    def serialize(self, include_username=False, include_deleted=False, include_profile=False):
        out = {
            'id': self.id,
            'avatar': File.format_public_path(self.avatar),
            'nickname': self.nickname,
            'level': self.level,
            'created_at': arrow.get(self.created_at).isoformat(),
            'last_contact': arrow.get(self.last_contact).isoformat()
        }
        if include_profile:
            out['profile_data'] = ujson.loads(self.profile_data)
        if include_username:
            out['username'] = bleach.clean(self.username)
        if include_deleted:
            out['deleted'] = self.deleted
        return out


class Session(Base, ModelHelperMixin):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True)
    user = Column(ForeignKey('new_user.id'), nullable=False)
    session_key = Column(Unicode(64), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    activity_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def serialize(self):
        return {
            'session_key': self.session_key,
            'created_at': arrow.get(self.created_at).isoformat(),
            'activity_at': arrow.get(self.activity_at).isoformat(),
            'user': self.user
        }


class File(Base, ModelHelperMixin):
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    key = Column(Unicode(32), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def __init__(self, ext, *args, **kwargs):
        self.key = u"{}.{}".format(generate_random_key()[:16], ext)
        super(File, self).__init__(*args, **kwargs)

    @staticmethod
    def format_local_path(filename):
        if not filename:
            return None
        return os.path.join(config.UPLOAD_LOCAL_PATH, filename)

    @staticmethod
    def format_public_path(filename):
        if not filename:
            return None
        return u"{}{}".format(config.UPLOAD_PUBLIC_PATH, filename)

    def get_local_path(self):
        return self.format_local_path(self.key)

    def get_public_path(self):
        return self.format_public_path(self.key)

    def serialize(self):
        return {
            'id': self.id,
            'key': self.key,
            'created_at': arrow.get(self.created_at).isoformat()
        }


class NewsItem(Base, ModelHelperMixin):
    __tablename__ = "news_item"
    id = Column(Integer, primary_key=True)
    nickname = Column(Unicode(64), nullable=False)
    header = Column(Unicode(128), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'nickname': self.nickname,
            'header': self.header,
            'message': self.message,
            'created_at': arrow.get(self.created_at).isoformat()
        }


class ForumSection(Base, ModelHelperMixin):
    __tablename__ = "forum_section"
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(128), nullable=False)
    sort_index = Column(Integer, default=0, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'sort_index': self.sort_index
        }


class ForumBoard(Base, ModelHelperMixin):
    __tablename__ = "forum_board"
    id = Column(Integer, primary_key=True)
    section = Column(ForeignKey('forum_section.id'), nullable=False)
    title = Column(Unicode(128), nullable=False)
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


class ForumThread(Base, ModelHelperMixin):
    __tablename__ = "forum_thread"
    id = Column(Integer, primary_key=True)
    board = Column(ForeignKey('forum_board.id'), nullable=False)
    user = Column(ForeignKey('new_user.id'), nullable=False)
    title = Column(Unicode(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    views = Column(Integer, default=0, nullable=False)
    sticky = Column(Boolean, default=False, nullable=False, index=True)
    closed = Column(Boolean, default=False, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    Index("desc_sort_index", 'sticky', 'updated_at')

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


class ForumPost(Base, ModelHelperMixin):
    __tablename__ = "forum_post"
    id = Column(Integer, primary_key=True)
    thread = Column(ForeignKey('forum_thread.id'), nullable=False)
    user = Column(ForeignKey('new_user.id'), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    deleted = Column(Boolean, default=False, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'thread': self.thread,
            'user': self.user,
            'message': self.message,
            'created_at': arrow.get(self.created_at).isoformat()
        }


class ForumPostEdit(Base, ModelHelperMixin):
    __tablename__ = "forum_edit"
    id = Column(Integer, primary_key=True)
    post = Column(ForeignKey('forum_post.id'), nullable=False)
    user = Column(ForeignKey('new_user.id'), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'post': self.post,
            'user': self.user,
            'message': self.message,
            'created_at': arrow.get(self.created_at).isoformat()
        }


class ForumLastRead(Base, ModelHelperMixin):
    __tablename__ = "forum_last_read"
    id = Column(Integer, primary_key=True)
    thread = Column(ForeignKey('forum_thread.id'), nullable=False)
    user = Column(ForeignKey('new_user.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    UniqueConstraint('thread', 'user', name='unique_thread_user_constraint')

    def serialize(self):
        return {
            'id': self.id,
            'thread': self.thread,
            'user': self.user,
            'created_at': arrow.get(self.created_at).isoformat()
        }
