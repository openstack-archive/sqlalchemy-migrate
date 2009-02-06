.. _versioning-system:

**************************
Database schema versioning
**************************

SQLAlchemy migrate provides the :mod:`migrate.versioning` API that is
also available as the :command:`migrate` command.

.. program:: migrate

Project Setup
=============

.. _create_change_repository:

Create a change repository
--------------------------

To begin, we'll need to create a *repository* for our
project. Repositories are associated with a single database schema,
and store collections of change scripts to manage that schema. The
scripts in a repository may be applied to any number of databases.

Repositories each have a name. This name is used to identify the
repository we're working with.

All work with repositories is done using the migrate command. Let's
create our project's repository::

 % migrate create my_repository "Example project"

This creates an initially empty repository in the current directory at
my_repository/ named Example project. The repository directory
contains a sub directory versions that will store the schema versions,
a configuration file :file:`migrate.cfg` that contains
:ref:`repository configuration <repository_configuration>`, a
:file:`README` file containing information that the directory is an
sqlalchemy-migrate repository and a script :file:`manage.py` that has
the same functionality as the :command:`migrate` command but is
preconfigured with the repository.

Version-control a database
--------------------------

Next, we need to create a database and declare it to be under version
control. Information on a database's version is stored in the database
itself; declaring a database to be under version control creates a
table, named 'migrate_version' by default, and associates it with your
repository.

The database is specified as a `SQLAlchemy database url`_.

.. _`sqlalchemy database url`:
 http://www.sqlalchemy.org/docs/05/dbengine.html#create-engine-url-arguments

::

 % python my_repository/manage.py version_control sqlite:///project.db

We can have any number of databases under this repository's version
control.

Each schema has a version that SQLAlchemy Migrate manages. Each change
script applied to the database increments this version number. You can
see a database's current version::

 % python my_repository/manage.py db_version sqlite:///project.db
 0 

A freshly versioned database begins at version 0 by default. This
assumes the database is empty. (If this is a bad assumption, you can
specify the version at the time the database is declared under version
control, with the "version_control" command.) We'll see that creating
and applying change scripts changes the database's version number.

Similarly, we can also see the latest version available in a
repository with the command::

 % python my_repository/manage.py version
 0

We've entered no changes so far, so our repository cannot upgrade a
database past version 0.

Project management script
-------------------------

Many commands need to know our project's database url and repository
path - typing them each time is tedious. We can create a script for
our project that remembers the database and repository we're using,
and use it to perform commands::

 % migrate manage manage.py --repository=my_repository --url=sqlite:///project.db
 % python manage.py db_version
 0

The script manage.py was created. All commands we perform with it are
the same as those performed with the 'migrate' tool, using the
repository and database connection entered above. The difference
between the script :file:`manage.py` in the current directory and the
script inside the repository is, that the one in the current directory
has the database URL preconfigured.

Making schema changes
=====================

All changes to a database schema under version control should be done
via change scripts - you should avoid schema modifications (creating
tables, etc.) outside of change scripts. This allows you to determine
what the schema looks like based on the version number alone, and
helps ensure multiple databases you're working with are consistent.

Create a change script
----------------------

Our first change script will create a simple table::

 account = Table('account',meta,
     Column('id',Integer,primary_key=True),
     Column('login',String(40)),
     Column('passwd',String(40)),
 )

This table should be created in a change script. Let's create one::

 % python manage.py script "Add account table"

This creates an empty change script at
:file:`my_repository/versions/001_Add_account_table.py`. Next, we'll
edit this script to create our table.

Edit the change script
----------------------

Our change script defines two functions, currently empty:
``upgrade()`` and ``downgrade()``. We'll fill those in::

  from sqlalchemy import *
  from migrate import *
  
  meta = MetaData(migrate_engine)
  account = Table('account', meta,
                  Column('id', Integer, primary_key=True),
                  Column('login', String(40)),
                  Column('passwd', String(40)),
                  )
  
  def upgrade():
      account.create()
  
  def downgrade():
      account.drop()

As you might have guessed, upgrade() upgrades the database to the next
version. This function should contain the changes we want to perform;
here, we're creating a table. downgrade() should reverse changes made
by upgrade(). You'll need to write both functions for every change
script. (Well, you don't *have* to write downgrade(), but you won't be
able to revert to an older version of the database or test your
scripts without it.)

``from migrate import *`` imports a special SQLAlchemy engine named
'migrate_engine'. You should use this in your change scripts, rather
than creating your own engine.

You should be very careful about importing files from the rest of your
application, as your change scripts might break when your application
changes. More about `writing scripts with consistent behavior`_.

Test the change script
------------------------

Change scripts should be tested before they are committed. Testing a
script will run its upgrade() and downgrade() functions on a specified
database; you can ensure the script runs without error. You should be
testing on a test database - if something goes wrong here, you'll need
to correct it by hand. If the test is successful, the database should
appear unchanged after upgrade() and downgrade() run.

To test the script:

.. code-block:: none
 
 % python manage.py test
 Upgrading... done
 Downgrading... done
 Success

Our script runs on our database (``sqlite:///project.db``, as
specified in manage.py) without any errors.

Our repository's version now is::

 % python manage.py version
 1

Upgrade the database
--------------------

Now, we can apply this change script to our database::

 % python manage.py upgrade
 0 -> 1... done

This upgrades the database (``sqlite:///project.db``, as specified
when we created manage.py above) to the latest available version. (We
could also specify a version number if we wished, using the --version
option.) We can see the database's version number has changed, and our
table has been created:

.. code-block:: none

 % python manage.py db_version
 1
 % sqlite3 project.db
 sqlite> .tables
 account migrate_version

