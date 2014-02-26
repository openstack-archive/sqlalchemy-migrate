.. _versioning-system:
.. currentmodule:: migrate.versioning
.. highlight:: console

***********************************
Database schema versioning workflow
***********************************

SQLAlchemy migrate provides the :mod:`migrate.versioning` API that is
also available as the :ref:`migrate <command-line-usage>` command.

Purpose of this package is frontend for migrations. It provides commands to
manage migrate :term:`repository` and database selection as well as script
versioning.


Project setup
=============

.. _create_change_repository:

Create a change repository
--------------------------

To begin, we'll need to create a :term:`repository` for our project.

All work with repositories is done using the :ref:`migrate
<command-line-usage>` command. Let's create our project's repository::

 $ migrate create my_repository "Example project"

This creates an initially empty :term:`repository` relative to current
directory at :file:`my_repository/` named `Example project`.

The :term:`repository` directory contains a sub directory :file:`versions` that
will store the :ref:`schema versions <changeset-system>`, a configuration file
:file:`migrate.cfg` that contains :ref:`repository configuration
<repository_configuration>` and a script :ref:`manage.py
<project_management_script>` that has the same functionality as the
:ref:`migrate <command-line-usage>` command but is preconfigured with
repository specific parameters.

.. note::

    Repositories are associated with a single database schema, and store
    collections of change scripts to manage that schema. The scripts in a
    :term:`repository` may be applied to any number of databases. Each
    :term:`repository` has an unique name. This name is used to identify the
    :term:`repository` we're working with.


Version control a database
--------------------------

Next we need to declare database to be under version control. Information on a
database's version is stored in the database itself; declaring a database to be
under version control creates a table named **migrate_version** and associates
it with your :term:`repository`.

The database is specified as a `SQLAlchemy database url`_.

.. _`sqlalchemy database url`:
  http://www.sqlalchemy.org/docs/core/engines.html#database-urls

The :option:`version_control` command assigns a specified database with a
:term:`repository`::

 $ python my_repository/manage.py version_control sqlite:///project.db my_repository

We can have any number of databases under this :term:`repository's
<repository>` version control.

Each schema has a :term:`version` that SQLAlchemy Migrate manages. Each change
script applied to the database increments this version number. You can retrieve
a database's current :term:`version`::

 $ python my_repository/manage.py db_version sqlite:///project.db my_repository
 0

A freshly versioned database begins at version 0 by default. This assumes the
database is empty or does only contain schema elements (tables, views,
constraints, indices, ...) that will not be affected by the changes in the
:term:`repository`. (If this is a bad assumption, you can specify the
:term:`version` at the time the database is put under version control, with the
:option:`version_control` command.) We'll see that creating and applying change
scripts changes the database's :term:`version` number.

Similarly, we can also see the latest :term:`version` available in a
:term:`repository` with the command::

 $ python my_repository/manage.py version my_repository
 0

We've entered no changes so far, so our :term:`repository` cannot upgrade a
database past version 0.

Project management script
-------------------------

.. _project_management_script:

Many commands need to know our project's database url and :term:`repository`
path - typing them each time is tedious. We can create a script for our project
that remembers the database and :term:`repository` we're using, and use it to
perform commands::

 $ migrate manage manage.py --repository=my_repository --url=sqlite:///project.db
 $ python manage.py db_version
 0

The script :file:`manage.py` was created. All commands we perform with it are
the same as those performed with the :ref:`migrate <command-line-usage>` tool,
using the :term:`repository` and database connection entered above. The
difference between the script :file:`manage.py` in the current directory and
the script inside the repository is, that the one in the current directory has
the database URL preconfigured.

.. note::

   Parameters specified in manage.py should be the same as in :ref:`versioning
   api <versioning-api>`. Preconfigured parameter should just be omitted from
   :ref:`migrate <command-line-usage>` command.


Making schema changes
=====================

All changes to a database schema under version control should be done via
change scripts - you should avoid schema modifications (creating tables, etc.)
outside of change scripts. This allows you to determine what the schema looks
like based on the version number alone, and helps ensure multiple databases
you're working with are consistent.

Create a change script
----------------------

Our first change script will create a simple table

.. code-block:: python

    account = Table(
        'account', meta,
        Column('id', Integer, primary_key=True),
        Column('login', String(40)),
        Column('passwd', String(40)),
    )

