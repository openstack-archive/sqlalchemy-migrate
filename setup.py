#!/usr/bin/python

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

try:
    import buildutils
except ImportError:
    pass

test_requirements = ['nose >= 0.10']
required_deps = ['sqlalchemy >= 0.5', 'decorator']

setup(
    name = "sqlalchemy-migrate",
    version = "0.5.4",
    packages = find_packages(exclude=['test*']),
    include_package_data = True,
    description = "Database schema migration for SQLAlchemy",
    long_description = """
Inspired by Ruby on Rails' migrations, Migrate provides a way to deal with database schema changes in `SQLAlchemy <http://sqlalchemy.org>`_ projects.

Migrate extends SQLAlchemy to have database changeset handling. It provides a database change repository mechanism which can be used from the command line as well as from inside python code.
""",

    install_requires = required_deps,
    tests_require = test_requirements,
    extras_require = {
        'docs' : ['sphinx >= 0.5'],
    },
    author = "Evan Rosson",
    author_email = "evan.rosson@gmail.com",
    url = "http://code.google.com/p/sqlalchemy-migrate/",
    maintainer = "Jan Dittberner",
    maintainer_email = "jan@dittberner.info",
    license = "MIT",

    entry_points = """
    [console_scripts]
    migrate = migrate.versioning.shell:main
    migrate-repository = migrate.versioning.migrate_repository:main
    """,
    test_suite = "nose.collector",
)
