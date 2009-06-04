#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import sys
import types

from test.fixture.pathed import *


class Shell(Pathed):
    """Base class for command line tests"""
    def execute(self, command, *p, **k):
        """Return the fd of a command; can get output (stdout/err) and exitcode"""
        # We might be passed a file descriptor for some reason; if so, just return it
        if isinstance(command, types.FileType):
            return command

        # Redirect stderr to stdout
        # This is a bit of a hack, but I've not found a better way
        py_path = os.environ.get('PYTHONPATH', '')
        py_path_list = py_path.split(':')
        py_path_list.append(os.path.abspath('.'))
        os.environ['PYTHONPATH'] = ':'.join(py_path_list)
        fd = os.popen(command + ' 2>&1')

        if py_path:
            py_path = os.environ['PYTHONPATH'] = py_path
        else:
            del os.environ['PYTHONPATH']
        return fd

    def output_and_exitcode(self, *p, **k):
        fd=self.execute(*p, **k)
        output = fd.read().strip()
        exitcode = fd.close()
        if k.pop('emit',False):
            print output
        return (output, exitcode)

    def exitcode(self, *p, **k):
        """Execute a command and return its exit code
        ...without printing its output/errors
        """
        ret = self.output_and_exitcode(*p, **k)
        return ret[1]

    def assertFailure(self, *p, **k):
        output,exitcode = self.output_and_exitcode(*p, **k)
        assert (exitcode), output

    def assertSuccess(self, *p, **k):
        output,exitcode = self.output_and_exitcode(*p, **k)
        #self.assert_(not exitcode, output)
        assert (not exitcode), output