This table should be created in a change script. Let's create one::

 $ python manage.py script "Add account table"

This creates an empty change script at
:file:`my_repository/versions/001_Add_account_table.py`. Next, we'll
edit this script to create our table.


Edit the change script
----------------------

Our change script predefines two functions, currently empty:
:py:func:`upgrade` and :py:func:`downgrade`. We'll fill those in:

.. code-block:: python

    from sqlalchemy import Table, Column, Integer, String, MetaData

    meta = MetaData()

    account = Table(
        'account', meta,
        Column('id', Integer, primary_key=True),
        Column('login', String(40)),
        Column('passwd', String(40)),
    )


    def upgrade(migrate_engine):
        meta.bind = migrate_engine
        account.create()


    def downgrade(migrate_engine):
        meta.bind = migrate_engine
        account.drop()

.. note::

    The generated script contains * imports from sqlalchemy and migrate. You
    should tailor the imports to fit your actual demand.

As you might have guessed, :py:func:`upgrade` upgrades the database to the next
version. This function should contain the :ref:`schema changes
<changeset-system>` we want to perform (in our example we're creating a
table).

:py:func:`downgrade` should reverse changes made by :py:func:`upgrade`. You'll
need to write both functions for every change script. (Well, you don't *have*
to write downgrade, but you won't be able to revert to an older version of the
database or test your scripts without it.) If you really don't want to support
downgrades it is a good idea to raise a :py:class:`NotImplementedError` or some
equivalent custom exception. If you let :py:func:`downgrade` pass silently you
might observe undesired behaviour for subsequent downgrade operations if
downgrading multiple :term:`versions <version>`.


.. note::

    As you can see, **migrate_engine** is passed to both functions.  You should
    use this in your change scripts, rather than creating your own engine.

.. warning::

    You should be very careful about importing files from the rest of your
    application, as your change scripts might break when your application
    changes. Read more about `writing scripts with consistent behavior`_.


Test the change script
------------------------

Change scripts should be tested before they are committed. Testing a script
will run its :func:`upgrade` and :func:`downgrade` functions on a specified
database; you can ensure the script runs without error. You should be testing
on a test database - if something goes wrong here, you'll need to correct it by
hand. If the test is successful, the database should appear unchanged after
:func:`upgrade` and :func:`downgrade` run.

To test the script::

 $ python manage.py test
 Upgrading... done
 Downgrading... done
 Success

Our script runs on our database (:file:`sqlite:///project.db`, as specified in
:file:`manage.py`) without any errors.

Our :term:`repository's <repository>` :term:`version` is::

 $ python manage.py version
 1

.. note::

    Due to #41 the database must be exactly one :term:`version` behind the
    :term:`repository` :term:`version`.

.. _production testing warning:

.. warning::

    The :option:`test` command executes actual scripts, be sure you are *NOT*
    doing this on production database.

    If you need to test production changes you should:

        #. get a dump of your production database
        #. import the dump into an empty database
        #. run :option:`test` or :option:`upgrade` on that copy


Upgrade the database
--------------------

Now, we can apply this change script to our database::

 $ python manage.py upgrade
 0 -> 1...
 done

This upgrades the database (:file:`sqlite:///project.db`, as specified when we
created :file:`manage.py` above) to the latest available :term:`version`. (We
could also specify a version number if we wished, using the :option:`--version`
option.) We can see the database's :term:`version` number has changed, and our
table has been created::

 $ python manage.py db_version
 1
 $ sqlite3 project.db
 sqlite> .tables
 account migrate_version
 sqlite> .schema account
 CREATE TABLE account (
    id INTEGER NOT NULL,
    login VARCHAR(40),
    passwd VARCHAR(40),
    PRIMARY KEY (id)
 );

Our account table was created - success!

Modifying existing tables
-------------------------

After we have initialized the database schema we now want to add another Column
to the `account` table that we already have in our schema.

First start a new :term:`changeset` by the commands learned above::

 $ python manage.py script "Add email column"

This creates a new :term:`changeset` template. Edit the resulting script
:file:`my_repository/versions/002_Add_email_column.py`:

