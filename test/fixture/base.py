#import unittest
from py.test import raises

class FakeTestCase(object):
    """Mimics unittest.testcase methods
    Minimize changes needed in migration to py.test
    """
    def setUp(self):
        pass
    def setup_method(self,func=None):
        self.setUp()

    def tearDown(self):
        pass
    def teardown_method(self,func=None):
        self.tearDown()

    def assert_(self,x,doc=None):
        assert x
    def assertEquals(self,x,y,doc=None):
        assert x == y
    def assertNotEquals(self,x,y,doc=None):
        assert x != y
    def assertRaises(self,error,func,*p,**k):
        assert raises(error,func,*p,**k)

class Base(FakeTestCase):
    """Base class for other test cases"""
    def ignoreErrors(self,*p,**k):
        """Call a function, ignoring any exceptions"""
        func=p[0]
        try:
            func(*p[1:],**k)
        except:
            pass
