# -*- coding: utf-8 -*-

import unittest
import helper
from aetherguild.listener_service.session import LEVEL_USER, LEVEL_GUEST, LEVEL_ADMIN


class TestQuery(unittest.TestCase, helper.DatabaseTestHelper):
    def setUp(self):
        self.init_database()

    def test_auth_login(self):
        pass

    def tearDown(self):
        self.close_database()
