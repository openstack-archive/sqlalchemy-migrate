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


class LogSqlError(Error):
    """A SQLError, with a traceback of where that statement was logged."""

    def __init__(self, sqlerror, entry):
        Exception.__init__(self)
        self.sqlerror = sqlerror
        self.entry = entry

    def __str__(self):
        ret = "SQL error in statement: \n%s\n"%(str(self.entry))
        ret += "Traceback from change script:\n"
        ret += ''.join(traceback.format_list(self.entry.traceback))
        ret += str(self.sqlerror)
        return ret


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
