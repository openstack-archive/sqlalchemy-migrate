#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import unittest

from nose.tools import raises, eq_


class Base(unittest.TestCase):

    def setup_method(self,func=None):
        self.setUp()

    def teardown_method(self,func=None):
        self.tearDown()
    
    def assertEqualsIgnoreWhitespace(self, v1, v2):
        """Compares two strings that should be\
        identical except for whitespace
        """
        def strip_whitespace(s):
            return re.sub(r'\s', '', s)

        line1 = strip_whitespace(v1)
        line2 = strip_whitespace(v2)

        self.assertEquals(line1, line2, "%s != %s" % (v1, v2))

    def ignoreErrors(self, func, *p,**k):
        """Call a function, ignoring any exceptions"""
        try:
            func(*p,**k)
        except:
            pass
