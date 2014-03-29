0.7.3 (201x-xx-xx)
---------------------------

Changes
******************

-

Documentation
******************

-

Features
******************

-

Fixed Bugs
******************

- #140: excludeTablesgetDiffOfModelAgainstModel is not passing excludeTables
  correctly (patch by Jason Michalski)
- #72:  Regression against issue #38, migrate drops engine reference (patch by
  asuffield@gmail.com)
- #154: versioning/schema.py imports deprecated sqlalchemy.exceptions (patch by
  Alex Favaro)
- fix deprecation warning using MetaData.reflect instead of reflect=True
  constructor argument
- fix test failure by removing unsupported length argument for Text column

0.7.2 (2011-11-01)
---------------------------

Changes
******************

- support for SQLAlchemy 0.5.x has been dropped
- Python 2.6 is the minimum supported Python version

Documentation
******************

- add :ref:`credits <credits>` for contributors
- add :ref:`glossary <glossary>`
- improve :ref:`advice on testing production changes <production testing
  warning>`
- improve Sphinx markup
- refine :ref:`Database Schema Versioning <versioning-system>` texts, add
  example for adding/droping columns (#104)
- add more developer related information to :ref:`development` section
- use sphinxcontrib.issuetracker to link to Google Code issue tracker

Features
******************

- improved :pep:`8` compliance (#122)
- optionally number versions with timestamps instead of sequences (partly
  pulled from Pete Keen)
- allow descriptions in SQL change script filenames (by Pete Keen)
- improved model generation

Fixed Bugs
******************

- #83: api test downgrade/upgrade does not work with sql scripts (pulled from
  Yuen Ho Wong)
- #105: passing a unicode string as the migrate repository fails (add
  regression test)
- #113: make_update_script_for_model fails with AttributeError: 'SchemaDiff'
  object has no attribute 'colDiffs' (patch by Jeremy Cantrell)
- #118: upgrade and downgrade functions are reversed when using the command
  "make_update_script_for_model" (patch by Jeremy Cantrell)
- #121: manage.py should use the "if __name__=='__main__'" trick
- #123: column creation in make_update_script_for_model and required API change
  (by Gabriel de Perthuis)
- #124: compare_model_to_db gets confused by sqlite_sequence (pulled from
  Dustin J. Mitchell)
- #125: drop column does not work on persistent sqlite databases (pulled from
  Benoît Allard)
- #128: table rename failure with sqlalchemy 0.7.x (patch by Mark McLoughlin)
- #129: update documentation and help text (pulled from Yuen Ho Wong)

0.7.1 (2011-05-27)
---------------------------

Fixed Bugs
******************

- docs/_build is excluded from source tarball builds
- use table.append_column() instead of column._set_parent() in
  ChangesetColumn.add_to_table()
- fix source and issue tracking URLs in documentation

0.7 (2011-05-27)
---------------------------

Features
******************

- compatibility with SQLAlchemy 0.7
- add :py:data:`migrate.__version__`

Fixed bugs
******************

- fix compatibility issues with SQLAlchemy 0.7

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
- repository keyword in :py:func:`migrate.versioning.api.version_control` can
  also be unicode
- added if main condition for manage.py script
- make :py:func:`migrate.changeset.constraint.ForeignKeyConstraint.autoname`
  work with SQLAlchemy 0.5 and 0.6
- fixed case sensitivity in setup.py dependencies
- moved :py:mod:`migrate.changeset.exceptions` and
  :py:mod:`migrate.versioning.exceptions` to :py:mod:`migrate.exceptions`
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
  :py:func:`migrate.versioning.shell.main` failed
- #108: Fixed issues with firebird support.

0.6 (11.07.2010)
---------------------------

.. _backwards-06:

.. warning:: **Backward incompatible changes**:

    - :py:func:`migrate.versioning.api.test` and schema comparison functions
      now all accept `url` as first parameter and `repository` as second.
    - python upgrade/downgrade scripts do not import `migrate_engine`
      magically, but recieve engine as the only parameter to function (eg.
      ``def upgrade(migrate_engine):``)
    - :py:meth:`Column.alter <migrate.changeset.schema.ChangesetColumn.alter>`
      does not accept `current_name` anymore, it extracts name from the old
      column.

