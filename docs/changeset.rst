.. _changeset-system:
.. highlight:: python

******************
Database changeset
******************

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

 table = Table('mytable', meta,
    Column('id', Integer, primary_key=True),
 )
 table.create()

Create a column::

 col = Column('col1', String)
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
.. currentmodule:: migrate.changeset.constraint

Index
=====

SQLAlchemy supports `index create/drop`_

Rename an index, given an SQLAlchemy ``Index`` object::

 index.rename('newindexname')

.. _`index create/drop`: http://www.sqlalchemy.org/docs/05/metadata.html#indexes

Constraint
==========

SQLAlchemy supports creating/dropping constraints at the same time a table is created/dropped. SQLAlchemy Migrate adds support for creating/dropping :class:`PrimaryKeyConstraint`/:class:`ForeignKeyConstraint`/:class:`CheckConstraint`/:class:`UniqueConstraint` constraints independently. (as ALTER TABLE statements).

The following rundowns are true for all constraints classes:

1. Make sure you do ``from migrate.changeset import *`` after SQLAlchemy imports since `migrate` does not patch SA's Constraints.

2. You can also use Constraints as in SQLAlchemy. In this case passing table argument explicitly is required::

	cons = PrimaryKeyConstraint('id', 'num', table=self.table)

	# Create the constraint
	cons.create()

	# Drop the constraint
	cons.drop()

or you can pass column objects (and table argument can be left out).

3. Some dialects support CASCADE option when dropping constraints::

	cons = PrimaryKeyConstraint(col1, col2)

	# Create the constraint
	cons.create()

	# Drop the constraint
	cons.drop(cascade=True)


.. note::
	 SQLAlchemy Migrate will try to guess the name of the constraints for databases, but if it's something other than the default, you'll need to give its name. Best practice is to always name your constraints. Note that Oracle requires that you state the name of the constraint to be created/dropped.


Examples
---------

Primary key constraints::

 from migrate.changeset import *

 cons = PrimaryKeyConstraint(col1, col2)

 # Create the constraint
 cons.create()

 # Drop the constraint
 cons.drop()

Foreign key constraints::

 from migrate.changeset import *

 cons = ForeignKeyConstraint([table.c.fkey], [othertable.c.id])

 # Create the constraint
 cons.create()

 # Drop the constraint
 cons.drop()

Check constraints::

	from migrate.changeset import *

	cons = CheckConstraint('id > 3', columns=[table.c.id])

	# Create the constraint
	cons.create()

	# Drop the constraint
	cons.drop()

Unique constraints::

	from migrate.changeset import *

	cons = UniqueConstraint('id', 'age', table=self.table)

	# Create the constraint
	cons.create()

	# Drop the constraint
	cons.drop()
