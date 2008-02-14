=======
Migrate
=======

Download
========

SQLAlchemy-Migrate builds on SQLAlchemy_, so you should install that first. 

You can get the latest version of SQLAlchemy Migrate from the `cheese shop`_, or via easy_install_::

 easy_install sqlalchemy-migrate

You should now be able to use the *migrate* command from the command line::

 migrate

This should list all available commands. *migrate help COMMAND* will display more information about each command. 

If you'd like to be notified when new versions of SQLAlchemy Migrate are released, subscribe to `migrate-announce`_.

.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall#installing-easy-install
.. _sqlalchemy: http://www.sqlalchemy.org/download.myt
.. _`cheese shop`: http://www.python.org/pypi/sqlalchemy-migrate
.. _`migrate-announce`: http://groups.google.com/group/migrate-announce

Development
===========

Migrate's Subversion_ repository is at http://sqlalchemy-migrate.googlecode.com/svn/

To get the latest trunk::

 svn co http://sqlalchemy-migrate.googlecode.com/svn/trunk

Patches should be submitted as Trac tickets.

.. _subversion: http://subversion.tigris.org/
