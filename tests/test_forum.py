# -*- coding: utf-8 -*-

import unittest
import helper
import random
from passlib.hash import pbkdf2_sha512
import loremipsum
from aetherguild.listener_service.session import LEVEL_USER, LEVEL_GUEST, LEVEL_ADMIN
from aetherguild.listener_service.handlers.forumhandler import ForumHandler
from aetherguild.listener_service.tables import ForumSection, ForumBoard, ForumThread, ForumPost, ForumPostEdit, User


class TestForum(unittest.TestCase, helper.DatabaseTestHelper):
    def setUp(self):
        self.init_database()
        s = self.session()

        self.forum_handler = ForumHandler(self.db)

        user = User()
        user.nickname = u'TestUser'
        user.username = u'test_user'
        user.password = pbkdf2_sha512.encrypt(u'{}'.format(random.random()))
        s.add(user)
        s.commit()

        for section_num in range(0, 2):
            section = ForumSection()
            section.title = u'Section {}'.format(section_num)
            section.description = u'Description for section {}'.format(section_num)
            section.sort_index = section_num
            s.add(section)
            s.commit()

            for board_num in range(0, 4):
                board = ForumBoard()
                board.section = section.id
                board.title = u'Board {}-{}'.format(section_num, board_num)
                board.description = u'Description for board {}-{}'.format(section_num, board_num)
                board.req_level = section_num
                board.sort_index = board_num
                s.add(board)
                s.commit()

                for thread_num in range(0, 11):
                    thread = ForumThread()
                    thread.board = board.id
                    thread.user = user.id
                    thread.title = u'Thread {}-{}-{}'.format(section_num, board_num, thread_num)
                    s.add(thread)
                    s.commit()

                    for post_num in range(0, 14):
                        post = ForumPost()
                        post.thread = thread.id
                        post.user = user.id
                        post.message = u'\n'.join(loremipsum.get_sentences(random.randint(1, 8)))
                        s.add(post)
                        s.commit()

                        for edit_num in range(0, random.randint(0, 2)):
                            edit = ForumPostEdit()
                            edit.post = post.id
                            edit.user = user.id
                            edit.message = u'Edit for post {}'.format(post_num)
                            s.add(edit)
                            s.commit()

    def test_get_sections(self):
        print

    def tearDown(self):
        self.close_database()
