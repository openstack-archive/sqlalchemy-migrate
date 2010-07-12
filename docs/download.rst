Download
--------

You can get the latest version of SQLAlchemy Migrate from the
`project's download page`_, the `cheese shop`_, pip_ or via easy_install_::

    easy_install sqlalchemy-migrate

or::

    pip install sqlalchemy-migrate

You should now be able to use the *migrate* command from the command
line::

 migrate

This should list all available commands. ``migrate help COMMAND`` will
display more information about each command.

If you'd like to be notified when new versions of SQLAlchemy Migrate
are released, subscribe to `migrate-announce`_.

.. _pip: http://pip.openplans.org/
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall#installing-easy-install
.. _sqlalchemy: http://www.sqlalchemy.org/download.html
.. _`project's download page`: http://code.google.com/p/sqlalchemy-migrate/downloads/list
.. _`cheese shop`: http://pypi.python.org/pypi/sqlalchemy-migrate
.. _`migrate-announce`: http://groups.google.com/group/migrate-announce

Development
-----------

Migrate's Mercurial_ repository is located at `Google Code`_.

To get the latest trunk::

    hg clone http://sqlalchemy-migrate.googlecode.com/hg/

Patches should be submitted to the `issue tracker`_.

We use `hudson`_ Continuous Integration tool to help us run tests on all databases that migrate supports.

.. _Mercurial: http://www.mercurial-scm.org/
.. _Google Code: http://sqlalchemy-migrate.googlecode.com/hg/
.. _issue tracker: http://code.google.com/p/sqlalchemy-migrate/issues/list
.. _hudson: http://hudson.fubar.si
