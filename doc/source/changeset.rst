.. _changeset-system:
.. highlight:: python

**************************
Database schema migrations
**************************

.. currentmodule:: migrate.changeset.schema

Importing :mod:`migrate.changeset` adds some new methods to existing SQLAlchemy
objects, as well as creating functions of its own. Most operations can be done
either by a method or a function. Methods match SQLAlchemy's existing API and
are more intuitive when the object is available; functions allow one to make
changes when only the name of an object is available (for example, adding a
column to a table in the database without having to load that table into
Python).

Changeset operations can be used independently of SQLAlchemy Migrate's
:ref:`versioning <versioning-system>`.

For more information, see the API documentation for :mod:`migrate.changeset`.

.. _summary-changeset-api:

Here are some direct links to the relevent sections of the API documentations:


* :meth:`Create a column <ChangesetColumn.create>`
* :meth:`Drop a column <ChangesetColumn.drop>`
* :meth:`Alter a column <ChangesetColumn.alter>` (follow a link for list of supported changes)
* :meth:`Rename a table <ChangesetTable.rename>`
* :meth:`Rename an index <ChangesetIndex.rename>`
* :meth:`Create primary key constraint <migrate.changeset.constraint.PrimaryKeyConstraint>`
* :meth:`Drop primary key constraint <migrate.changeset.constraint.PrimaryKeyConstraint.drop>`
* :meth:`Create foreign key contraint <migrate.changeset.constraint.ForeignKeyConstraint.create>`
* :meth:`Drop foreign key constraint <migrate.changeset.constraint.ForeignKeyConstraint.drop>`
* :meth:`Create unique key contraint <migrate.changeset.constraint.UniqueConstraint.create>`
* :meth:`Drop unique key constraint <migrate.changeset.constraint.UniqueConstraint.drop>`
* :meth:`Create check key contraint <migrate.changeset.constraint.CheckConstraint.create>`
* :meth:`Drop check key constraint <migrate.changeset.constraint.CheckConstraint.drop>`


.. note::

  Many of the schema modification methods above take an ``alter_metadata``
  keyword parameter. This parameter defaults to `True`.

The following sections give examples of how to make various kinds of schema
changes.

Column
======

Given a standard SQLAlchemy table:

.. code-block:: python

    table = Table('mytable', meta,
        Column('id', Integer, primary_key=True),
    )
    table.create()

.. _column-create:

You can create a column with :meth:`~ChangesetColumn.create`:

.. code-block:: python

    col = Column('col1', String, default='foobar')
    col.create(table, populate_default=True)

    # Column is added to table based on its name
    assert col is table.c.col1

    # col1 is populated with 'foobar' because of `populate_default`

.. _column-drop:

.. note::

  You can pass `primary_key_name`, `index_name` and `unique_name` to the
  :meth:`~ChangesetColumn.create` method to issue ``ALTER TABLE ADD
  CONSTRAINT`` after changing the column.

  For multi columns constraints and other advanced configuration, check the
  :ref:`constraint tutorial <constraint-tutorial>`.

  .. versionadded:: 0.6.0

You can drop a column with :meth:`~ChangesetColumn.drop`:

.. code-block:: python

    col.drop()


.. _column-alter:

You can alter a column with :meth:`~ChangesetColumn.alter`:

.. code-block:: python

    col.alter(name='col2')

    # Renaming a column affects how it's accessed by the table object
    assert col is table.c.col2

    # Other properties can be modified as well
    col.alter(type=String(42), default="life, the universe, and everything", nullable=False)

    # Given another column object, col1.alter(col2), col1 will be changed to match col2
    col.alter(Column('col3', String(77), nullable=True))
    assert col.nullable
    assert table.c.col3 is col

.. deprecated:: 0.6.0
    Passing a :class:`~sqlalchemy.schema.Column` to
    :meth:`ChangesetColumn.alter` is deprecated. Pass in explicit
    parameters, such as `name` for a new column name and `type` for a
    new column type, instead. Do **not** include any parameters that
    are not changed.

