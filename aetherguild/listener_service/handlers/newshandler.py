# -*- coding: utf-8 -*-

import logging

from sqlalchemy.orm.exc import NoResultFound
import bleach

from aetherguild.listener_service.tables import NewsItem
from aetherguild.listener_service.user_session import LEVEL_ADMIN
from basehandler import BaseHandler, validate_message_schema, has_level, ErrorList
from aetherguild.listener_service.schemas.news import *

log = logging.getLogger(__name__)


class NewsHandler(BaseHandler):
    @has_level(LEVEL_ADMIN)
    @validate_message_schema(get_news_posts)
    def get_news_posts(self, track_route, message):
        start = message['data'].get('start')
        count = message['data'].get('count')

        # Form the query
        query = self.db.query(NewsItem).filter(NewsItem.deleted == False)
        news_count = query.count()
        query = query.order_by(NewsItem.id.desc())
        if start:
            query = query.offset(start)
        if count:
            query = query.limit(count)

        # Serialize objects
        out_list = []
        for post in query:
            out_list.append(post.serialize())

        # Dump out the object list
        self.send_message({
            'news_count': news_count,
            'posts': out_list
        })

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(get_news_post)
    def get_news_post(self, track_route, message):
        post_id = message['data']['post']

        # Find the news post, error out if not found
        try:
            post = NewsItem.get_one(self.db, id=post_id, deleted=False)
        except NoResultFound:
            self.send_error(404, u"News item not found")
            return

        # Serialize and send the news post
        self.send_message({
            'post': post.serialize()
        })

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(insert_news_posts_request)
    def insert_news_post(self, track_route, message):
        msg = bleach.clean(message['data']['message'])
        err_list = ErrorList()

        # Make sure the message has at least some content
        if len(msg) < 1:
            err_list.add_error(u"Please fill in the news text", 'message')

        # Send errors if any
        if err_list.get_list():
            self.send_error(450, err_list)
            return

        # Create the new post
        post = NewsItem()
        post.alias = self.session.user.nickname
        post.post = msg
        self.db.add(post)
        self.db.flush()

        # Send the new post as a response
        self.send_message({
            'post': post.serialize()
        })

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_news_post_request)
    def delete_news_post(self, track_route, message):
        post_id = message['data']['post']

        # Make sure the user exists and get the reference
        try:
            post = NewsItem.get_one(self.db, id=post_id, deleted=False)
        except NoResultFound:
            self.send_error(404, u"News item not found")
            return

        # Set deleted flag
        post.deleted = True
        self.db.add(post)

        # Just send an empty notification
        self.send_message({})

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(update_news_post_request)
    def update_news_post(self, track_route, message):
        post_id = message['data']['post']
        msg = bleach.clean(message['data']['message'])
        err_list = ErrorList()

        # Make sure the message has at least some content
        if len(msg) < 1:
            err_list.add_error(u"Please fill in the news text", 'message')

        # Send errors if any
        if err_list.get_list():
            self.send_error(450, err_list)
            return

        # Find the news post, error out if not found
        try:
            post = NewsItem.get_one(self.db, id=post_id, deleted=False)
        except NoResultFound:
            self.send_error(404, u"News item not found")
            return

        # Update content
        post.post = msg
        self.db.add(post)

        # Serialize and send the news post
        self.send_message({
            'post': post.serialize()
        })

    def get_routes(self):
        return {
            'get_news_posts': self.get_news_posts,
            'get_news_post': self.get_news_post,
            'insert_news_post': self.insert_news_post,
            'delete_news_post': self.delete_news_post,
            'update_news_post': self.update_news_post,
        }
