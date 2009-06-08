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

    Changesets are bound to a repository and manage a set of
    scripts from that repository.

    Behaves like a dict, for the most part. Keys are ordered based on step value.
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
        """Add new change to changeset"""
        key = self.end
        self.end += self.step
        self[key] = change

    def run(self, *p, **k):
        """Run the changeset scripts"""
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
        self.config = cfgparse.Config(os.path.join(self.path, self._config))
        self.versions = version.Collection(os.path.join(self.path,
                                                      self._versions))
        log.info('Repository %s loaded successfully' % path)
        log.debug('Config: %r' % self.config.to_dict())

    @classmethod
    def verify(cls, path):
        """
        Ensure the target path is a valid repository.

        :raises: :exc:`InvalidRepositoryError <migrate.versioning.exceptions.InvalidRepositoryError>`
        """
        # Ensure the existance of required files
        try:
            cls.require_found(path)
            cls.require_found(os.path.join(path, cls._config))
            cls.require_found(os.path.join(path, cls._versions))
        except exceptions.PathNotFoundError, e:
            raise exceptions.InvalidRepositoryError(path)

    # TODO: what are those options?
    @classmethod
    def prepare_config(cls, pkg, rsrc, name, **opts):
        """
        Prepare a project configuration file for a new project.
        """
        # Prepare opts
        defaults = dict(
            version_table = 'migrate_version',
            repository_id = name,
            required_dbs = [])

        defaults.update(opts)

        tmpl = resource_string(pkg, rsrc)
        ret = string.Template(tmpl).substitute(defaults)
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
        shutil.copytree(tmplfile, path)

        # Edit config defaults
        fd = open(os.path.join(path, cls._config), 'w')
        fd.write(config_text)
        fd.close()

        # Create a management script
        manager = os.path.join(path, 'manage.py')
        Repository.create_manage_file(manager, repository=path)

        return cls(path)

    def create_script(self, description, **k):
        """API to :meth:`migrate.versioning.version.Collection.create_new_python_version`"""
        self.versions.create_new_python_version(description, **k)

    def create_script_sql(self, database, **k):
        """API to :meth:`migrate.versioning.version.Collection.create_new_sql_version`"""
        self.versions.create_new_sql_version(database, **k)

    @property
    def latest(self):
        """API to :attr:`migrate.versioning.version.Collection.latest`"""
        return self.versions.latest

    @property
    def version_table(self):
        """Returns version_table name specified in config"""
        return self.config.get('db_settings', 'version_table')

    @property
    def id(self):
        """Returns repository id specified in config"""
        return self.config.get('db_settings', 'repository_id')

    def version(self, *p, **k):
        """API to :attr:`migrate.versioning.version.Collection.version`"""
        return self.versions.version(*p, **k)

    @classmethod
    def clear(cls):
        # TODO: deletes repo
        super(Repository, cls).clear()
        version.Collection.clear()

    def changeset(self, database, start, end=None):
        """Create a changeset to migrate this database from ver. start to end/latest.

        :param database: name of database to generate changeset
        :param start: version to start at
        :param end: version to end at (latest if None given)
        :type database: string
        :type start: int
        :type end: int
        :returns: :class:`Changeset instance <migration.versioning.repository.Changeset>`
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

        versions = range(start + range_mod, end + range_mod, step)
        changes = [self.version(v).script(database, op) for v in versions]
        ret = Changeset(start, step=step, *changes)
        return ret

    @classmethod
    def create_manage_file(cls, file_, **opts):
        """Create a project management script (manage.py)
        
        :param file_: Destination file to be written
        :param opts: Options that are passed to template
        """
        vars_ = ",".join(["%s='%s'" % var for var in opts.iteritems()])

        pkg, rsrc = template.manage(as_pkg=True)
        tmpl = resource_string(pkg, rsrc)
        result = tmpl % dict(defaults=vars_)

        fd = open(file_, 'w')
        fd.write(result)
        fd.close()
