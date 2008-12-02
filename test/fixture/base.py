#import unittest
#from py.test import raises
from nose.tools import raises

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
    
    def assertRaises(self, exceptions, func, *arg, **kw):
        if not hasattr(exceptions, '__iter__'):
            exceptions = (exceptions, )
        valid = ' or '.join([e.__name__ for e in exceptions])
        try:
            func(*arg, **kw)
        except exceptions:
            pass
        except:
            raise
        else:
            message = "%s() did not raise %s" % (func.__name__, valid)
            raise AssertionError(message)
           
    #def assertRaises(self,error,func,*p,**k):
    #    assert raises(error,func,*p,**k)
        
    def assertEqualsIgnoreWhitespace(self, v1, v2):
        def createLines(s):
            s = s.replace(' ', '')
            lines = s.split('\n')
            return [ line for line in lines if line ]
        lines1 = createLines(v1)
        lines2 = createLines(v2)
        self.assertEquals(len(lines1), len(lines2))
        for line1, line2 in zip(lines1, lines2):
            self.assertEquals(line1, line2)


class Base(FakeTestCase):
    """Base class for other test cases"""
    def ignoreErrors(self,*p,**k):
        """Call a function, ignoring any exceptions"""
        func=p[0]
        try:
            func(*p[1:],**k)
        except:
            pass
