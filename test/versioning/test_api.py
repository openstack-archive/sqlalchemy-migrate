#!/usr/bin/python
# -*- coding: utf-8 -*-

from migrate.versioning import api
from migrate.versioning.exceptions import *

from test.fixture.pathed import *


class TestAPI(Pathed):

    def test_help(self):
        self.assertTrue(isinstance(api.help('help'), basestring))
        self.assertRaises(UsageError, api.help)
        self.assertRaises(UsageError, api.help, 'foobar')
        self.assert_(isinstance(api.help('create'), str))

    def test_help_commands(self):
        pass

    def test_create(self):
        pass

    def test_script(self):
        pass

    def test_script_sql(self):
        pass
