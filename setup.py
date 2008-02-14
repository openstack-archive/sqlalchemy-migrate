#!/usr/bin/python
from setuptools import setup,find_packages

# Pudge
try:
    import buildutils
except ImportError:
    pass

setup(
    name = "sqlalchemy-migrate",
    version = "0.4.1dev",
    packages = find_packages(exclude=['test*']),
    scripts = ['shell/migrate'],
    include_package_data = True,
    description = "Database schema migration for SQLAlchemy",
    long_description = """
Inspired by Ruby on Rails' migrations, Migrate provides a way to deal with database schema changes in `SQLAlchemy <http://sqlalchemy.org>`_ projects.

Migrate extends SQLAlchemy to have database changeset handling. It provides a database change repository mechanism which can be used from the command line as well as from inside python code.
""",

    install_requires = ['sqlalchemy >= 0.3.10'],
    setup_requires = ['py >= 0.9.0-beta'],
    dependency_links = [
        "http://codespeak.net/download/py/",
    ],

    author = "Evan Rosson",
    author_email = "evan.rosson@gmail.com",
    url = "http://code.google.com/p/sqlalchemy-migrate/",
    maintainer = "Jan Dittberner",
    maintainer_email = "jan@dittberner.info",
    license = "MIT",

    test_suite = "py.test.cmdline.main",
)
