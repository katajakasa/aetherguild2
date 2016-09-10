# -*- coding: utf-8 -*-

import logging

import arrow
import bleach
from sqlalchemy import func, and_
from sqlalchemy.orm.exc import NoResultFound

from basehandler import BaseHandler, is_authenticated, has_level, validate_message_schema, ErrorList
from aetherguild.listener_service.schemas.forum import *
from aetherguild.listener_service.tables import ForumBoard, ForumSection, ForumPost, ForumThread,\
    ForumLastRead, ForumPostEdit, User
from utils import validate_str_length, validate_required_field
from aetherguild.listener_service.user_session import LEVEL_ADMIN

log = logging.getLogger(__name__)


class ForumHandler(BaseHandler):
    def _get_board_extra_data(self, board):
        extra_data = {}

        # Fetch board posts count
        posts_count = self.db.query(func.count('*').label('count1')).filter(and_(
            ForumPost.thread == ForumThread.id,
            ForumThread.board == board.id,
            ForumThread.deleted == False,
            ForumPost.deleted == False
        )).all()

        # Fetch board thread count
        threads_count = self.db.query(func.count('*').label('count1')).filter(and_(
            ForumThread.board == board.id,
            ForumThread.deleted == False,
        )).all()

        # Get board last post
        last_post = self.db.query(ForumPost, ForumThread, User).filter(and_(
            ForumPost.thread == ForumThread.id,
            User.id == ForumPost.user,
            ForumThread.board == board.id,
            ForumPost.deleted == False,
            ForumThread.deleted == False
        )).order_by(ForumPost.id.desc()).first()

        # Form a custom last post serialized object
        if last_post:
            last_post_ser = last_post[0].serialize()
            last_post_ser.update({
                'thread_title': last_post[1].title,
                'user_nickname': last_post[2].nickname,
            })
            del last_post_ser['message']  # No need to send, just reduce payload size
        else:
            last_post_ser = None

        # Get correct objects from responses
        extra_data['posts_count'] = posts_count[0][0]
        extra_data['threads_count'] = threads_count[0][0]
        extra_data['last_post'] = last_post_ser
        return extra_data

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
            serialized = board.serialize()
            serialized.update(self._get_board_extra_data(board))
            out.append(serialized)
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
        if not board or not self._has_rights_to_board(board):
            self.send_error(404, "Board not Found")
            return

        # Base query
        posts_query = self.db.query(func.count('*').label('posts_count')).filter(and_(
            ForumPost.thread == ForumThread.id,
            ForumPost.deleted == False
        ))
        base_query = self.db.query(ForumThread, posts_query.as_scalar()).filter(
            ForumThread.board == board_id,
            ForumThread.deleted == False
        )

        # Get threads + thread count, apply limit and offset if required in args
        threads_count = base_query.count()
        threads = base_query.order_by(ForumThread.created_at.desc())
        if start:
            threads = threads.offset(start)
        if count:
            threads = threads.limit(count)

        thread_list = []
        user_list = {}
        for thread, posts_count in threads:
            # Serialize thread contents
            data = thread.serialize()

            # Insert post count
            data['posts_count'] = posts_count

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
                serialized_board = board.serialize()
                serialized_board.update(self._get_board_extra_data(board))
                out_section['boards'].append(serialized_board)
            out.append(out_section)
        self.send_message({'sections': out})

    @validate_message_schema(update_thread_views_request)
    def update_thread_views(self, track_route, message):
        thread_id = message['data']['thread']
        try:
            thread = ForumThread.get_one(self.db, id=thread_id)
            thread.views += 1
            self.db.add(thread)
        except NoResultFound:
            pass

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
        post_id = message['data']['post']
        msg = bleach.clean(message['data']['message'])
        edit_msg = message['data'].get('edit_message')
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

        # Save edit (with message if given)
        edit = ForumPostEdit()
        edit.message = bleach.clean(edit_msg) if edit_msg else None
        edit.post = post.id
        edit.user = self.session.user.id
        self.db.add(edit)

        # Notify the sender user about success
        self.send_message({
            'thread': thread.serialize(),
            'post': post.serialize(),
            'user': self.session.user.serialize(),
            'edit': edit.serialize()
        })

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
        thread_id = message['data']['thread']
        title = message['data']['title']
        closed = message['data']['closed']
        sticky = message['data']['sticky']
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
        validate_required_field('title', title, errors_list)

        # If errors, stop here
        if errors_list.get_list():
            self.send_error(450, errors_list)
            return

        # Update fields
        thread.sticky = sticky
        thread.closed = closed
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
        post_id = message['data']['post']

        try:
            post = ForumPost.get_one(self.db, id=post_id, deleted=False)
            post.deleted = True
            self.db.add(post)
        except NoResultFound:
            self.send_error(404, u"Post not found")
            return

        self.send_message({})

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_thread_request)
    def delete_thread(self, track_route, message):
        thread_id = message['data']['thread']

        try:
            thread = ForumThread.get_one(self.db, id=thread_id, deleted=False)
            thread.deleted = True
            self.db.add(thread)
        except NoResultFound:
            self.send_error(404, u"Thread not found")
            return

        self.send_message({})

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_board_request)
    def delete_board(self, track_route, message):
        board_id = message['data']['board']

        try:
            board = ForumBoard.get_one(self.db, id=board_id, deleted=False)
            board.deleted = True
            self.db.add(board)
        except NoResultFound:
            self.send_error(404, u"Board not found")
            return

        self.send_message({})

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(delete_section_request)
    def delete_section(self, track_route, message):
        section_id = message['data']['section']

        try:
            section = ForumSection.get_one(self.db, id=section_id, deleted=False)
            section.deleted = True
            self.db.add(section)
        except NoResultFound:
            self.send_error(404, u"Section not found")
            return

        self.send_message({})

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(insert_board_request)
    def insert_board(self, track_route, message):
        section_id = message['data']['section']
        title = message['data']['title']
        description = message['data']['description']
        req_level = message['data']['req_level']
        sort_index = message['data']['sort_index']

        # Make sure the section exists first
        try:
            ForumSection.get_one(self.db, id=section_id)
        except NoResultFound:
            self.send_error(404, u"Section not found")
            return

        # Add a new board
        board = ForumBoard()
        board.section = section_id
        board.title = title
        board.description = description
        board.req_level = req_level
        board.sort_index = sort_index
        self.db.add(board)
        self.db.flush()

        # Send response to the user and broadcast the new board
        self.send_message({
            'board': board.serialize()
        })
        self.broadcast_message({
            'board': board.serialize()
        })

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(update_board_request)
    def update_board(self, track_route, message):
        board_id = message['data']['board']
        title = message['data']['title']
        description = message['data']['description']
        req_level = message['data']['req_level']
        sort_index = message['data']['sort_index']

        # Make sure the board exists first
        try:
            board = ForumBoard.get_one(self.db, id=board_id)
        except NoResultFound:
            self.send_error(404, u"Board not found")
            return

        # Update content data
        board.title = title
        board.description = description
        board.req_level = req_level
        board.sort_index = sort_index
        self.db.add(board)

        # Just send the new object
        self.send_message({
            'board': board.serialize()
        })

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(insert_section_request)
    def insert_section(self, track_route, message):
        title = message['data']['title']
        sort_index = message['data']['sort_index']

        # Save the new section
        section = ForumSection()
        section.title = title
        section.sort_index = sort_index
        self.db.add(section)
        self.db.flush()

        # Send response to the user and broadcast the new section
        self.send_message({
            'section': section.serialize()
        })
        self.broadcast_message({
            'section': section.serialize()
        })

    @has_level(LEVEL_ADMIN)
    @validate_message_schema(update_section_request)
    def update_section(self, track_route, message):
        section_id = message['data']['section']
        title = message['data']['title']
        sort_index = message['data']['sort_index']

        # Make sure the section exists first
        try:
            section = ForumSection.get_one(self.db, id=section_id)
        except NoResultFound:
            self.send_error(404, u"Section not found")
            return

        # Update content data
        section.title = title
        section.sort_index = sort_index
        self.db.add(section)

        # Just send the new object
        self.send_message({
            'section': section.serialize()
        })

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
            'update_thread_views': self.update_thread_views,
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
