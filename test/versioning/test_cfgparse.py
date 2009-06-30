from test import fixture
from migrate.versioning import cfgparse
from migrate.versioning.repository import *

class TestConfigParser(fixture.Base):
    def test_to_dict(self):
        """Correctly interpret config results as dictionaries"""
        parser = cfgparse.Parser(dict(default_value=42))
        self.assert_(len(parser.sections())==0)
        parser.add_section('section')
        parser.set('section','option','value')
        self.assert_(parser.get('section','option')=='value')
        self.assert_(parser.to_dict()['section']['option']=='value')
    
    def test_table_config(self):
        """We should be able to specify the table to be used with a repository"""
        default_text=Repository.prepare_config(template.get_repository(as_pkg=True,as_str=True),
            Repository._config,'repository_name')
        specified_text=Repository.prepare_config(template.get_repository(as_pkg=True,as_str=True),
            Repository._config,'repository_name',version_table='_other_table')
        self.assertNotEquals(default_text,specified_text)
