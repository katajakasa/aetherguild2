# -*- coding: utf-8 -*-

import logging
import arrow
from sqlalchemy import func, and_
from sqlalchemy.orm.exc import NoResultFound
from basehandler import BaseHandler
from aetherguild.listener_service.tables import ForumBoard, ForumSection, ForumPost, ForumThread,\
    ForumLastRead, ForumPostEdit, User

log = logging.getLogger(__name__)


class ForumHandler(BaseHandler):
    def get_sections(self, track_route, message):
        # Select sections that have boards with req_level that is smaller or equal to current logged users userlevel
        sections = self.db.query(ForumSection).filter(and_(
            self.db.query(func.count('*').label('count1')).filter(and_(
                ForumBoard.section == ForumSection.id,
                ForumBoard.deleted == False,
                ForumBoard.req_level <= self.session.get_level(),
            )).as_scalar() > 0,
            ForumSection.deleted == False
        ))

        # Serialize and dump out
        out = []
        for section in sections:
            out.append(section.serialize())
        self.send_message({'sections': out})

    def get_boards(self, track_route, message):
        data = message.get('data', {})
        section_id = data.get('section', None)

        # Get boards that have acceptable user level. If section was requested, add it as a restriction to the query.
        boards = self.db.query(ForumBoard)\
            .filter(ForumBoard.req_level <= self.session.get_level(), ForumBoard.deleted == False)
        if section_id:
            boards = boards.filter(ForumBoard.section == section_id)

        out = []
        for board in boards:
            out.append(board.serialize())
        self.send_message({'boards': out})

    def get_combined_boards(self, track_route, message):
        # Get allowed sections
        sections = self.db.query(ForumSection).filter(and_(
            self.db.query(func.count('*').label('count1')).filter(and_(
                ForumBoard.section == ForumSection.id,
                ForumBoard.deleted == False,
                ForumBoard.req_level <= self.session.get_level()
            )).as_scalar() > 0,
            ForumSection.deleted == False
        ))

        # Iterate through sections, get boards for them
        out = []
        for section in sections:
            out_section = section.serialize()
            out_section['boards'] = []
            boards = self.db.query(ForumBoard).filter(and_(
                ForumBoard.req_level <= self.session.get_level(),
                ForumBoard.section == section.id,
                ForumBoard.deleted == False
            ))
            for board in boards:
                out_section['boards'].append(board.serialize())
            out.append(out_section)
        self.send_message({'sections': out})

    def get_threads(self, track_route, message):
        start = message['data'].get('start', None)
        count = message['data'].get('count', None)
        board_id = message['data']['board']

        # Check if user has rights to the board. Fake out 404 if not.
        board = ForumBoard.get_one_or_none(self.db, id=board_id, deleted=False)
        if not board or not self._has_rights_to_board(board=board):
            self.send_error(404, "Not Found")
            return

        # Get threads, apply limit and offset if required in args
        threads = self.db.query(ForumThread)\
            .filter(ForumThread.board == board_id, ForumThread.deleted == False)\
            .order_by(ForumThread.created_at.desc())
        if start:
            threads = threads.offset(start)
        if count:
            threads = threads.limit(count)

        thread_list = []
        user_list = {}
        for thread in threads:
            # Serialize thread contents
            data = thread.serialize()

            # Add user to the users list if not yet there
            if thread.user not in user_list:
                user_list[thread.user] = User.get_one(self.db, id=thread.user).serialize()

            # Fetch last_read information for this user and thread
            data['last_read'] = None
            if self.session.user:
                last_read = ForumLastRead.get_one_or_none(self.db, thread=thread.id, user=self.session.user.id)
                if last_read:
                    data['last_read'] = arrow.get(last_read.created_at).isoformat()
            thread_list.append(data)
        self.send_message({'threads': thread_list, 'users': user_list})

    def get_posts(self, track_route, message):
        start = message['data'].get('start', None)
        count = message['data'].get('count', None)
        thread_id = message['data']['thread']

        # Check if user has rights to the board. Fake out 404 if not.
        thread = ForumThread.get_one_or_none(self.db, id=thread_id, deleted=False)
        if not thread or not self._has_rights_to_board(thread=thread):
            self.send_error(404, "Not Found")
            return

        # Get posts, apply limit and offset if required in args
        posts = self.db.query(ForumPost)\
            .filter(ForumPost.thread == thread_id, ForumPost.deleted == False)\
            .order_by(ForumPost.created_at.desc())
        if start:
            posts = posts.offset(start)
        if count:
            posts = posts.limit(count)

        post_list = []
        user_list = {}
        for post in posts:
            # Serialize post contents
            data = post.serialize()

            # Add user to a dict if not yet there
            if post.user not in user_list:
                user_list[post.user] = User.get_one(self.db, id=post.user).serialize()

            # Find edits for post
            data['edits'] = []
            for edit in ForumPostEdit.get_many(self.db, post=post.id):
                # Add editor to the userlist also (if not yet there)
                if edit.user not in user_list:
                    user_list[edit.user] = User.get_one(self.db, id=edit.user).serialize()

                # Append the edit as serialized to edits list
                data['edits'].append(edit.serialize())
                post_list.append(data)

        self.send_message({'posts': post_list, 'users': user_list})

    def get_post(self, track_route, message):
        post_id = message['data']['post']

        # Check if user has rights to the board. Fake out 404 if not.
        post = ForumPost.get_one_or_none(self.db, id=post_id, deleted=False)
        if not post or not self._has_rights_to_board(post=post):
            self.send_error(404, "Not Found")
            return

        user_list = {}
        if post.user not in user_list:
            user_list[post.user] = User.get_one(self.db, id=post.user).serialize()

        # Serialize post data
        post_data = post.serialize()

        # Fetch edits for the post
        post_data['edits'] = []
        for edit in ForumPostEdit.get_many(self.db, post=post.id):
            if edit.user not in user_list:
                user_list[edit.user] = User.get_one(self.db, id=edit.user).serialize()
            post_data['edits'].append(edit.serialize())

        # Send post data
        self.send_message({'post': post_data, 'users': user_list})

    def _has_rights_to_board(self, board=None, thread=None, post=None):
        if not board:
            if not thread:
                if not post:
                    return False
                thread = ForumThread.get_one_or_none(self.db, id=post.thread, deleted=False)
            board = ForumBoard.get_one_or_none(self.db, id=thread.board, deleted=False)
        return board and board.deleted is False and board.req_level <= self.session.get_level()

    def handle(self, track_route, message):
        # If we fail here, it's fine. An exception handler in upwards takes care of the rest.
        cbs = {
            'get_sections': self.get_sections,
            'get_boards': self.get_boards,
            'get_combined_boards': self.get_combined_boards,
            'get_threads': self.get_threads,
            'get_posts': self.get_posts,
            'get_post': self.get_post
        }
        cbs[track_route.pop(0)](track_route, message)
