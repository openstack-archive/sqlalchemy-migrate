#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from scripttest import TestFileEnvironment

from tests.fixture.pathed import *


class Shell(Pathed):
    """Base class for command line tests"""

    def setUp(self):
        super(Shell, self).setUp()
        self.env = TestFileEnvironment(
            base_path=os.path.join(self.temp_usable_dir, 'env'),
            script_path=[os.path.dirname(sys.executable)], # PATH to migrate development script folder
            environ={'PYTHONPATH': '%s/tests' % (os.getcwd(),)},
        )
        self.env.run("virtualenv %s" % self.env.base_path)
        self.env.run("%s/bin/python setup.py install" % (self.env.base_path,), cwd=os.getcwd())

    def run_version(self, repos_path):
        result = self.env.run('bin/migrate version %s' % repos_path)
        return int(result.stdout.strip())

    def run_db_version(self, url, repos_path):
        result = self.env.run('bin/migrate db_version %s %s' % (url, repos_path))
        return int(result.stdout.strip())
