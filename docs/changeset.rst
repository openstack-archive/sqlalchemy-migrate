.. _changeset-system:

**********************
Database changeset API
**********************

.. currentmodule:: migrate.changeset

Importing :mod:`migrate.changeset` adds some new methods to existing
SA objects, as well as creating functions of its own. Most operations
can be done either by a method or a function. Methods match
SQLAlchemy's existing API and are more intuitive when the object is
available; functions allow one to make changes when only the name of
an object is available (for example, adding a column to a table in the
database without having to load that table into Python).

Changeset operations can be used independently of SQLAlchemy Migrate's
:ref:`versioning <versioning-system>`.

For more information, see the generated documentation for
:mod:`migrate.changeset`.

Column
======

Given a standard SQLAlchemy table::

 table = Table('mytable',meta,
    Column('id',Integer,primary_key=True),
 )
 table.create()

Create a column::

 col = Column('col1',String)
 col.create(table)

 # Column is added to table based on its name
 assert col is table.c.col1

Drop a column (Not supported by SQLite_)::

 col.drop()


Alter a column (Not supported by SQLite_)::

 col.alter(name='col2')

 # Renaming a column affects how it's accessed by the table object
 assert col is table.c.col2

 # Other properties can be modified as well
 col.alter(type=String(42),
     default="life, the universe, and everything",
     nullable=False,
 )

 # Given another column object, col1.alter(col2), col1 will be changed to match col2
 col.alter(Column('col3',String(77),nullable=True))
 assert col.nullable
 assert table.c.col3 is col

.. _sqlite: http://www.sqlite.org/lang_altertable.html

Table
=====

SQLAlchemy supports `table create/drop`_

Rename a table::

 table.rename('newtablename')

.. _`table create/drop`: http://www.sqlalchemy.org/docs/05/metadata.html#creating-and-dropping-database-tables

Index
=====

SQLAlchemy supports `index create/drop`_

Rename an index, given an SQLAlchemy ``Index`` object::

 index.rename('newindexname')

.. _`index create/drop`: http://www.sqlalchemy.org/docs/05/metadata.html#indexes

Constraint
==========

SQLAlchemy supports creating/dropping constraints at the same time a table is created/dropped. SQLAlchemy Migrate adds support for creating/dropping primary/foreign key constraints independently.

Primary key constraints::

 cons = PrimaryKeyConstraint(col1,col2)
 # Create the constraint
 cons.create()
 # Drop the constraint
 cons.drop()

Note that Oracle requires that you state the name of the primary key constraint to be created/dropped. SQLAlchemy Migrate will try to guess the name of the PK constraint for other databases, but if it's something other than the default, you'll need to give its name::

 PrimaryKeyConstraint(col1,col2,name='my_pk_constraint')

Foreign key constraints::

 cons = ForeignKeyConstraint([table.c.fkey], [othertable.c.id])
 # Create the constraint
 cons.create()
 # Drop the constraint
 cons.drop()

Names are specified just as with primary key constraints::
 
 ForeignKeyConstraint([table.c.fkey], [othertable.c.id],name='my_fk_constraint')