Our account table was created - success! As our application evolves,
we can create more change scripts using a similar process.

Writing change scripts
======================

By default, change scripts may do anything any other SQLAlchemy
program can do.

SQLAlchemy Migrate extends SQLAlchemy with several operations used to
change existing schemas - ie. ``ALTER TABLE`` stuff. See
:ref:`changeset <changeset-system>` documentation for details.


Writing scripts with consistent behavior
----------------------------------------

Normally, it's important to write change scripts in a way that's
independent of your application - the same SQL should be generated
every time, despite any changes to your app's source code. You don't
want your change scripts' behavior changing when your source code
does.

Consider the following example of what can go wrong (i.e. what NOT to
do):

Your application defines a table in the model.py file:

::

 from sqlalchemy import *
 
 meta = MetaData()
 table = Table('mytable',meta,
     Column('id',Integer,primary_key=True),
 )

...and uses this file to create a table in a change script:

::
 
 from sqlalchemy import *
 from migrate import *
 import model
 model.meta.connect(migrate_engine)

 def upgrade():
     model.table.create()
 def downgrade():
     model.table.drop()

This runs successfully the first time. But what happens if we change
the table definition?

::

 table = Table('mytable',meta,
     Column('id',Integer,primary_key=True),
     Column('data',String(42)),
 )

We'll create a new column with a matching change script::

 from sqlalchemy import *
 from migrate import *
 import model
 model.meta.connect(migrate_engine)

 def upgrade():
     model.table.data.create()
 def downgrade():
     model.table.data.drop()

This appears to run fine when upgrading an existing database - but the
first script's behavior changed! Running all our change scripts on a
new database will result in an error - the first script creates the
table based on the new definition, with both columns; the second
cannot add the column because it already exists.

To avoid the above problem, you should copy-paste your table
definition into each change script rather than importing parts of your
application.

Writing for a specific database
-------------------------------

Sometimes you need to write code for a specific database. Migrate
scripts can run under any database, however - the engine you're given
might belong to any database. Use engine.name to get the name of the
database you're working with::

 >>> from sqlalchemy import *
 >>> from migrate import *
 >>> 
 >>> engine = create_engine('sqlite:///:memory:')
 >>> engine.name
 'sqlite'

.sql scripts
------------

You might prefer to write your change scripts in SQL, as .sql files,
rather than as Python scripts. SQLAlchemy-migrate can work with that::

 % python manage.py version
 1
 % python manage.py script_sql postgres

This creates two scripts
:file:`my_repository/versions/002_postgresql_upgrade.sql` and
:file:`my_repository/versions/002_postgresql_downgrade.sql`, one for
each *operation*, or function defined in a Python change script -
upgrade and downgrade. Both are specified to run with Postgres
databases - we can add more for different databases if we like. Any
database defined by SQLAlchemy may be used here - ex. sqlite,
postgres, oracle, mysql...

Experimental commands
=====================

Some interesting new features to create SQLAlchemy db models from
existing databases and vice versa were developed by Christian Simms
during the development of SQLAlchemy-migrate 0.4.5. These features are
roughly documented in a `thread in migrate-users`_.

.. _`thread in migrate-users`:
 http://groups.google.com/group/migrate-users/browse_thread/thread/a5605184e08abf33#msg_85c803b71b29993f

Here are the commands' descriptions as given by ``migrate help <command>``:

- ``compare_model_to_db``: Compare the current model (assumed to be a
  module level variable of type sqlalchemy.MetaData) against the
  current database.
- ``create_model``: Dump the current database as a Python model to
  stdout.
- ``make_update_script_for_model``: Create a script changing the old
  Python model to the new (current) Python model, sending to stdout.
- ``upgrade_db_from_model``: Modify the database to match the
  structure of the current Python model. This also sets the db_version
  number to the latest in the repository.

As this sections headline says: These features are EXPERIMENTAL. Take
the necessary arguments to the commands from the output of ``migrate
help <command>``.

Python API
==========

.. currentmodule:: migrate.versioning

All commands available from the command line are also available for
your Python scripts by importing :mod:`migrate.versioning`. See the
:mod:`migrate.versioning` documentation for a list of functions;
function names match equivalent shell commands. You can use this to
help integrate SQLAlchemy Migrate with your existing update process.

For example, the following commands are similar:
 
*From the command line*::

 % migrate help help
 /usr/bin/migrate help COMMAND

     Displays help on a given command.

*From Python*::

 import migrate.versioning.api
 migrate.versioning.api.help('help')
 # Output:
 # %prog help COMMAND
 # 
 #     Displays help on a given command.
  

.. _migrate.versioning.api: module-migrate.versioning.api.html

.. _repository_configuration:

Repository configuration
========================

SQLAlchemy-migrate repositories can be configured in their migrate.cfg
files. The initial configuration is performed by the `migrate create`
call explained in :ref:`Create a change repository
<create_change_repository>`. The following options are available
currently:

- `repository_id` Used to identify which repository this database is
  versioned under. You can use the name of your project.
- `version_table` The name of the database table used to track the
  schema version. This name shouldn't already be used by your
  project. If this is changed once a database is under version
  control, you'll need to change the table name in each database too.
- `required_dbs` When committing a change script, SQLAlchemy-migrate
  will attempt to generate the sql for all supported databases;
  normally, if one of them fails - probably because you don't have
  that database installed - it is ignored and the commit continues,
  perhaps ending successfully. Databases in this list MUST compile
  successfully during a commit, or the entire commit will fail. List
  the databases your application will actually be using to ensure your
  updates to that database work properly. This must be a list;
  example: `['postgres','sqlite']`
