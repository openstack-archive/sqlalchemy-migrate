Module :mod:`migrate.changeset` -- Schema changes
=================================================

Module :mod:`migrate.changeset` -- Schema migration API
-------------------------------------------------------

.. automodule:: migrate.changeset
   :members:
   :synopsis: Database changeset management

Module :mod:`ansisql <migrate.changeset.ansisql>` -- Standard SQL implementation
------------------------------------------------------------------------------------

.. automodule:: migrate.changeset.ansisql
   :members:
   :member-order: groupwise
   :synopsis: Standard SQL implementation for altering database schemas

Module :mod:`constraint <migrate.changeset.constraint>` -- Constraint schema migration API
---------------------------------------------------------------------------------------------

.. automodule:: migrate.changeset.constraint
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: groupwise
   :synopsis: Standalone schema constraint objects

Module :mod:`databases <migrate.changeset.databases>` -- Database specific schema migration
-----------------------------------------------------------------------------------------------

.. automodule:: migrate.changeset.databases
   :members:
   :synopsis: Database specific changeset implementations

.. _mysql-d:

Module :mod:`mysql <migrate.changeset.databases.mysql>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. automodule:: migrate.changeset.databases.mysql
   :members:
   :synopsis: MySQL database specific changeset implementations

.. _firebird-d:

Module :mod:`firebird <migrate.changeset.databases.firebird>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. automodule:: migrate.changeset.databases.firebird
   :members:
   :synopsis: Firebird database specific changeset implementations

.. _oracle-d:

Module :mod:`oracle <migrate.changeset.databases.oracle>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. automodule:: migrate.changeset.databases.oracle
   :members:
   :synopsis: Oracle database specific changeset implementations

.. _postgres-d:

Module :mod:`postgres <migrate.changeset.databases.postgres>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: migrate.changeset.databases.postgres
   :members:
   :synopsis: PostgreSQL database specific changeset implementations

.. _sqlite-d:

Module :mod:`sqlite <migrate.changeset.databases.sqlite>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: migrate.changeset.databases.sqlite
   :members:
   :synopsis: SQLite database specific changeset implementations

Module :mod:`visitor <migrate.changeset.databases.visitor>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: migrate.changeset.databases.visitor
   :members:

Module :mod:`schema <migrate.changeset.schema>` -- Additional API to SQLAlchemy for migrations
----------------------------------------------------------------------------------------------

.. automodule:: migrate.changeset.schema
   :members:
   :synopsis: Schema changeset handling functions


Module :mod:`migrate.versioning` -- Database versioning and repository management
==================================================================================

.. automodule:: migrate.versioning
   :members:
   :synopsis: Database version and repository management

.. _versioning-api:

Module :mod:`api <migrate.versioning.api>` -- Python API commands
-----------------------------------------------------------------

.. automodule:: migrate.versioning.api
   :members:
   :synopsis: External API for :mod:`migrate.versioning`


Module :mod:`genmodel <migrate.versioning.genmodel>` -- ORM Model generator
-------------------------------------------------------------------------------------

.. automodule:: migrate.versioning.genmodel
   :members:
   :synopsis: Python database model generator and differencer

Module :mod:`pathed <migrate.versioning.pathed>` -- Path utilities
----------------------------------------------------------------------------

.. automodule:: migrate.versioning.pathed
   :members:
   :synopsis: File/Directory handling class

Module :mod:`repository <migrate.versioning.repository>` -- Repository management
-------------------------------------------------------------------------------------

.. automodule:: migrate.versioning.repository
   :members:
   :synopsis: SQLAlchemy migrate repository management
   :member-order: groupwise

Module :mod:`schema <migrate.versioning.schema>` -- Migration upgrade/downgrade
----------------------------------------------------------------------------------

.. automodule:: migrate.versioning.schema
   :members:
   :member-order: groupwise
   :synopsis: Database schema management

Module :mod:`schemadiff <migrate.versioning.schemadiff>` -- ORM Model differencing
-------------------------------------------------------------------------------------

.. automodule:: migrate.versioning.schemadiff
   :members:
   :synopsis: Database schema and model differencing

Module :mod:`script <migrate.versioning.script>` -- Script actions
--------------------------------------------------------------------

.. automodule:: migrate.versioning.script.base
   :synopsis: Script utilities
   :member-order: groupwise
   :members:

.. automodule:: migrate.versioning.script.py
   :members:
   :member-order: groupwise
   :inherited-members:
   :show-inheritance:

.. automodule:: migrate.versioning.script.sql
   :members:
   :member-order: groupwise
   :show-inheritance:
   :inherited-members:

Module :mod:`shell <migrate.versioning.shell>` -- CLI interface
------------------------------------------------------------------

.. automodule:: migrate.versioning.shell
   :members:
   :synopsis: Shell commands

Module :mod:`util <migrate.versioning.util>` -- Various utility functions
--------------------------------------------------------------------------

.. automodule:: migrate.versioning.util
   :members:
   :synopsis: Utility functions

Module :mod:`version <migrate.versioning.version>` -- Versioning management
-----------------------------------------------------------------------------

.. automodule:: migrate.versioning.version
   :members:
   :member-order: groupwise
   :synopsis: Version management

Module :mod:`exceptions <migrate.exceptions>` -- Exception definitions
======================================================================

.. automodule:: migrate.exceptions
   :members:
   :synopsis: Migrate exception classes

