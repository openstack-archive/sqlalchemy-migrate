from test import fixture
from migrate.versioning.repository import *
import os

class TestPathed(fixture.Base):
    def test_templates(self):
        """We can find the path to all repository templates"""
        path = str(template)
        self.assert_(os.path.exists(path))
    def test_repository(self):
        """We can find the path to the default repository"""
        path = template.get_repository() 
        self.assert_(os.path.exists(path))
    def test_script(self):
        """We can find the path to the default migration script"""
        path = template.get_script() 
        self.assert_(os.path.exists(path))
