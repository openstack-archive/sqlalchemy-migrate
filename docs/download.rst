=======
Migrate
=======

Download
========

Migrate builds on SQLAlchemy_, so you should install that first. 

You can get the latest version of Migrate from the `cheese shop`_, or via easy_install_::

 easy_install migrate

You should now be able to use the *migrate* command from the command line::

 migrate

This should list all available commands. *migrate help COMMAND* will display more information about each command. 

If you'd like to be notified when new versions of migrate are released, subscribe to `migrate-announce`_.

.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall#installing-easy-install
.. _sqlalchemy: http://www.sqlalchemy.org/download.myt
.. _`cheese shop`: http://www.python.org/pypi/migrate
.. _`migrate-announce`: http://groups.google.com/group/migrate-announce

Development
===========

Migrate's Subversion_ repository is at http://erosson.com/migrate/svn/

To get the latest trunk::

 svn co http://erosson.com/migrate/svn/migrate/trunk

Patches should be submitted as Trac tickets.

.. _subversion: http://subversion.tigris.org/
