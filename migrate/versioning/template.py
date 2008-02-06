from pkg_resources import resource_filename
import os,shutil
import sys
from migrate.versioning.base import *
from migrate.versioning import pathed

class Packaged(pathed.Pathed):
    """An object assoc'ed with a Python package"""
    def __init__(self,pkg):
        self.pkg = pkg
        path = self._find_path(pkg)
        super(Packaged,self).__init__(path)

    @classmethod
    def _find_path(cls,pkg):
        pkg_name, resource_name = pkg.rsplit('.',1)
        ret = resource_filename(pkg_name,resource_name)
        return ret

class Collection(Packaged):
    """A collection of templates of a specific type"""
    _default=None
    def get_path(self,file):
        return os.path.join(self.path,str(file))
    def get_pkg(self,file):
        return (self.pkg,str(file))

class RepositoryCollection(Collection):
    _default='default'

class ScriptCollection(Collection):
    _default='default.py_tmpl'

class Template(Packaged):
    """Finds the paths/packages of various Migrate templates"""
    _repository='repository'
    _script='script'
    _manage='manage.py_tmpl'

    def __init__(self,pkg):
        super(Template,self).__init__(pkg)
        self.repository=RepositoryCollection('.'.join((self.pkg,self._repository)))
        self.script=ScriptCollection('.'.join((self.pkg,self._script)))

    def get_item(self,attr,filename=None,as_pkg=None,as_str=None):
        item = getattr(self,attr)
        if filename is None:
            filename = getattr(item,'_default')
        if as_pkg:
            ret = item.get_pkg(filename)
            if as_str:
                ret = '.'.join(ret)
        else:
            ret = item.get_path(filename)
        return ret

    def get_repository(self,filename=None,as_pkg=None,as_str=None):
        return self.get_item('repository',filename,as_pkg,as_str)
    
    def get_script(self,filename=None,as_pkg=None,as_str=None):
        return self.get_item('script',filename,as_pkg,as_str)

    def manage(self,**k):
        return (self.pkg,self._manage)

template_pkg='migrate.versioning.templates'
template=Template(template_pkg)