.. code-block:: python

    from sqlalchemy import Table, MetaData, String, Column


    def upgrade(migrate_engine):
        meta = MetaData(bind=migrate_engine)
        account = Table('account', meta, autoload=True)
        emailc = Column('email', String(128))
        emailc.create(account)


    def downgrade(migrate_engine):
        meta = MetaData(bind=migrate_engine)
        account = Table('account', meta, autoload=True)
        account.c.email.drop()

As we can see in this example we can (and should) use SQLAlchemy's schema
reflection (autoload) mechanism to reference existing schema objects. We could
have defined the table objects as they are expected before upgrade or downgrade
as well but this would have been more work and is not as convenient.

We can now apply the changeset to :file:`sqlite:///project.db`::

 $ python manage.py upgrade
 1 -> 2...
 done

and get the following expected result::

 $ sqlite3 project.db
 sqlite> .schema account
 CREATE TABLE account (
    id INTEGER NOT NULL,
    login VARCHAR(40),
    passwd VARCHAR(40), email VARCHAR(128),
    PRIMARY KEY (id)
 );


Writing change scripts
======================

As our application evolves, we can create more change scripts using a similar
process.

By default, change scripts may do anything any other SQLAlchemy program can do.

SQLAlchemy Migrate extends SQLAlchemy with several operations used to change
existing schemas - ie. ``ALTER TABLE`` stuff. See :ref:`changeset
<changeset-system>` documentation for details.


Writing scripts with consistent behavior
----------------------------------------

Normally, it's important to write change scripts in a way that's independent of
your application - the same SQL should be generated every time, despite any
changes to your app's source code. You don't want your change scripts' behavior
changing when your source code does.

.. warning::

    **Consider the following example of what NOT to do**

    Let's say your application defines a table in the :file:`model.py` file:

    .. code-block:: python

        from sqlalchemy import *

        meta = MetaData()
        table = Table('mytable', meta,
            Column('id', Integer, primary_key=True),
        )

    ... and uses this file to create a table in a change script:

    .. code-block:: python

        from sqlalchemy import *
        from migrate import *
        import model

        def upgrade(migrate_engine):
            model.meta.bind = migrate_engine

        def downgrade(migrate_engine):
            model.meta.bind = migrate_engine
            model.table.drop()

    This runs successfully the first time. But what happens if we change the
    table definition in :file:`model.py`?

    .. code-block:: python

        from sqlalchemy import *

        meta = MetaData()
        table = Table('mytable', meta,
            Column('id', Integer, primary_key=True),
            Column('data', String(42)),
        )

    We'll create a new column with a matching change script

    .. code-block:: python

        from sqlalchemy import *
        from migrate import *
        import model

        def upgrade(migrate_engine):
            model.meta.bind = migrate_engine
            model.table.create()

        def downgrade(migrate_engine):
            model.meta.bind = migrate_engine
            model.table.drop()

    This appears to run fine when upgrading an existing database - but the
    first script's behavior changed! Running all our change scripts on a new
    database will result in an error - the first script creates the table based
    on the new definition, with both columns; the second cannot add the column
    because it already exists.

    To avoid the above problem, you should use SQLAlchemy schema reflection as
    shown above or copy-paste your table definition into each change script
    rather than importing parts of your application.

    .. note::
        Sometimes it is enough to just reflect tables with SQLAlchemy instead
        of copy-pasting - but remember, explicit is better than implicit!


Writing for a specific database
-------------------------------

Sometimes you need to write code for a specific database. Migrate scripts can
run under any database, however - the engine you're given might belong to any
database. Use engine.name to get the name of the database you're working with

.. code-block:: python

 >>> from sqlalchemy import *
 >>> from migrate import *
 >>>
 >>> engine = create_engine('sqlite:///:memory:')
 >>> engine.name
 'sqlite'


Writings .sql scripts
---------------------

You might prefer to write your change scripts in SQL, as .sql files, rather
than as Python scripts. SQLAlchemy-migrate can work with that::

 $ python manage.py version
 1
 $ python manage.py script_sql postgresql

This creates two scripts
:file:`my_repository/versions/002_postgresql_upgrade.sql` and
:file:`my_repository/versions/002_postgresql_downgrade.sql`, one for each
*operation*, or function defined in a Python change script - upgrade and
downgrade. Both are specified to run with PostgreSQL databases - we can add
more for different databases if we like. Any database defined by SQLAlchemy may
be used here - ex. sqlite, postgresql, oracle, mysql...


.. _command-line-usage:

