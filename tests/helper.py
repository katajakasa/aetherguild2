# -*- coding: utf-8 -*-

import os
import json
import loremipsum
import random
from sqlalchemy.orm import sessionmaker
from passlib.hash import pbkdf2_sha512
from sqlalchemy import create_engine
from aetherguild.listener_service.tables import Base, ForumSection, ForumBoard, ForumThread, ForumPost,\
    ForumPostEdit, User, Session


class DatabaseTestHelper(object):
    def __init__(self):
        self.test_users = []
        self.test_sessions = []
        self.engine = None
        self.db = None

    def init_database(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.db = sessionmaker(bind=self.engine, autoflush=True)
        Base.metadata.create_all(self.engine)

    def close_database(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def create_test_users(self):
        s = self.db()
        self.test_users = []
        for m in range(0, 3):
            user = User()
            user.username = u'test_user{}'.format(m)
            user.nickname = u'Nickname {}'.format(m)
            user.password = pbkdf2_sha512.encrypt(u'password_{}'.format(m))
            user.level = m
            s.add(user)
            self.test_users.append(user)
        s.commit()

    def create_test_sessions(self):
        s = self.db()
        self.test_sessions = []
        for user in self.test_users:
            ses = Session()
            ses.user = user.id
            ses.session_key = u'testsession_{}'.format(user.id)
            s.add(ses)
            self.test_sessions.append(ses)
        s.commit()

    def create_test_forum(self, user):
        s = self.db()
        for section_num in range(0, 2):
            section = ForumSection()
            section.title = u'Section {}'.format(section_num)
            section.description = u'Description for section {}'.format(section_num)
            section.sort_index = section_num
            s.add(section)
            s.flush()

            for board_num in range(0, 4):
                board = ForumBoard()
                board.section = section.id
                board.title = u'Board {}-{}'.format(section_num, board_num)
                board.description = u'Description for board {}-{}'.format(section_num, board_num)
                board.req_level = section_num
                board.sort_index = board_num
                s.add(board)
                s.flush()

                for thread_num in range(0, 11):
                    thread = ForumThread()
                    thread.board = board.id
                    thread.user = user.id
                    thread.title = u'Thread {}-{}-{}'.format(section_num, board_num, thread_num)
                    s.add(thread)
                    s.flush()

                    for post_num in range(0, 14):
                        post = ForumPost()
                        post.thread = thread.id
                        post.user = user.id
                        post.message = u'\n'.join(loremipsum.get_sentences(random.randint(1, 8)))
                        s.add(post)
                        s.flush()

                        for edit_num in range(0, random.randint(0, 2)):
                            edit = ForumPostEdit()
                            edit.post = post.id
                            edit.user = user.id
                            edit.message = u'Edit for post {}'.format(post_num)
                            s.add(edit)
        s.commit()
