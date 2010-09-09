#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2

def main(imports=None):
    if imports:
        global suite
        suite = suite(imports)
        defaultTest='fixture.suite'
    else:
        defaultTest=None
    return unittest2.TestProgram(defaultTest=defaultTest)

from base import Base
from migrate.tests.fixture.pathed import Pathed
from shell import Shell
from database import DB,usedb
