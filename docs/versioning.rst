==================
migrate.versioning
==================

.. contents::

Project Setup
=============

Create a change repository
--------------------------

To begin, we'll need to create a *repository* for our project. Repositories are associated with a single database schema, and store collections of change scripts to manage that schema. The scripts in a repository may be applied to any number of databases.

Repositories each have a name. This name is used to identify the repository we're working with.

All work with repositories is done using the migrate command. Let's create our project's repository::

 % migrate create my_repository "Example project"

This creates an initially empty repository in the current directory at my_repository/ named Example project.

Version-control a database
--------------------------

Next, we need to create a database and declare it to be under version control. Information on a database's version is stored in the database itself; declaring a database to be under version control creates a table, named 'migrate_version' by default, and associates it with your repository.

The database is specified as a `SQLAlchemy database url`_.

.. _`sqlalchemy database url`: http://www.sqlalchemy.org/docs/dbengine.myt#dbengine_establishing

::

 % migrate version_control sqlite:///project.db my_repository

We can have any number of databases under this repository's version control.

Each schema has a version that Migrate manages. Each change script applied to the database increments this version number. You can see a database's current version::

 % migrate db_version sqlite:///project.db my_repository
 0 

A freshly versioned database begins at version 0 by default. This assumes the database is empty. (If this is a bad assumption, you can specify the version at the time the database is declared under version control, with the "version_control" command.) We'll see that creating and applying change scripts changes the database's version number.

Similarly, we can also see the latest version available in a repository with the command::

 % migrate version my_repository
 0

We've entered no changes so far, so our repository cannot upgrade a database past version 0. 

Project management script
-------------------------

Many commands need to know our project's database url and repository path - typing them each time is tedious. We can create a script for our project that remembers the database and repository we're using, and use it to perform commands::

 % migrate manage manage.py --repository=my_repository --url=sqlite:///project.db
 % python manage.py db_version
 0

The script manage.py was created. All commands we perform with it are the same as those performed with the 'migrate' tool, using the repository and database connection entered above.

Making schema changes
=====================

All changes to a database schema under version control should be done via change scripts - you should avoid schema modifications (creating tables, etc.) outside of change scripts. This allows you to determine what the schema looks like based on the version number alone, and helps ensure multiple databases you're working with are consistent.

Create a change script
----------------------
Our first change script will create a simple table::

 account = Table('account',meta,
     Column('id',Integer,primary_key=True),
     Column('login',String(40)),
     Column('passwd',String(40)),
 )

This table should be created in a change script. Let's create one::

 % python manage.py script script.py

This creates an empty change script at ``script.py``. Next, we'll edit this script to create our table.

Edit the change script
----------------------
Our change script defines two functions, currently empty: upgrade() and downgrade(). We'll fill those in::

 # script.py
 from sqlalchemy import *
 from migrate import *
 
 meta = BoundMetaData(migrate_engine)
 account = Table('account',meta,
     Column('id',Integer,primary_key=True),
     Column('login',String(40)),
     Column('passwd',String(40)),
 )
 
 def upgrade():
     account.create()
 
 def downgrade():
     account.drop()


As you might have guessed, upgrade() upgrades the database to the next version. This function should contain the changes we want to perform; here, we're creating a table. downgrade() should reverse changes made by upgrade(). You'll need to write both functions for every change script. (Well, you don't *have* to write downgrade(), but you won't be able to revert to an older version of the database or test your scripts without it.)

``from migrate import *`` imports a special SQLAlchemy engine named 'migrate_engine'. You should use this in your change scripts, rather than creating your own engine.

You should be very careful about importing files from the rest of your application, as your change scripts might break when your application changes. More about `writing scripts with consistent behavior`_.

Commit the change script
------------------------
Now that our script is done, we'll commit it to our repository. Committed scripts are considered 'done' - once a script is committed, it is moved into the repository, the change script file 'disappears', and your change script can be applied to a database. Once a script is committed, Migrate expects that the SQL the script generates will not change. (As mentioned above, this may be a bad assumption when importing files from your application!)

