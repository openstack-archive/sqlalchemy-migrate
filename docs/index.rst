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

.. warning::

	 **0.5.5** release breaks backward compatability, please read :ref:`changelog <backwards-055>` for more info.

Download and Development of SQLAlchemy Migrate
----------------------------------------------

.. toctree::

   download

Documentation
-------------

SQLAlchemy is split into two parts, database schema versioning and
database changeset management. This is represented by two python
packages :mod:`migrate.versioning` and :mod:`migrate.changeset`. The
versioning API is available as the :command:`migrate` command.

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
