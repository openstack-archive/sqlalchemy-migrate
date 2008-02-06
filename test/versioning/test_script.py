from test import fixture
from migrate.versioning.script import *
from migrate.versioning import exceptions
import os,shutil

class TestPyScript(fixture.Pathed):
    cls = PythonScript
    def test_create(self):
        """We can create a migration script"""
        path=self.tmp_py()
        # Creating a file that doesn't exist should succeed
        self.cls.create(path)
        self.assert_(os.path.exists(path))
        # Created file should be a valid script (If not, raises an error)
        self.cls.verify(path)
        # Can't create it again: it already exists
        self.assertRaises(exceptions.PathFoundError,self.cls.create,path)

    def test_verify_notfound(self):
        """Correctly verify a python migration script: nonexistant file"""
        path=self.tmp_py()
        self.assert_(not os.path.exists(path))
        # Fails on empty path
        self.assertRaises(exceptions.InvalidScriptError,self.cls.verify,path)
        self.assertRaises(exceptions.InvalidScriptError,self.cls,path)

    def test_verify_invalidpy(self):
        """Correctly verify a python migration script: invalid python file"""
        path=self.tmp_py()
        # Create empty file
        f=open(path,'w')
        f.write("def fail")
        f.close()
        self.assertRaises(Exception,self.cls.verify_module,path)
        # script isn't verified on creation, but on module reference
        py = self.cls(path)
        self.assertRaises(Exception,(lambda x: x.module),py)

    def test_verify_nofuncs(self):
        """Correctly verify a python migration script: valid python file; no upgrade func"""
        path=self.tmp_py()
        # Create empty file
        f=open(path,'w')
        f.write("def zergling():\n\tprint 'rush'")
        f.close()
        self.assertRaises(exceptions.InvalidScriptError,self.cls.verify_module,path)
        # script isn't verified on creation, but on module reference
        py = self.cls(path)
        self.assertRaises(exceptions.InvalidScriptError,(lambda x: x.module),py)

    def test_verify_success(self):
        """Correctly verify a python migration script: success"""
        path=self.tmp_py()
        # Succeeds after creating
        self.cls.create(path)
        self.cls.verify(path)
    
