from test import fixture
from migrate.versioning.version import *

class TestVerNum(fixture.Base):
    def test_invalid(self):
        """Disallow invalid version numbers"""
        versions = ('-1',-1,'Thirteen','')
        for version in versions:
            self.assertRaises(ValueError,VerNum,version)
    def test_is(self):
        a=VerNum(1)
        b=VerNum(1)
        self.assert_(a is b)
    def test_add(self):
        self.assert_(VerNum(1)+VerNum(1)==VerNum(2))
        self.assert_(VerNum(1)+1==2)
        self.assert_(VerNum(1)+1=='2')
    def test_sub(self):
        self.assert_(VerNum(1)-1==0)
        self.assertRaises(ValueError,lambda:VerNum(0)-1)
    def test_eq(self):
        self.assert_(VerNum(1)==VerNum('1'))
        self.assert_(VerNum(1)==1)
        self.assert_(VerNum(1)=='1')
        self.assert_(not VerNum(1)==2)
    def test_ne(self):
        self.assert_(VerNum(1)!=2)
        self.assert_(not VerNum(1)!=1)
    def test_lt(self):
        self.assert_(not VerNum(1)<1)
        self.assert_(VerNum(1)<2)
        self.assert_(not VerNum(2)<1)
    def test_le(self):
        self.assert_(VerNum(1)<=1)
        self.assert_(VerNum(1)<=2)
        self.assert_(not VerNum(2)<=1)
    def test_gt(self):
        self.assert_(not VerNum(1)>1)
        self.assert_(not VerNum(1)>2)
        self.assert_(VerNum(2)>1)
    def test_ge(self):
        self.assert_(VerNum(1)>=1)
        self.assert_(not VerNum(1)>=2)
        self.assert_(VerNum(2)>=1)
        
class TestDescriptionNaming(fixture.Base):
    def test_names(self):
        self.assertEquals(strToFilename(''), '')
        self.assertEquals(strToFilename('a'), 'a')
        self.assertEquals(strToFilename('Abc Def'), 'Abc_Def')
        self.assertEquals(strToFilename('Abc "D" Ef'), 'Abc_D_Ef')
        self.assertEquals(strToFilename("Abc's Stuff"), 'Abc_s_Stuff')
        self.assertEquals(strToFilename("a      b"), 'a_b')
        