.. _table-rename:

Table
=====

SQLAlchemy includes support for `creating and dropping`__ tables..

Tables can be renamed with :meth:`~ChangesetTable.rename`:

.. code-block:: python

    table.rename('newtablename')

.. __: http://www.sqlalchemy.org/docs/core/schema.html#creating-and-dropping-database-tables
.. currentmodule:: migrate.changeset.constraint


.. _index-rename:

Index
=====

SQLAlchemy supports `creating and dropping`__ indexes.

Indexes can be renamed using
:meth:`~migrate.changeset.schema.ChangesetIndex.rename`:

.. code-block:: python

    index.rename('newindexname')

.. __: http://www.sqlalchemy.org/docs/core/schema.html#indexes


.. _constraint-tutorial:

Constraint
==========

.. currentmodule:: migrate.changeset.constraint

SQLAlchemy supports creating or dropping constraints at the same time a table
is created or dropped. SQLAlchemy Migrate adds support for creating and
dropping :class:`~sqlalchemy.schema.PrimaryKeyConstraint`,
:class:`~sqlalchemy.schema.ForeignKeyConstraint`,
:class:`~sqlalchemy.schema.CheckConstraint` and
:class:`~sqlalchemy.schema.UniqueConstraint` constraints independently using
``ALTER TABLE`` statements.

The following rundowns are true for all constraints classes:

#. Make sure you import the relevant constraint class from :mod:`migrate` and
   not from :mod:`sqlalchemy`, for example:

   .. code-block:: python

        from migrate.changeset.constraint import ForeignKeyConstraint

   The classes in that module have the extra
   :meth:`~ConstraintChangeset.create` and :meth:`~ConstraintChangeset.drop`
   methods.

#. You can also use constraints as in SQLAlchemy. In this case passing table
   argument explicitly is required:

   .. code-block:: python

        cons = PrimaryKeyConstraint('id', 'num', table=self.table)

        # Create the constraint
        cons.create()

        # Drop the constraint
        cons.drop()

   You can also pass in :class:`~sqlalchemy.schema.Column` objects (and table
   argument can be left out):

   .. code-block:: python

        cons = PrimaryKeyConstraint(col1, col2)

#. Some dialects support ``CASCADE`` option when dropping constraints:

    .. code-block:: python

        cons = PrimaryKeyConstraint(col1, col2)

        # Create the constraint
        cons.create()

        # Drop the constraint
        cons.drop(cascade=True)

.. note::
    SQLAlchemy Migrate will try to guess the name of the constraints for
    databases, but if it's something other than the default, you'll need to
    give its name. Best practice is to always name your constraints. Note that
    Oracle requires that you state the name of the constraint to be created or
    dropped.


Examples
---------

Primary key constraints:

.. code-block:: python

    from migrate.changeset.constraint import PrimaryKeyConstraint

    cons = PrimaryKeyConstraint(col1, col2)

    # Create the constraint
    cons.create()

    # Drop the constraint
    cons.drop()

Foreign key constraints:

.. code-block:: python

    from migrate.changeset.constraint import ForeignKeyConstraint

    cons = ForeignKeyConstraint([table.c.fkey], [othertable.c.id])

    # Create the constraint
    cons.create()

    # Drop the constraint
    cons.drop()

Check constraints:

.. code-block:: python

    from migrate.changeset.constraint import CheckConstraint

    cons = CheckConstraint('id > 3', columns=[table.c.id])

    # Create the constraint
    cons.create()

    # Drop the constraint
    cons.drop()

Unique constraints:

.. code-block:: python

    from migrate.changeset.constraint import UniqueConstraint

    cons = UniqueConstraint('id', 'age', table=self.table)

    # Create the constraint
    cons.create()

    # Drop the constraint
    cons.drop()
