"""
   This module provides exception classes.
"""


class Error(Exception):
    """
    Changeset error.
    """
    pass


class NotSupportedError(Error):
    """
    Not supported error.
    """
    pass


class InvalidConstraintError(Error):
    """
    Invalid constraint error.
    """
    pass
