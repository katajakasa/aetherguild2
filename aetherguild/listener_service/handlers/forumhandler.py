# -*- coding: utf-8 -*-

import logging

import arrow
import bleach
from sqlalchemy import func, and_
from sqlalchemy.orm.exc import NoResultFound

from basehandler import BaseHandler, is_authenticated, has_level, validate_message_schema, ErrorList
from aetherguild.listener_service.schemas import get_boards_request, get_threads_request, get_posts_request,\
    get_post_request, insert_post_request, insert_thread_request, update_post_request, update_thread_request,\
    delete_post_request, delete_thread_request, delete_board_request, delete_section_request, insert_section_request,\
    insert_board_request, update_section_request, update_board_request
from aetherguild.listener_service.tables import ForumBoard, ForumSection, ForumPost, ForumThread,\
    ForumLastRead, ForumPostEdit, User
from utils import validate_str_length, validate_required_field
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

        # Base query
        base_query = self.db.query(ForumThread) \
            .filter(ForumThread.board == board_id, ForumThread.deleted == False)

        # Get threads + thread count, apply limit and offset if required in args
        threads_count = base_query.count()
        threads = base_query.order_by(ForumThread.created_at.desc())
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
            'threads_count': threads_count,
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

        base_query = self.db.query(ForumPost)\
            .filter(ForumPost.thread == thread_id, ForumPost.deleted == False)

        # Get posts, apply limit and offset if required in args
        posts_count = base_query.count()
        posts = base_query.order_by(ForumPost.created_at.asc())
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
            'posts_count': posts_count,
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
        post_id = message['data'].get('post')
        msg = bleach.clean(message['data'].get('message'))
        edit_msg = bleach.clean(message['data'].get('edit_message', ''))
        errors_list = ErrorList()

        # Get the post and make sure it belongs to the current user
        post = self._get_post(post_id=post_id)
        if not post or post.user != self.session.user.id:
            self.send_error(404, "Post not found")
            return

        # Get the thread
        thread = self._get_thread(thread_id=post.thread)
        if not thread:
            self.send_error(404, "Post not found")
            return

        # Make sure user can access the board to which the thread belongs
        board = self._get_board(board_id=thread.board)
        if not board or not self._has_rights_to_board(board=board):
            self.send_error(404, "Post not found")
            return

        # Validate fields
        validate_required_field('message', msg, errors_list)
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        # Update post
        post.message = msg
        self.db.add(post)

        # If edit message is given, save it
        edit = None
        if edit_msg:
            edit = ForumPostEdit()
            edit.message = edit_msg
            edit.post = post.id
            edit.user = self.session.user.id
            self.db.add(edit)

        # Notify the sender user about success; also broadcast notification to everyone else with sufficient privileges
        out_data = {
            'thread': thread.serialize(),
            'post': post.serialize(),
            'user': self.session.user.serialize()
        }
        if edit:
            out_data['edit'] = edit.serialize()
        self.send_message(out_data)

    @is_authenticated
    @validate_message_schema(insert_post_request)
    def insert_post(self, track_route, message):
        thread_id = message['data'].get('thread')
        msg = bleach.clean(message['data'].get('message'))
        errors_list = ErrorList()

        # Get the thread
        thread = self._get_thread(thread_id=thread_id)
        if not thread:
            self.send_error(404, "Thread not found")
            return

        # Make sure user can access the board to which the thread belongs
        board = self._get_board(board_id=thread.board)
        if not board or not self._has_rights_to_board(board=board):
            self.send_error(404, "Thread not found")
            return

        # Validate fields
        validate_required_field('message', msg, errors_list)
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        # Create a new post for the thread
        post = ForumPost()
        post.message = msg
        post.user = self.session.user.id
        post.thread = thread.id
        self.db.add(post)
        self.db.flush()

        # Notify the sender user about success; also broadcast notification to everyone else with sufficient privileges
        self.send_message({
            'thread': thread.serialize(),
            'post': post.serialize(),
            'user': self.session.user.serialize()
        })
        self.broadcast_message({
            'thread': thread.serialize(),
            'post': post.serialize(),
            'user': self.session.user.serialize()
        }, avoid_self=True, req_level=board.req_level)

    @is_authenticated
    @validate_message_schema(update_thread_request)
    def update_thread(self, track_route, message):
        thread_id = message['data'].get('thread')
        title = message['data'].get('title')
        closed = message['data'].get('closed')
        sticky = message['data'].get('sticky')
        errors_list = ErrorList()

        # Get the thread
        thread = self._get_thread(thread_id=thread_id)
        if not thread or thread.user != self.session.user.id:
            self.send_error(404, "Thread not found")
            return

        # Make sure user can access the board to which the thread belongs
        board = self._get_board(board_id=thread.board)
        if not board or not self._has_rights_to_board(board=board):
            self.send_error(404, "Thread not found")
            return

        # Validate fields
        if title:
            validate_required_field('title', title, errors_list)

        # If errors, stop here
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        # Update fields as necessary
        if sticky:
            thread.sticky = sticky
        if closed:
            thread.closed = closed
        if title:
            thread.title = title
        self.db.add(thread)
        self.db.flush()

        # Notify the sender user about success
        self.send_message({
            'thread': thread.serialize(),
            'user': self.session.user.serialize()
        })

    @is_authenticated
    @validate_message_schema(insert_thread_request)
    def insert_thread(self, track_route, message):
        board_id = message['data'].get('board')
        title = bleach.clean(message['data'].get('title'))
        msg = bleach.clean(message['data'].get('message'))
        sticky = message['data'].get('sticky')
        closed = message['data'].get('closed')
        errors_list = ErrorList()

        # Make sure user can access the board
        board = self._get_board(board_id=board_id)
        if not board or not self._has_rights_to_board(board=board):
            self.send_error(404, "Board not found")
            return

        # Validate fields
        validate_required_field('message', msg, errors_list)
        validate_str_length('title', title, errors_list, 4, 64)
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        # Create a new thread
        thread = ForumThread()
        thread.user = self.session.user.id
        thread.board = board.id
        thread.title = title
        thread.sticky = sticky
        thread.closed = closed
        self.db.add(thread)
        self.db.flush()

        # Create a new post for the thread
        post = ForumPost()
        post.message = msg
        post.user = self.session.user.id
        post.thread = thread.id
        self.db.add(post)
        self.db.flush()

        # Notify the sender user about success; also broadcast notification to everyone else with sufficient privileges
        self.send_message({
            'thread': thread.serialize(),
            'post': post.serialize(),
            'user': self.session.user.serialize()
        })
        self.broadcast_message({
            'thread': thread.serialize(),
            'post': post.serialize(),
            'user': self.session.user.serialize()
        }, avoid_self=True, req_level=board.req_level)

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_post_request)
    def delete_post(self, track_route, message):
        pass

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_thread_request)
    def delete_thread(self, track_route, message):
        pass

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_board_request)
    def delete_board(self, track_route, message):
        pass

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_section_request)
    def delete_section(self, track_route, message):
        pass

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(insert_board_request)
    def insert_board(self, track_route, message):
        pass

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(update_board_request)
    def update_board(self, track_route, message):
        pass

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(insert_section_request)
    def insert_section(self, track_route, message):
        pass

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(update_section_request)
    def update_section(self, track_route, message):
        pass

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

    def _get_post(self, post_id=None):
        if post_id:
            return ForumPost.get_one_or_none(self.db, id=post_id, deleted=False)
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
            'update_thread': self.update_thread,
            'insert_thread': self.insert_thread,
            'delete_thread': self.delete_thread,
            'update_post': self.update_post,
            'insert_post': self.insert_post,
            'delete_post': self.delete_post,
            'insert_section': self.insert_section,
            'update_section': self.update_section,
            'delete_section': self.delete_section,
            'insert_board': self.insert_board,
            'update_board': self.update_board,
            'delete_board': self.delete_board
        }
