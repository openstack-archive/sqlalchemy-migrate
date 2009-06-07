"""
   Provide exception classes for :mod:`migrate.versioning`
"""


class Error(Exception):
    """Error base class."""
    pass


class ApiError(Error):
    """Base class for API errors."""
    pass


class KnownError(ApiError):
    """A known error condition."""


class UsageError(ApiError):
    """A known error condition where help should be displayed."""


class ControlledSchemaError(Error):
    """Base class for controlled schema errors."""
    pass


class InvalidVersionError(ControlledSchemaError):
    """Invalid version number."""


class DatabaseNotControlledError(ControlledSchemaError):
    """Database should be under version control, but it's not."""


class DatabaseAlreadyControlledError(ControlledSchemaError):
    """Database shouldn't be under version control, but it is"""


class WrongRepositoryError(ControlledSchemaError):
    """This database is under version control by another repository."""


class NoSuchTableError(ControlledSchemaError):
    """The table does not exist."""
    pass


class PathError(Error):
    """Base class for path errors."""
    pass


class PathNotFoundError(PathError):
    """A path with no file was required; found a file."""
    pass


class PathFoundError(PathError):
    """A path with a file was required; found no file."""
    pass


class RepositoryError(Error):
    """Base class for repository errors."""
    pass


class InvalidRepositoryError(RepositoryError):
    """Invalid repository error."""
    pass


class ScriptError(Error):
    """Base class for script errors."""
    pass


class InvalidScriptError(ScriptError):
    """Invalid script error."""
    pass


class InvalidVersionError(Error):
    """Invalid version error."""
    pass