Command line usage
==================

.. currentmodule:: migrate.versioning.shell

:command:`migrate` command is used for API interface. For list of commands and
help use::

 $ migrate --help

:command:`migrate` command executes :func:`main` function.
For ease of usage, generate your own :ref:`project management script
<project_management_script>`, which calls :func:`main
<migrate.versioning.shell.main>` function with keywords arguments. You may want
to specify `url` and `repository` arguments which almost all API functions
require.

If api command looks like::

 $ migrate downgrade URL REPOSITORY VERSION [--preview_sql|--preview_py]

and you have a project management script that looks like

.. code-block:: python

    from migrate.versioning.shell import main

    main(url='sqlite://', repository='./project/migrations/')

you have first two slots filed, and command line usage would look like::

    # preview Python script
    $ migrate downgrade 2 --preview_py

    # downgrade to version 2
    $ migrate downgrade 2

.. versionchanged:: 0.5.4
    Command line parsing refactored: positional parameters usage

Whole command line parsing was rewriten from scratch with use of OptionParser.
Options passed as kwargs to :func:`~migrate.versioning.shell.main` are now
parsed correctly. Options are passed to commands in the following priority
(starting from highest):

- optional (given by :option:`--some_option` in commandline)
- positional arguments
- kwargs passed to :func:`migrate.versioning.shell.main`


Python API
==========

.. currentmodule:: migrate.versioning.api

All commands available from the command line are also available for
your Python scripts by importing :mod:`migrate.versioning.api`. See the
:mod:`migrate.versioning.api` documentation for a list of functions;
function names match equivalent shell commands. You can use this to
help integrate SQLAlchemy Migrate with your existing update process.

For example, the following commands are similar:

*From the command line*::

 $ migrate help help
 /usr/bin/migrate help COMMAND

     Displays help on a given command.

*From Python*

.. code-block:: python

 import migrate.versioning.api
 migrate.versioning.api.help('help')
 # Output:
 # %prog help COMMAND
 #
 #     Displays help on a given command.


.. _migrate.versioning.api: module-migrate.versioning.api.html

.. _repository_configuration:


Experimental commands
=====================

Some interesting new features to create SQLAlchemy db models from existing
databases and vice versa were developed by Christian Simms during the
development of SQLAlchemy-migrate 0.4.5. These features are roughly documented
in a `thread in migrate-users`_.

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

As this sections headline says: These features are *EXPERIMENTAL*. Take the
necessary arguments to the commands from the output of ``migrate
help <command>``.


Repository configuration
========================

SQLAlchemy-migrate :term:`repositories <repository>` can be configured in their
:file:`migrate.cfg` files.  The initial configuration is performed by the
`migrate create` call explained in :ref:`Create a change repository
<create_change_repository>`. The following options are available currently:

- :option:`repository_id` Used to identify which repository this database is
  versioned under. You can use the name of your project.
- :option:`version_table` The name of the database table used to track the
  schema version. This name shouldn't already be used by your project. If this
  is changed once a database is under version control, you'll need to change
  the table name in each database too.
- :option:`required_dbs` When committing a change script, SQLAlchemy-migrate
  will attempt to generate the sql for all supported databases; normally, if
  one of them fails - probably because you don't have that database installed -
  it is ignored and the commit continues, perhaps ending successfully.
  Databases in this list MUST compile successfully during a commit, or the
  entire commit will fail. List the databases your application will actually be
  using to ensure your updates to that database work properly. This must be a
  list; example: `['postgres', 'sqlite']`
- :option:`use_timestamp_numbering` When creating new change scripts, Migrate
  will stamp the new script with a version number. By default this is
  latest_version + 1. You can set this to 'true' to tell Migrate to use the UTC
  timestamp instead.

  .. versionadded:: 0.7.2

.. _custom-templates:


Customize templates
===================

Users can pass ``templates_path`` to API functions to provide customized
templates path.  Path should be a collection of templates, like
``migrate.versioning.templates`` package directory.

One may also want to specify custom themes. API functions accept
``templates_theme`` for this purpose (which defaults to `default`)

Example::

 /home/user/templates/manage $ ls
 default.py_tmpl
 pylons.py_tmpl

 /home/user/templates/manage $ migrate manage manage.py --templates_path=/home/user/templates --templates_theme=pylons

.. versionadded:: 0.6.0
