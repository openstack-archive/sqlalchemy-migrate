Repository migration (0.4.5 -> 0.5.4)
================================================

.. index:: repository migration

:command:`migrate_repository.py` should be
used to migrate your repository from a version before 0.4.5 of
SQLAlchemy migrate to the current version.

.. module:: migrate.versioning.migrate_repository
   :synopsis: Tool for migrating pre 0.4.5 repositories to current layout

Running :command:`migrate_repository.py` is as easy as:

 :samp:`migrate_repository.py {repository_directory}`
