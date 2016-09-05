# -*- coding: utf-8 -*-

import logging

import arrow
import bleach
from sqlalchemy import func, and_
from sqlalchemy.orm.exc import NoResultFound

from basehandler import BaseHandler, is_authenticated, validate_message_schema
from aetherguild.listener_service.schemas import get_boards_request, get_threads_request, get_posts_request,\
    get_post_request, insert_post_request, insert_thread_request, update_post_request, update_thread_request
from aetherguild.listener_service.tables import ForumBoard, ForumSection, ForumPost, ForumThread,\
    ForumLastRead, ForumPostEdit, User
from aetherguild.listener_service.user_session import LEVEL_ADMIN

log = logging.getLogger(__name__)


class ForumHandler(BaseHandler):
    @validate_message_schema(get_boards_request)
    def get_boards(self, track_route, message):
        section_id = message['data'].get('section', None)

        # Get boards that have acceptable user level. If section was requested, add it as a restriction to the query.
        boards = self.db.query(ForumBoard)\
            .filter(ForumBoard.req_level <= self.session.get_level(), ForumBoard.deleted == False)
        if section_id:
            boards = boards.filter(ForumBoard.section == section_id)

        out = []
        for board in boards:
            out.append(board.serialize())
        self.send_message({'boards': out})

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

    @validate_message_schema(get_threads_request)
    def get_threads(self, track_route, message):
        start = message['data'].get('start', None)
        count = message['data'].get('count', None)
        board_id = message['data']['board']

        # Check if user has rights to the board. Fake out 404 if not.
        board = self._get_board(board_id=board_id)
        print(board.serialize())
        if not board or not self._has_rights_to_board(board):
            self.send_error(404, "Board not Found")
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

        self.send_message({
            'board': board.serialize(),
            'threads': thread_list,
            'users': user_list
        })

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

    def _get_post(self, post_id=None):
        if post_id:
            return ForumPost.get_one_or_none(self.db, id=post_id, deleted=False)
        return None

    @validate_message_schema(get_posts_request)
    def get_posts(self, track_route, message):
        start = message['data'].get('start', None)
        count = message['data'].get('count', None)
        thread_id = message['data']['thread']

        # Make sure thread exists first
        thread = self._get_thread(thread_id=thread_id)
        if not thread:
            self.send_error(404, "Thread not Found")
            return

        # Check if user has rights to the board. Fake out 404 if not.
        board = self._get_board(board_id=thread.board)
        if not board or not self._has_rights_to_board(board):
            self.send_error(404, "Thread not Found")
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

        self.send_message({
            'board': board.serialize(),
            'thread': thread.serialize(),
            'posts': post_list,
            'users': user_list
        })

    @validate_message_schema(get_post_request)
    def get_post(self, track_route, message):
        post_id = message['data']['post']

        # Check if post exists
        post = self._get_post(post_id=post_id)
        if not post:
            self.send_error(404, "Post not Found")
            return

        # Get thread for later usage
        thread = self._get_thread(thread_id=post.thread)
        if not thread:
            self.send_error(404, "Post not Found")
            return

        # Check if user has rights to the board. Fake out 404 if not.
        board = self._get_board(board_id=thread.board)
        if not board or not self._has_rights_to_board(board):
            self.send_error(404, "Post not Found")
            return

        # Append post owner to the user list that is returned with the response
        user_list = {
            post.user: User.get_one(self.db, id=post.user).serialize()
        }

        # Serialize post data
        post_data = post.serialize()

        # Fetch edits for the post
        post_data['edits'] = []
        for edit in ForumPostEdit.get_many(self.db, post=post.id):
            if edit.user not in user_list:
                user_list[edit.user] = User.get_one(self.db, id=edit.user).serialize()
            post_data['edits'].append(edit.serialize())

        # Send post data
        self.send_message({
            'board': board.serialize(),
            'thread': thread.serialize(),
            'post': post_data,
            'users': user_list
        })

    @is_authenticated
    @validate_message_schema(update_post_request)
    def update_post(self, track_route, message):
        pass

    @is_authenticated
    @validate_message_schema(insert_post_request)
    def insert_post(self, track_route, message):
        pass

    @is_authenticated
    @validate_message_schema(update_thread_request)
    def update_thread(self, track_route, message):
        pass

    @is_authenticated
    @validate_message_schema(insert_thread_request)
    def insert_thread(self, track_route, message):
        pass

    @is_authenticated
    def upsert_post(self, track_route, message):
        post_data = message['data']['post']
        edit_data = message['data'].get('edit', {})
        post_id = post_data.get('id')
        thread_id = post_data.get('thread')
        message = post_data.get('message')
        edit_message = edit_data.get('message')

        # Validate post message length (if any)
        if message:
            message = bleach.clean(message)
            if len(message) == 0:
                self.send_error(400, "Message must not be empty")
                return

        # Validate edit message length (if any)
        if edit_message:
            edit_message = bleach.clean(edit_message)
            if len(edit_message) > 256:
                self.send_error(400, "Edit Message must less than 256 characters long")
                return

        # Must supply either post_id or thread_id
        if not thread_id and not post_id:
            self.send_error(400, "Must supply either board id or thread id")
            return

        # Find the thread
        if post_id:
            thread = self._get_thread(post_id=post_id)
        else:
            thread = self._get_thread(thread_id=thread_id)

        # Check if the thread exists
        if not thread:
            self.send_error(404, "Thread not Found")
            return

        # Fetch board and check if we have rights to upsert to it. Also, we need board ref later
        board = self._get_board(board_id=thread.board)
        if not board or not self._has_rights_to_board(board=board):
            self.send_error(404, "Thread not Found")
            return

        # Create a new post or get an old one, depending on whether we are updating or inserting
        if post_id:
            try:
                post = ForumPost.get_one(self.db, id=post_id, user=self.session.user.id, deleted=False)
                post.message = message or post.message
                if self.session.has_level(LEVEL_ADMIN):
                    post.thread = thread_id or post.thread
            except NoResultFound:
                self.send_error(404, "Post not found")
                return
        else:
            post = ForumPost()
            post.user = self.session.user
            post.thread = thread_id
            post.message = message

        # Set message
        self.db.add(post)

        # If this is an edit, add a message
        if post_id:
            edit = ForumPostEdit()
            edit.user = self.session.user
            edit.post = post.id
            edit.message = edit_message
            self.db.add(edit)

        # Notify the sender user about success; also broadcast notification to everyone else with sufficient privileges
        self.send_message({'post_id': post.id})
        self.broadcast_message({'post_id': post.id}, avoid_self=True, req_level=board.req_level)

    @is_authenticated
    def upsert_thread(self, track_route, message):
        thread_data = message['data']['thread']
        thread_id = thread_data.get('id')
        board_id = thread_data.get('board')
        title = thread_data.get('title')
        sticky = thread_data.get('sticky')
        closed = thread_data.get('closed')

        # Validate title length
        if title:
            title = bleach.clean(title)
            if len(title) < 4 or len(title) > 64:
                self.send_error(400, "Thread title must be between 4 and 64 characters long")
                return

        # Must supply either board_id or thread_id
        if not thread_id and not board_id:
            self.send_error(400, "Must supply either board id or thread id")
            return

        # Get the board ref
        if thread_id:
            current_board = self._get_board(thread_id=thread_id)
        else:
            current_board = self._get_board(board_id=board_id)

        # Make sure user can access the board
        if not current_board or not self._has_rights_to_board(board=current_board):
            self.send_error(404, "Board not Found")
            return

        # Create a new post or get an old one, depending on whether we are updating or inserting
        if thread_id:
            try:
                thread = ForumThread.get_one(self.db, id=thread_id, user=self.session.user.id, deleted=False)
                if self.session.has_level(LEVEL_ADMIN):
                    thread.board = board_id or thread.board
                thread.title = title or thread.title
                thread.sticky = sticky or thread.sticky
                thread.closed = closed or thread.closed
            except NoResultFound:
                self.send_error(404, "Thread not found")
                return
        else:
            thread = ForumThread()
            thread.user = self.session.user
            thread.board = board_id
            thread.title = title
            thread.sticky = sticky or False
            thread.closed = closed or False

        self.db.add(thread)

        # Notify the sender user about success; also broadcast notification to everyone else with sufficient privileges
        self.send_message({'thread_id': thread.id})
        self.broadcast_message({'thread_id': thread.id}, avoid_self=True, req_level=board.req_level)

    def _get_board(self, board_id=None, thread_id=None, post_id=None):
        if post_id and not thread_id and not board_id:
            post = self._get_post(post_id=post_id)
            thread_id = post.thread if post else None
        if thread_id and not board_id:
            thread = self._get_thread(thread_id=thread_id)
            board_id = thread.board if thread else None
        if board_id:
            return ForumBoard.get_one_or_none(self.db, id=board_id, deleted=False)
        return None

    def _get_thread(self, thread_id=None, post_id=None):
        if post_id and not thread_id:
            post = self._get_post(post_id=post_id)
            thread_id = post.thread if post else None
        if thread_id:
            return ForumThread.get_one_or_none(self.db, id=thread_id, deleted=False)
        return None

    def _has_rights_to_board(self, board=None):
        return board and board.deleted is False and board.req_level <= self.session.get_level()

    def get_routes(self):
        return {
            'get_sections': self.get_sections,
            'get_boards': self.get_boards,
            'get_combined_boards': self.get_combined_boards,
            'get_threads': self.get_threads,
            'get_posts': self.get_posts,
            'get_post': self.get_post,
            'upsert_post': self.upsert_post,
            'upsert_thread': self.upsert_thread,
            'update_thread': self.update_thread,
            'insert_thread': self.insert_thread,
            'update_post': self.update_post,
            'insert_post': self.insert_post
        }
