
class Error(Exception):
    pass
class ApiError(Error):
    pass
class KnownError(ApiError):
    """A known error condition"""
class UsageError(ApiError):
    """A known error condition where help should be displayed"""

class ControlledSchemaError(Error):
    pass
class InvalidVersionError(ControlledSchemaError):
    """Invalid version number"""
class DatabaseNotControlledError(ControlledSchemaError):
    """Database shouldn't be under vc, but it is"""
class DatabaseAlreadyControlledError(ControlledSchemaError):
    """Database should be under vc, but it's not"""
class WrongRepositoryError(ControlledSchemaError):
    """This database is under version control by another repository"""
class NoSuchTableError(ControlledSchemaError):
    pass

class LogSqlError(Error):
    """A SQLError, with a traceback of where that statement was logged"""
    def __init__(self,sqlerror,entry):
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
    pass
class PathNotFoundError(PathError):
    """A path with no file was required; found a file"""
    pass
class PathFoundError(PathError):
    """A path with a file was required; found no file"""
    pass

class RepositoryError(Error):
    pass
class InvalidRepositoryError(RepositoryError):
    pass

class ScriptError(Error):
    pass
class InvalidScriptError(ScriptError):
    pass

class InvalidVersionError(Error):
    pass

