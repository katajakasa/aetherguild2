# -*- coding: utf-8 -*-

import logging
import arrow
from sqlalchemy import func, and_
from basehandler import BaseHandler
from aetherguild.listener_service.tables import ForumBoard, ForumSection, ForumPost, ForumThread,\
    ForumLastRead, ForumPostEdit, User

log = logging.getLogger(__name__)


class ForumHandler(BaseHandler):
    def get_sections(self, track_route, message):
        # Select sections that have boards with req_level that is smaller or equal to current logged users userlevel
        sections = self.db.query(ForumSection).filter(
            self.db.query(func.count('*').label('count1')).filter(and_(
                ForumBoard.section == ForumSection.id,
                ForumBoard.req_level <= self.session.get_level()
            )).as_scalar() > 0
        )

        # Serialize and dump out
        out = []
        for section in sections:
            out.append(section.serialize())
        self.send_message({'sections': out})

    def get_boards(self, track_route, message):
        data = message.get('data', {})
        section_id = data.get('section', None)

        # Get boards that have acceptable user level. If section was requested, add it as a restriction to the query.
        boards = self.db.query(ForumBoard).filter(ForumBoard.req_level <= self.session.get_level())
        if section_id:
            boards = boards.filter(ForumBoard.section == section_id)

        out = []
        for board in boards:
            out.append(board.serialize())
        self.send_message({'boards': out})

    def get_combined_boards(self, track_route, message):
        # Get allowed sections
        sections = self.db.query(ForumSection).filter(
            self.db.query(func.count('*').label('count1')).filter(and_(
                ForumBoard.section == ForumSection.id,
                ForumBoard.deleted == False,
                ForumBoard.req_level <= self.session.get_level()
            )).as_scalar() > 0
        )

        # Iterate through sections, get boards for them
        out = []
        for section in sections:
            out_section = section.serialize()
            out_section['boards'] = []
            boards = self.db.query(ForumBoard).filter(and_(
                ForumBoard.req_level <= self.session.get_level(),
                ForumBoard.section == section.id
            ))
            for board in boards:
                out_section['boards'].append(board.serialize())
            out.append(out_section)
        self.send_message({'sections': out})

    def get_threads(self, track_route, message):
        start = message['data'].get('start', None)
        count = message['data'].get('count', None)
        board_id = message['data']['board']

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

    def handle(self, track_route, message):
        # If we fail here, it's fine. An exception handler in upwards takes care of the rest.
        cbs = {
            'get_sections': self.get_sections,
            'get_boards': self.get_boards,
            'get_combined_boards': self.get_combined_boards,
            'get_threads': self.get_threads,
            'get_posts': self.get_posts,
        }
        cbs[track_route.pop(0)](track_route, message)
