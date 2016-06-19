# -*- coding: utf-8 -*-

import unittest
import helper


class TestAuth(unittest.TestCase, helper.DatabaseTestHelper):
    def setUp(self):
        self.init_database()

    def test_auth_login(self):
        pass

    def tearDown(self):
        self.close_database()
