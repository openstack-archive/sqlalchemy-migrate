#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
import sys


# Append test method name,etc. to descriptions automatically.
# Yes, this is ugly, but it's the simplest way...
def getDescription(self, test):
   ret = str(test)
   if self.descriptions:
       return test.shortDescription() or ret
   return ret
unittest2._TextTestResult.getDescription = getDescription


class Result(unittest2._TextTestResult):
    # test description may be changed as we go; store the description at 
    # exception-time and print later
    def __init__(self,*p,**k):
        super(Result,self).__init__(*p,**k)
        self.desc=dict()
    def _addError(self,test,err,errs):
        test,err=errs.pop()
        errdata=(test,err,self.getDescription(test))
        errs.append(errdata)
        
    def addFailure(self,test,err):
        super(Result,self).addFailure(test,err)
        self._addError(test,err,self.failures)
    def addError(self,test,err):
        super(Result,self).addError(test,err)
        self._addError(test,err,self.errors)
    def printErrorList(self, flavour, errors):
        # Copied from unittest2.py
        #for test, err in errors:
        for errdata in errors:
            test,err,desc=errdata
            self.stream.writeln(self.separator1)
            #self.stream.writeln("%s: %s" % (flavour,self.getDescription(test)))
            self.stream.writeln("%s: %s" % (flavour,desc or self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)

class Runner(unittest2.TextTestRunner):
    def _makeResult(self):
        return Result(self.stream,self.descriptions,self.verbosity)

def suite(imports):
    return unittest2.TestLoader().loadTestsFromNames(imports)

def main(imports=None):
    if imports:
        global suite
        suite = suite(imports)
        defaultTest='fixture.suite'
    else:
        defaultTest=None
    return unittest2.TestProgram(defaultTest=defaultTest,\
        testRunner=Runner(verbosity=1))

from base import Base
from migrate.tests.fixture.pathed import Pathed
from shell import Shell
from database import DB,usedb
