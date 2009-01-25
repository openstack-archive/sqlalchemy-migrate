Download and Development of SQLAlchemy Migrate
==============================================

Download
--------

SQLAlchemy-Migrate builds on SQLAlchemy_, so you should install that
first.

You can get the latest version of SQLAlchemy Migrate from the
`project's download page`_, the `cheese shop`_, or via easy_install_::

 easy_install sqlalchemy-migrate

You should now be able to use the *migrate* command from the command
line::

 migrate

This should list all available commands. *migrate help COMMAND* will
display more information about each command.

If you'd like to be notified when new versions of SQLAlchemy Migrate
are released, subscribe to `migrate-announce`_.

.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall#installing-easy-install
.. _sqlalchemy: http://www.sqlalchemy.org/download.html
.. _`project's download page`: http://code.google.com/p/sqlalchemy-migrate/downloads/list
.. _`cheese shop`: http://pypi.python.org/pypi/sqlalchemy-migrate
.. _`migrate-announce`: http://groups.google.com/group/migrate-announce

Development
-----------

Migrate's Subversion_ repository is at
http://sqlalchemy-migrate.googlecode.com/svn/

To get the latest trunk::

 svn co http://sqlalchemy-migrate.googlecode.com/svn/trunk

Patches should be submitted to the `issue tracker`_.

.. _subversion: http://subversion.tigris.org/
.. _issue tracker: http://code.google.com/p/sqlalchemy-migrate/issues/list
