0.6.1 (2011-02-11)
---------------------------

Features
******************
- implemented column adding when foreign keys are present for sqlite
- implemented columns adding with unique constraints for sqlite
- implemented adding unique and foreign key constraints to columns
  for sqlite
- remove experimental `alter_metadata` parameter

Fixed bugs
******************

- updated tests for Python 2.7
- repository keyword in :func:`api.version_control` can also be unicode
- added if main condition for manage.py script
- make :func:`migrate.changeset.constraint.ForeignKeyConstraint.autoname`
  work with SQLAlchemy 0.5 and 0.6
- fixed case sensitivity in setup.py dependencies
- moved :mod:`migrate.changeset.exceptions` and :mod:`migrate.versioning.exceptions`
  to :mod:`migrate.exceptions`
- cleared up test output and improved testing of deprecation warnings. 
- some documentation fixes
- #107: fixed syntax error in genmodel.py 
- #96: fixed bug with column dropping in sqlite
- #94: fixed bug that prevented non-unique indexes being created
- fixed bug with column dropping involving foreign keys
- fixed bug when dropping columns with unique constraints in sqlite
- rewrite of the schema diff internals, now supporting column
  differences in additon to missing columns and tables.
- fixed bug when passing empty list in
  :func:`migrate.versioning.shell.main` failed 
- #108: Fixed issues with firebird support.

0.6 (11.07.2010)
---------------------------

.. _backwards-06:

.. warning:: **Backward incompatible changes**:

    - :func:`api.test` and schema comparison functions now all accept `url` as first parameter and `repository` as second.
    - python upgrade/downgrade scripts do not import `migrate_engine` magically, but recieve engine as the only parameter to function (eg. ``def upgrade(migrate_engine):``)
    - :meth:`Column.alter <migrate.changeset.schema.ChangesetColumn.alter>` does not accept `current_name` anymore, it extracts name from the old column.

Features
**************

- added support for :ref:`firebird <firebird-d>`
- added option to define custom templates through option ``--templates_path`` and ``--templates_theme``,
  read more in :ref:`tutorial section <custom-templates>`
- use Python logging for output, can be shut down by passing ``--disable_logging`` to :func:`migrate.versioning.shell.main`
- deprecated `alter_column` comparing of columns. Just use explicit parameter change.
- added support for SQLAlchemy 0.6.x by Michael Bayer
- Constraint classes have `cascade=True` keyword argument to issue ``DROP CASCADE`` where supported
- added :class:`~migrate.changeset.constraint.UniqueConstraint`/:class:`~migrate.changeset.constraint.CheckConstraint`
  and corresponding create/drop methods
- API `url` parameter can also be an :class:`Engine` instance (this usage is discouraged though sometimes necessary)
- code coverage is up to 80% with more than 100 tests
- alter, create, drop column / rename table / rename index constructs now accept `alter_metadata` parameter. If True, it will modify Column/Table objects according to changes. Otherwise, everything will be untouched.
- added `populate_default` bool argument to :meth:`Column.create <migrate.changeset.schema.ChangesetColumn.create>` which issues corresponding UPDATE statements to set defaults after column creation
- :meth:`Column.create <migrate.changeset.schema.ChangesetColumn.create>` accepts `primary_key_name`, `unique_name` and `index_name` as string value which is used as contraint name when adding a column

Bug fixes
*****************

- ORM methods now accept `connection` parameter commonly used for transactions
- `server_defaults` passed to :meth:`Column.create <migrate.changeset.schema.ChangesetColumn.create>`
  are now issued correctly
- use SQLAlchemy quoting system to avoid name conflicts (for issue 32)
- complete refactoring of :class:`~migrate.changeset.schema.ColumnDelta` (fixes issue 23)
- partial refactoring of :mod:`changeset` package
- fixed bug when :meth:`Column.alter <migrate.changeset.schema.ChangesetColumn.alter>`\(server_default='string') was not properly set
- constraints passed to :meth:`Column.create <migrate.changeset.schema.ChangesetColumn.create>` are correctly interpreted  (``ALTER TABLE ADD CONSTRAINT`` is issued after ``ATLER TABLE ADD COLUMN``)
- script names don't break with dot in the name

