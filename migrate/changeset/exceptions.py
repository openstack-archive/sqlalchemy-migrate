"""
   This module provides exception classes.
"""


class Error(Exception):
    """
    Changeset error.
    """


class NotSupportedError(Error):
    """
    Not supported error.
    """


class InvalidConstraintError(Error):
    """
    Invalid constraint error.
    """

class MigrateDeprecationWarning(DeprecationWarning):
    """
    Warning for deprecated features in Migrate
    """
