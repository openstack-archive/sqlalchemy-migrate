"""
   Database schema version management.
"""
from sqlalchemy import (Table, Column, MetaData, String, Text, Integer,
    create_engine)
from sqlalchemy.sql import and_
from sqlalchemy import exceptions as sa_exceptions

from migrate.versioning import exceptions, genmodel, schemadiff
from migrate.versioning.repository import Repository
from migrate.versioning.util import load_model
from migrate.versioning.version import VerNum


class ControlledSchema(object):
    """A database under version control"""

    def __init__(self, engine, repository):
        if isinstance(repository, str):
            repository=Repository(repository)
        self.engine = engine
        self.repository = repository
        self.meta=MetaData(engine)
        self._load()

    def __eq__(self, other):
        return (self.repository is other.repository \
            and self.version == other.version)

    def _load(self):
        """Load controlled schema version info from DB"""
        tname = self.repository.version_table
        self.meta=MetaData(self.engine)
        if not hasattr(self, 'table') or self.table is None:
            try:
                self.table = Table(tname, self.meta, autoload=True)
            except (exceptions.NoSuchTableError):
                raise exceptions.DatabaseNotControlledError(tname)
        # TODO?: verify that the table is correct (# cols, etc.)
        result = self.engine.execute(self.table.select(
                    self.table.c.repository_id == str(self.repository.id)))
        data = list(result)[0]
        # TODO?: exception if row count is bad
        # TODO: check repository id, exception if incorrect
        self.version = data['version']

    def _get_repository(self):
        """
        Given a database engine, try to guess the repository.

        :raise: :exc:`NotImplementedError`
        """
        # TODO: no guessing yet; for now, a repository must be supplied
        raise NotImplementedError()

    @classmethod
    def create(cls, engine, repository, version=None):
        """
        Declare a database to be under a repository's version control.
        """
        # Confirm that the version # is valid: positive, integer,
        # exists in repos
        if type(repository) is str:
            repository=Repository(repository)
        version = cls._validate_version(repository, version)
        table=cls._create_table_version(engine, repository, version)
        # TODO: history table
        # Load repository information and return
        return cls(engine, repository)

    @classmethod
    def _validate_version(cls, repository, version):
        """
        Ensures this is a valid version number for this repository.

        :raises: :exc:`cls.InvalidVersionError` if invalid
        :return: valid version number
        """
        if version is None:
            version = 0
        try:
            version = VerNum(version) # raises valueerror
            if version < 0 or version > repository.latest:
                raise ValueError()
        except ValueError:
            raise exceptions.InvalidVersionError(version)
        return version

    @classmethod
    def _create_table_version(cls, engine, repository, version):
        """
        Creates the versioning table in a database.
        """
        # Create tables
        tname = repository.version_table
        meta = MetaData(engine)

        table = Table(
            tname, meta,
            Column('repository_id', String(255), primary_key=True),
            Column('repository_path', Text),
            Column('version', Integer), )

        if not table.exists():
            table.create()

        # Insert data
        try:
            engine.execute(table.insert(), repository_id=repository.id,
                           repository_path=repository.path,
                           version=int(version))
        except sa_exceptions.IntegrityError:
            # An Entry for this repo already exists.
            raise exceptions.DatabaseAlreadyControlledError()
        return table

    @classmethod
    def compare_model_to_db(cls, engine, model, repository):
        """
        Compare the current model against the current database.
        """
        if isinstance(repository, basestring):
            repository=Repository(repository)
        model = load_model(model)
        diff = schemadiff.getDiffOfModelAgainstDatabase(
            model, engine, excludeTables=[repository.version_table])
        return diff

    @classmethod
    def create_model(cls, engine, repository, declarative=False):
        """
        Dump the current database as a Python model.
        """
        if isinstance(repository, basestring):
            repository=Repository(repository)
        diff = schemadiff.getDiffOfModelAgainstDatabase(
            MetaData(), engine, excludeTables=[repository.version_table])
        return genmodel.ModelGenerator(diff, declarative).toPython()

    def update_db_from_model(self, model):
        """
        Modify the database to match the structure of the current Python model.
        """
        if isinstance(self.repository, basestring):
            self.repository=Repository(self.repository)
        model = load_model(model)
        diff = schemadiff.getDiffOfModelAgainstDatabase(
            model, self.engine, excludeTables=[self.repository.version_table])
        genmodel.ModelGenerator(diff).applyModel()
        update = self.table.update(
            self.table.c.repository_id == str(self.repository.id))
        self.engine.execute(update, version=int(self.repository.latest))

    def drop(self):
        """
        Remove version control from a database.
        """
        try:
            self.table.drop()
        except (sa_exceptions.SQLError):
            raise exceptions.DatabaseNotControlledError(str(self.table))

    def _engine_db(self, engine):
        """
        Returns the database name of an engine - ``postgres``, ``sqlite`` ...
        """
        # TODO: This is a bit of a hack...
        return str(engine.dialect.__module__).split('.')[-1]

    def changeset(self, version=None):
        database = self._engine_db(self.engine)
        start_ver = self.version
        changeset = self.repository.changeset(database, start_ver, version)
        return changeset

    def runchange(self, ver, change, step):
        startver = ver
        endver = ver + step
        # Current database version must be correct! Don't run if corrupt!
        if self.version != startver:
            raise exceptions.InvalidVersionError("%s is not %s" % \
                                                     (self.version, startver))
        # Run the change
        change.run(self.engine, step)
        # Update/refresh database version
        update = self.table.update(
            and_(self.table.c.version == int(startver),
                 self.table.c.repository_id == str(self.repository.id)))
        self.engine.execute(update, version=int(endver))
        self._load()

    def upgrade(self, version=None):
        """
        Upgrade (or downgrade) to a specified version, or latest version.
        """
        changeset = self.changeset(version)
        for ver, change in changeset:
            self.runchange(ver, change, changeset.step)
