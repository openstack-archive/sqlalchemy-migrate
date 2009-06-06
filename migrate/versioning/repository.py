"""
   SQLAlchemy migrate repository management.
"""
import os
import shutil
import string
from pkg_resources import resource_string, resource_filename

from migrate.versioning import exceptions, script, version, pathed, cfgparse
from migrate.versioning.template import template
from migrate.versioning.base import *


class Changeset(dict):
    """A collection of changes to be applied to a database.

    Changesets are bound to a repository and manage a set of logsql
    scripts from that repository.

    Behaves like a dict, for the most part. Keys are ordered based on
    start/end.
    """

    def __init__(self, start, *changes, **k):
        """
        Give a start version; step must be explicitly stated.
        """
        self.step = k.pop('step', 1)
        self.start = version.VerNum(start)
        self.end = self.start
        for change in changes:
            self.add(change)

    def __iter__(self):
        return iter(self.items())

    def keys(self):
        """
        In a series of upgrades x -> y, keys are version x. Sorted.
        """
        ret = super(Changeset, self).keys()
        # Reverse order if downgrading
        ret.sort(reverse=(self.step < 1))
        return ret

    def values(self):
        return [self[k] for k in self.keys()]

    def items(self):
        return zip(self.keys(), self.values())

    def add(self, change):
        key = self.end
        self.end += self.step
        self[key] = change

    def run(self, *p, **k):
        for version, script in self:
            script.run(*p, **k)


class Repository(pathed.Pathed):
    """A project's change script repository"""
    _config = 'migrate.cfg'
    _versions = 'versions'

    def __init__(self, path):
        log.info('Loading repository %s...' % path)
        self.verify(path)
        super(Repository, self).__init__(path)
        self.config=cfgparse.Config(os.path.join(self.path, self._config))
        self.versions=version.Collection(os.path.join(self.path,
                                                      self._versions))
        log.info('Repository %s loaded successfully' % path)
        log.debug('Config: %r' % self.config.to_dict())

    @classmethod
    def verify(cls, path):
        """
        Ensure the target path is a valid repository.

        :raises: :exc:`InvalidRepositoryError` if not valid
        """
        # Ensure the existance of required files
        try:
            cls.require_found(path)
            cls.require_found(os.path.join(path, cls._config))
            cls.require_found(os.path.join(path, cls._versions))
        except exceptions.PathNotFoundError, e:
            raise exceptions.InvalidRepositoryError(path)

    @classmethod
    def prepare_config(cls, pkg, rsrc, name, **opts):
        """
        Prepare a project configuration file for a new project.
        """
        # Prepare opts
        defaults=dict(
            version_table='migrate_version',
            repository_id=name,
            required_dbs=[], )
        for key, val in defaults.iteritems():
            if (key not in opts) or (opts[key] is None):
                opts[key]=val

        tmpl = resource_string(pkg, rsrc)
        ret = string.Template(tmpl).substitute(opts)
        return ret

    @classmethod
    def create(cls, path, name, **opts):
        """Create a repository at a specified path"""
        cls.require_notfound(path)

        pkg, rsrc = template.get_repository(as_pkg=True)
        tmplpkg = '.'.join((pkg, rsrc))
        tmplfile = resource_filename(pkg, rsrc)
        config_text = cls.prepare_config(tmplpkg, cls._config, name, **opts)
        # Create repository
        try:
            shutil.copytree(tmplfile, path)
            # Edit config defaults
            fd = open(os.path.join(path, cls._config), 'w')
            fd.write(config_text)
            fd.close()
            # Create a management script
            manager = os.path.join(path, 'manage.py')
            manage(manager, repository=path)
        except:
            log.error("There was an error creating your repository")
        return cls(path)

    def create_script(self, description, **k):
        self.versions.create_new_python_version(description, **k)

    def create_script_sql(self, database, **k):
        self.versions.create_new_sql_version(database, **k)

    latest=property(lambda self: self.versions.latest)
    version_table=property(lambda self: self.config.get('db_settings',
                                                        'version_table'))
    id=property(lambda self: self.config.get('db_settings', 'repository_id'))

    def version(self, *p, **k):
        return self.versions.version(*p, **k)

    @classmethod
    def clear(cls):
        super(Repository, cls).clear()
        version.Collection.clear()

    def changeset(self, database, start, end=None):
        """
        Create a changeset to migrate this dbms from ver. start to end/latest.
        """
        start = version.VerNum(start)
        if end is None:
            end = self.latest
        else:
            end = version.VerNum(end)
        if start <= end:
            step = 1
            range_mod = 1
            op = 'upgrade'
        else:
            step = -1
            range_mod = 0
            op = 'downgrade'
        versions = range(start+range_mod, end+range_mod, step)
        changes = [self.version(v).script(database, op) for v in versions]
        ret = Changeset(start, step=step, *changes)
        return ret


def manage(file, **opts):
    """Create a project management script"""
    pkg, rsrc = template.manage(as_pkg=True)
    tmpl = resource_string(pkg, rsrc)
    vars = ",".join(["%s='%s'" % vars for vars in opts.iteritems()])
    result = tmpl%dict(defaults=vars)

    fd = open(file, 'w')
    fd.write(result)
    fd.close()
