#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        def createLines(s):
            s = s.replace(' ', '')
            lines = s.split('\n')
            return [line for line in lines if line]
        lines1 = createLines(v1)
        lines2 = createLines(v2)
        self.assertEquals(len(lines1), len(lines2))
        for line1, line2 in zip(lines1, lines2):
            self.assertEquals(line1, line2)

    def ignoreErrors(self, func, *p,**k):
        """Call a function, ignoring any exceptions"""
        try:
            func(*p,**k)
        except:
            pass
