SQLAlchemy migrate tools
========================

The most commonly used tool is the :ref:`migrate <command-line-usage>`.

.. index:: repository migration

There is a second tool :command:`migrate_repository.py` that may be
used to migrate your repository from a version before 0.4.5 of
SQLAlchemy migrate to the current version.

.. module:: migrate.versioning.migrate_repository
   :synopsis: Tool for migrating pre 0.4.5 repositories to current layout

Running :command:`migrate_repository.py` is as easy as:

 :samp:`migrate_repository.py {repository_directory}`
