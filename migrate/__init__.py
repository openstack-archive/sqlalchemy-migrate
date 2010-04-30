"""
   SQLAlchemy migrate provides two APIs :mod:`migrate.versioning` for
   database schema version and repository management and
   :mod:`migrate.changeset` that allows to define database schema changes
   using Python.
"""

class MigrateDeprecationWarning(DeprecationWarning):
    """Warning for deprecated features in Migrate"""
