# -*- coding: utf-8 -*-

import unittest
import helper
from aetherguild.listener_service.handlers.forumhandler import ForumHandler
from aetherguild.listener_service.mq_connection import MQConnectionMock
from aetherguild.listener_service.mq_session import MQSession
from aetherguild.listener_service.user_session import UserSession


class TestForum(unittest.TestCase, helper.DatabaseTestHelper):
    def setUp(self):
        self.init_database()
        self.create_test_users()
        self.create_test_sessions()
        self.create_test_forum(self.test_users[1])

        self.db_session = self.db()
        self.mq_connection = MQConnectionMock()
        self.mq_session = MQSession(self.mq_connection)
        self.user_session_lguest = UserSession(self.db_session, None)
        self.user_session_luser = UserSession(self.db_session, self.test_sessions[1].session_key)
        self.user_session_ladmin = UserSession(self.db_session, self.test_sessions[2].session_key)

    def create_handler(self, route, user_session):
        return ForumHandler(self.db_session, self.mq_session, user_session, 'connection_id', 'receipt_id', route)

    def test_get_sections_as_guest(self):
        h = self.create_handler('forum.get_sections', self.user_session_lguest)
        h.handle(['get_sections'], {})
        self.assertEqual(len(self.mq_connection.message_log), 1)

    def tearDown(self):
        self.close_database()
