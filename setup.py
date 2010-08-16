#!/usr/bin/python

import os

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

required_deps = ['SQLAlchemy >= 0.5', 'decorator', 'Tempita >= 0.4', 'setuptools']
readme_file = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'README'))

setup(
    name = "sqlalchemy-migrate",
    version = "0.6.1",
    packages = find_packages(exclude=["migrate.tests*"]),
    include_package_data = True,
    description = "Database schema migration for SQLAlchemy",
    long_description = readme_file.read(),
    install_requires = required_deps,
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
