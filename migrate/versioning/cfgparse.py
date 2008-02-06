from migrate.versioning.base import *
from migrate.versioning import pathed
from ConfigParser import ConfigParser

#__all__=['MigrateConfigParser']

class Parser(ConfigParser):
    """A project configuration file"""
    def to_dict(self,sections=None):
        """It's easier to access config values like dictionaries"""
        return self._sections

class Config(pathed.Pathed,Parser):
    def __init__(self,path,*p,**k):
        """Confirm the config file exists; read it"""
        self.require_found(path)
        pathed.Pathed.__init__(self,path)
        Parser.__init__(self,*p,**k)
        self.read(path)