Change scripts should be tested before they are committed. Testing a script will run its upgrade() and downgrade() functions on a specified database; you can ensure the script runs without error. You should be testing on a test database - if something goes wrong here, you'll need to correct it by hand. If the test is successful, the database should appear unchanged after upgrade() and downgrade() run.

To test the script::
 
 % python manage.py test script.py
 Upgrading... done
 Downgrading... done
 Success

Our script runs on our database (``sqlite:///project.db``, as specified in manage.py) without any errors.

To commit the script::

 % python manage.py commit script.py

``script.py`` will be removed, and our repository's version will change::

 % python manage.py version
 1

Upgrade the database
--------------------
Now, we can apply this change script to our database::

 % python manage.py upgrade

This upgrades the database (``sqlite:///project.db``, as specified when we created manage.py above) to the latest available version. (We could also specify a version number if we wished, using the --version option.) We can see the database's version number has changed, and our table has been created::

 % python manage.py db_version
 1
 % sqlite3 project.db
 sqlite> .tables
 _version  account

Our account table was created - success! As our application evolves, we can create more change scripts using a similar process. 

Writing change scripts
======================

By default, change scripts may do anything any other SQLAlchemy program can do. 

Migrate extends SQLAlchemy with several operations used to change existing schemas - ie. ALTER TABLE stuff. See changeset_ documentation for details.

.. _changeset: changeset.html

Writing scripts with consistent behavior
----------------------------------------

Normally, it's important to write change scripts in a way that's independent of your application - the same SQL should be generated every time, despite any changes to your app's source code. You don't want your change scripts' behavior changing when your source code does. 

Consider the following example of what can go wrong (ie. what NOT to do):

Your application defines a table in the model.py file::

 # model.py
 from sqlalchemy import *

 meta = DynamicMetaData()
 table = Table('mytable',meta,
     Column('id',Integer,primary_key=True),
 )

...and uses this file to create a table in a change script::
 
 # changescript.py
 from sqlalchemy import *
 from migrate import *
 import model
 model.meta.connect(migrate_engine)

 def upgrade():
     model.table.create()
 def downgrade():
     model.table.drop()

This runs successfully the first time. But what happens if we change the table definition?

::

 table = Table('mytable',meta,
     Column('id',Integer,primary_key=True),
     Column('data',String(42)),
 )

We'll create a new column with a matching change script::

 # changescript2.py
 from sqlalchemy import *
 from migrate import *
 import model
 model.meta.connect(migrate_engine)

 def upgrade():
     model.table.data.create()
 def downgrade():
     model.table.data.drop()

This appears to run fine when upgrading an existing database - but the first script's behavior changed! Running all our change scripts on a new database will result in an error - the first script creates the table based on the new definition, with both columns; the second cannot add the column because it already exists. 

To avoid the above problem, you should copy-paste your table definition into each change script rather than importing parts of your application. 

Writing for a specific database
-------------------------------

Sometimes you need to write code for a specific database. Migrate scripts can run under any database, however - the engine you're given might belong to any database. Use engine.name to get the name of the database you're working with::

 >>> from sqlalchemy import *
 >>> from migrate import *
 >>> 
 >>> engine = create_engine('sqlite:///:memory:')
 >>> engine.name
 'sqlite'

.sql scripts
------------

You might prefer to write your change scripts in SQL, as .sql files, rather than as Python scripts. Migrate can work with that::

 % migrate version my_repository
 10
 % migrate commit upgrade.sql my_repository postgres upgrade
 % migrate version my_repository
 11
 % migrate commit downgrade.sql my_repository postgres downgrade 11
 % migrate version my_repository
 11

Here, two scripts are given, one for each *operation*, or function defined in a Python change script - upgrade and downgrade. Both are specified to run with Postgres databases - we can commit more for different databases if we like. Any database defined by SQLAlchemy may be used here - ex. sqlite, postgres, oracle, mysql...

For every .sql script added after the first, we must specify the version - if you don't enter a version to commit, Migrate assumes that commit is for a new version.

Python API
==========
All commands available from the command line are also available for your Python scripts by importing `migrate.versioning.api`_. See the `migrate.versioning.api`_ documentation for a list of functions; function names match equivalent shell commands. You can use this to help integrate Migrate with your existing update process. 

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