Features
**************

- added support for :ref:`firebird <firebird-d>`
- added option to define custom templates through option ``--templates_path``
  and ``--templates_theme``,
  read more in :ref:`tutorial section <custom-templates>`
- use Python logging for output, can be shut down by passing
  ``--disable_logging`` to :py:func:`migrate.versioning.shell.main`
- deprecated `alter_column` comparing of columns. Just use explicit parameter
  change.
- added support for SQLAlchemy 0.6.x by Michael Bayer
- Constraint classes have `cascade=True` keyword argument to issue ``DROP
  CASCADE`` where supported
- added :py:class:`~migrate.changeset.constraint.UniqueConstraint`/
  :py:class:`~migrate.changeset.constraint.CheckConstraint` and corresponding
  create/drop methods
- API `url` parameter can also be an :py:class:`Engine` instance (this usage is
  discouraged though sometimes necessary)
- code coverage is up to 80% with more than 100 tests
- alter, create, drop column / rename table / rename index constructs now
  accept `alter_metadata` parameter. If True, it will modify Column/Table
  objects according to changes. Otherwise, everything will be untouched.
- added `populate_default` bool argument to :py:meth:`Column.create
  <migrate.changeset.schema.ChangesetColumn.create>` which issues corresponding
  UPDATE statements to set defaults after column creation
- :py:meth:`Column.create <migrate.changeset.schema.ChangesetColumn.create>`
  accepts `primary_key_name`, `unique_name` and `index_name` as string value
  which is used as contraint name when adding a column

Fixed bugs
*****************

- :term:`ORM` methods now accept `connection` parameter commonly used for
  transactions
- `server_defaults` passed to :py:meth:`Column.create
  <migrate.changeset.schema.ChangesetColumn.create>` are now issued correctly
- use SQLAlchemy quoting system to avoid name conflicts (#32)
- complete refactoring of :py:class:`~migrate.changeset.schema.ColumnDelta`
  (#23)
- partial refactoring of :py:mod:`migrate.changeset` package
- fixed bug when :py:meth:`Column.alter
  <migrate.changeset.schema.ChangesetColumn.alter>`\(server_default='string')
  was not properly set
- constraints passed to :py:meth:`Column.create
  <migrate.changeset.schema.ChangesetColumn.create>` are correctly interpreted
  (``ALTER TABLE ADD CONSTRAINT`` is issued after ``ATLER TABLE ADD COLUMN``)
- script names don't break with dot in the name

Documentation
*********************

- :ref:`dialect support <dialect-support>` table was added to documentation
- major update to documentation


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
- :pep:`8` clean code

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
- Removed logsql (trac issue 75)
- Updated py.test version from 0.8 to 0.9; added a download link to setup.py
- Fixed incorrect "function not defined" error (trac issue 88)
- Fixed SQLite and .sql scripts (trac issue 87)

0.2.2
-----

- Deprecated driver(engine) in favor of engine.name (trac issue 80)
- Deprecated logsql (trac issue 75)
- Comments in .sql scripts don't make things fail silently now (trac issue 74)
- Errors while downgrading (and probably other places) are shown on their own line
- Created mailing list and announcements list, updated documentation accordingly
- Automated tests now require py.test (trac issue 66)
- Documentation fix to .sql script commits (trac issue 72)
- Fixed a pretty major bug involving logengine, dealing with commits/tests (trac issue 64)
- Fixes to the online docs - default DB versioning table name (trac issue 68)
- Fixed the engine name in the scripts created by the command 'migrate script' (trac issue 69)
- Added Evan's email to the online docs

0.2.1
-----

- Created this changelog
- Now requires (and is now compatible with) SA 0.3
- Commits across filesystems now allowed (shutil.move instead of os.rename) (trac issue 62)