Documentation
*********************

- :ref:`dialect support <dialect-support>` table was added to documentation
- majoy update to documentation



0.5.4
-----

- fixed preview_sql parameter for downgrade/upgrade. Now it prints SQL if the step is SQL script and runs step with mocked engine to only print SQL statements if ORM is used. [Domen Kozar]
- use entrypoints terminology to specify dotted model names (module.model:User) [Domen Kozar]
- added engine_dict and engine_arg_* parameters to all api functions (deprecated echo) [Domen Kozar]
- make --echo parameter a bit more forgivable (better Python API support)  [Domen Kozar]
- apply patch to refactor cmd line parsing for Issue 54 by Domen Kozar

0.5.3
-----

- apply patch for Issue 29 by Jonathan Ellis
- fix Issue 52 by removing needless parameters from object.__new__ calls

0.5.2
-----

- move sphinx and nose dependencies to extras_require and tests_require
- integrate patch for Issue 36 by Kumar McMillan
- fix unit tests
- mark ALTER TABLE ADD COLUMN with FOREIGN KEY as not supported by SQLite

0.5.1.2
-------

- corrected build

0.5.1.1
-------

- add documentation in tarball
- add a MANIFEST.in

0.5.1
-----

- SA 0.5.x support. SQLAlchemy < 0.5.1 not supported anymore.
- use nose instead of py.test for testing
- Added --echo=True option for all commands, which will make the sqlalchemy connection echo SQL statements.
- Better PostgreSQL support, especially for schemas.
- modification to the downgrade command to simplify the calling (old way still works just fine)
- improved support for SQLite
- add support for check constraints (EXPERIMENTAL)
- print statements removed from APIs
- improved sphinx based documentation
- removal of old commented code
- PEP-8 clean code

0.4.5
-----

- work by Christian Simms to compare metadata against databases
- new repository format
- a repository format migration tool is in migrate/versioning/migrate_repository.py
- support for default SQL scripts
- EXPERIMENTAL support for dumping database to model

0.4.4
-----

- patch by pwannygoodness for Issue #15
- fixed unit tests to work with py.test 0.9.1
- fix for a SQLAlchemy deprecation warning

0.4.3
-----

- patch by Kevin Dangoor to handle database versions as packages and ignore their __init__.py files in version.py
- fixed unit tests and Oracle changeset support by Christian Simms

0.4.2
-----

- package name is sqlalchemy-migrate again to make pypi work
- make import of sqlalchemy's SchemaGenerator work regardless of previous imports

0.4.1
-----

- setuptools patch by Kevin Dangoor
- re-rename module to migrate

0.4.0
-----

- SA 0.4.0 compatibility thanks to Christian Simms
- all unit tests are working now (with sqlalchemy >= 0.3.10)

0.3
---

- SA 0.3.10 compatibility

0.2.3
-----

- Removed lots of SA monkeypatching in Migrate's internals
- SA 0.3.3 compatibility
- Removed logsql (#75)
- Updated py.test version from 0.8 to 0.9; added a download link to setup.py
- Fixed incorrect "function not defined" error (#88)
- Fixed SQLite and .sql scripts (#87)

0.2.2
-----

- Deprecated driver(engine) in favor of engine.name (#80)
- Deprecated logsql (#75)
- Comments in .sql scripts don't make things fail silently now (#74)
- Errors while downgrading (and probably other places) are shown on their own line
- Created mailing list and announcements list, updated documentation accordingly
- Automated tests now require py.test (#66)
- Documentation fix to .sql script commits (#72)
- Fixed a pretty major bug involving logengine, dealing with commits/tests (#64)
- Fixes to the online docs - default DB versioning table name (#68)
- Fixed the engine name in the scripts created by the command 'migrate script' (#69)
- Added Evan's email to the online docs

0.2.1
-----

- Created this changelog
- Now requires (and is now compatible with) SA 0.3
- Commits across filesystems now allowed (shutil.move instead of os.rename) (#62)
