:mod:`migrate` - SQLAlchemy Migrate (schema change management)
==============================================================

.. module:: migrate
.. moduleauthor:: Evan Rosson

:Author: Evan Rosson
:Maintainer: Domen Kozar <domenNO@SPAMdev.si>
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
	SQLAlchemy >=0.5 is supported only.

.. warning::

	 Version **0.5.5** breaks backward compatability, please read :ref:`changelog <backwards-055>` for more info.


Download and Development
------------------------

.. toctree::

   download


Dialect support
---------------

+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+
| Operation / Dialect                                     | :ref:`sqlite <sqlite-d>` | :ref:`postgres <postgres-d>` | :ref:`mysql <mysql-d>` | :ref:`oracle  <oracle-d>` | firebird | mssql |
|                                                         |                          |                              |                        |                           |          |       |
+=========================================================+==========================+==============================+========================+===========================+==========+=======+
| :ref:`ALTER TABLE RENAME TABLE <table-rename>`          | yes                      | yes                          | yes                    | yes                       |          |       |
|                                                         |                          |                              |                        |                           |          |       |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+
| :ref:`ALTER TABLE RENAME COLUMN <column-alter>`         | yes                      | yes                          | yes                    | yes                       |          |       |
|                                                         | (workaround) [#1]_       |                              |                        |                           |          |       |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+
| :ref:`ALTER TABLE ADD COLUMN <column-create>`           | yes                      | yes                          | yes                    | yes                       |          |       |
|                                                         | (with limitations) [#2]_ |                              |                        |                           |          |       |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+
| :ref:`ALTER TABLE DROP COLUMN <column-drop>`            | yes                      | yes                          | yes                    | yes                       |          |       |
|                                                         | (workaround) [#1]_       |                              |                        |                           |          |       |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+
| :ref:`ALTER TABLE ALTER COLUMN <column-alter>`          | no                       | yes                          | yes                    | yes                       |          |       |
|                                                         |                          |                              |                        | (with limitations) [#3]_  |          |       |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+
| :ref:`ALTER TABLE ADD CONSTRAINT <constraint-tutorial>` | no                       | yes                          | yes                    | yes                       |          |       |
|                                                         |                          |                              |                        |                           |          |       |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+
| :ref:`ALTER TABLE DROP CONSTRAINT <constraint-tutorial>`| no                       | yes                          | yes                    | yes                       |          |       |
|                                                         |                          |                              |                        |                           |          |       |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+
| :ref:`RENAME INDEX <index-rename>`                      | no                       | yes                          | no                     | yes                       |          |       |
|                                                         |                          |                              |                        |                           |          |       |
+---------------------------------------------------------+--------------------------+------------------------------+------------------------+---------------------------+----------+-------+


.. [#1] Table is renamed to temporary table, new table is created followed by INSERT statements.
.. [#2] Visit http://www.sqlite.org/lang_altertable.html for more information.
.. [#3] You can not change datatype or rename column if table has NOT NULL data, see http://blogs.x2line.com/al/archive/2005/08/30/1231.aspx for more information.
 

Documentation
-------------

SQLAlchemy is split into two parts, database schema versioning and
database changeset management. This is represented by two python
packages :mod:`migrate.versioning` and :mod:`migrate.changeset`. The
versioning API is available as the :ref:`migrate <command-line-usage>` command.

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
