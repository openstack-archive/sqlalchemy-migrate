#!/usr/bin/python

import os

import setuptools

required_deps = ['SQLAlchemy >= 0.6', 'decorator', 'Tempita >= 0.4']
readme_file = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'README'))

setuptools.setup(
    name = "sqlalchemy-migrate",
    version = "0.7.3",
    packages = setuptools.find_packages(exclude=["migrate.tests*"]),
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
