:mod:`migrate` - SQLAlchemy Migrate (schema change management)
==============================================================

.. module:: migrate
.. moduleauthor:: Evan Rosson

:Author: Evan Rosson
:Maintainer: Domen Kožar <domenNO@SPAMdev.si>
:Source code: http://code.google.com/p/sqlalchemy-migrate/issues/list
:Issues: http://code.google.com/p/sqlalchemy-migrate/
:Version: |release|


.. topic:: Overview

	Inspired by Ruby on Rails' migrations, SQLAlchemy Migrate provides a
	way to deal with database schema changes in SQLAlchemy_ projects.

	Migrate was started as part of `Google's Summer of Code`_ by Evan
	Rosson, mentored by Jonathan LaCour.

	The project was taken over by a small group of volunteers when Evan
	had no free time for the project. It is now hosted as a `Google Code
	project`_. During the hosting change the project was renamed to
	SQLAlchemy Migrate.

	Currently, sqlalchemy-migrate supports Python versions from 2.4 to 2.6.
	SQLAlchemy Migrate 0.6.0 supports SQLAlchemy both 0.5.x and 0.6.x branches.

.. warning::

	 Version **0.6** breaks backward compatability, please read :ref:`changelog <backwards-06>` for more info.


Download and Development
------------------------

.. toctree::

   download

.. _dialect-support:

Dialect support
---------------

+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+
| Operation / Dialect                                     | :ref:`sqlite <sqlite-d>` | :ref:`postgres <postgres-d>` | :ref:`mysql <mysql-d>` | :ref:`oracle  <oracle-d>` | :ref:`firebird <firebird-d>`  |   mssql            |
|                                                         |                          |                              |                        |                           |                               |                    |
+=========================================================+==========================+==============================+========================+===========================+===============================+====================+
| :ref:`ALTER TABLE RENAME TABLE <table-rename>`          | yes                      | yes                          | yes                    | yes                       | no                            |   not supported    |
|                                                         |                          |                              |                        |                           |                               |                    |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+
| :ref:`ALTER TABLE RENAME COLUMN <column-alter>`         | yes                      | yes                          | yes                    | yes                       | yes                           |   not supported    |
|                                                         | (workaround) [#1]_       |                              |                        |                           |                               |                    |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+
| :ref:`ALTER TABLE ADD COLUMN <column-create>`           | yes                      | yes                          | yes                    | yes                       | yes                           |   not supported    |
|                                                         | (with limitations) [#2]_ |                              |                        |                           |                               |                    |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+
| :ref:`ALTER TABLE DROP COLUMN <column-drop>`            | yes                      | yes                          | yes                    | yes                       | yes                           |   not supported    |
|                                                         | (workaround) [#1]_       |                              |                        |                           |                               |                    |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+
| :ref:`ALTER TABLE ALTER COLUMN <column-alter>`          | yes                      | yes                          | yes                    | yes                       | yes [#4]_                     |   not supported    |
|                                                         | (workaround) [#1]_       |                              |                        | (with limitations) [#3]_  |                               |                    |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+
| :ref:`ALTER TABLE ADD CONSTRAINT <constraint-tutorial>` | no                       | yes                          | yes                    | yes                       | yes                           |   not supported    |
|                                                         |                          |                              |                        |                           |                               |                    |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+
| :ref:`ALTER TABLE DROP CONSTRAINT <constraint-tutorial>`| no                       | yes                          | yes                    | yes                       | yes                           |   not supported    |
|                                                         |                          |                              |                        |                           |                               |                    |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+
| :ref:`RENAME INDEX <index-rename>`                      | no                       | yes                          | no                     | yes                       | yes                           |   not supported    |
|                                                         |                          |                              |                        |                           |                               |                    |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+-------------------------------+--------------------+


.. [#1] Table is renamed to temporary table, new table is created followed by INSERT statements.
.. [#2] Visit http://www.sqlite.org/lang_altertable.html for more information.
.. [#3] You can not change datatype or rename column if table has NOT NULL data, see http://blogs.x2line.com/al/archive/2005/08/30/1231.aspx for more information.
.. [#4] Changing nullable is not supported

Documentation
-------------

SQLAlchemy Migrate is split into two parts, database schema versioning (:mod:`migrate.versioning`) and
database migration management (:mod:`migrate.changeset`).
The versioning API is available as the :ref:`migrate <command-line-usage>` command.

.. toctree::

   versioning
   changeset
   tools

.. _`google's summer of code`: http://code.google.com/soc
.. _`Google Code project`: http://code.google.com/p/sqlalchemy-migrate
.. _sqlalchemy: http://www.sqlalchemy.org


API Documentation
------------------ 

.. toctree::

   api


Changelog
---------

.. toctree::

   changelog


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
