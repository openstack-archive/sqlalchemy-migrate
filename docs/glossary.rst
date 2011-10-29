.. _glossary:

********
Glossary
********

.. glossary::
    :sorted:

    repository
        A migration repository contains :command:`manage.py`, a configuration
        file (:file:`migrate.cfg`) and the database :term:`changeset` scripts
        which can be Python scripts or SQL files.

    changeset
        A set of instructions how upgrades and downgrades to or from a specific
        version of a database schema should be performed.

    ORM
        Abbreviation for "object relational mapper". An ORM is a tool that maps
        object hierarchies to database relations.

    version
        A version in SQLAlchemy migrate is defined by a :term:`changeset`.
        Versions may be numbered using ascending numbers or using timestamps
        (as of SQLAlchemy migrate release 0.7.2)
