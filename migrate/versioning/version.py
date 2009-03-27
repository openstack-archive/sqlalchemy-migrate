from migrate.versioning import exceptions,pathed,script
import os,re,shutil



class VerNum(object):
    """A version number"""
    _instances=dict()
    def __new__(cls,value):
        val=str(value)
        if val not in cls._instances:
            cls._instances[val] = super(VerNum,cls).__new__(cls)
        ret = cls._instances[val]
        return ret
    def __init__(self,value):
        self.value=str(int(value))
        if self < 0:
            raise ValueError("Version number cannot be negative")
    def __repr__(self):
        return str(self.value)
    def __str__(self):
        return str(self.value)
    def __int__(self):
        return int(self.value)
    def __add__(self,value):
        ret=int(self)+int(value)
        return VerNum(ret)
    def __sub__(self,value):
        return self+(int(value)*-1)
    def __cmp__(self,value):
        return int(self)-int(value)


def strToFilename(s):
    s = s.replace(' ', '_').replace('"', '_').replace("'", '_')
    while '__' in s:
        s = s.replace('__', '_')
    return s
        

class Collection(pathed.Pathed):
    """A collection of versioning scripts in a repository"""
    FILENAME_WITH_VERSION = re.compile(r'^(\d+).*')
    def __init__(self,path):
        super(Collection,self).__init__(path)
        
        # Create temporary list of files, allowing skipped version numbers.
        files = os.listdir(path)
        if '1' in files:
            raise Exception('It looks like you have a repository in the old format (with directories for each version). Please convert repository before proceeding.')
        tempVersions = dict()
        for filename in files:
            match = self.FILENAME_WITH_VERSION.match(filename)
            if match:
                num = int(match.group(1))
                tempVersions.setdefault(num, []).append(filename)
            else:
                pass  # Must be a helper file or something, let's ignore it.

        # Create the versions member where the keys are VerNum's and the values are Version's.
        self.versions=dict()
        for num, files in tempVersions.items():
            self.versions[VerNum(num)] = Version(num, path, files)
        self.latest = max([VerNum(0)] + self.versions.keys())  # calculate latest version

    def version_path(self,ver):
        return os.path.join(self.path,str(ver))
    
    def version(self,vernum=None):
        if vernum is None:
            vernum = self.latest
        return self.versions[VerNum(vernum)]

    def getNewVersion(self):
        ver = self.latest+1
        # No change scripts exist for 0 (even though it's a valid version)
        if ver <= 0:
            raise exceptions.InvalidVersionError()
        self.latest = ver
        return ver
    
    def createNewVersion(self, description, **k):
        ver = self.getNewVersion()
        extra = strToFilename(description)
        if extra:
            if extra == '_':
                extra = ''
            elif not extra.startswith('_'):
                extra = '_%s' % extra
        filename = '%03d%s.py' % (ver, extra)
        filepath = self.version_path(filename)
        if os.path.exists(filepath):
            raise Exception('Script already exists: %s' % filepath)
        else:
            script.PythonScript.create(filepath)
        self.versions[ver] = Version(ver, self.path, [filename])
        
    def createNewSQLVersion(self, database, **k):
	# Determine version number to use.
	# fix from Issue 29
	ver = self.getNewVersion()
	self.versions[ver] = Version(ver, self.path, [])

        # Create new files.
        for op in ('upgrade', 'downgrade'):
            filename = '%03d_%s_%s.sql' % (ver, database, op)
            filepath = self.version_path(filename)
            if os.path.exists(filepath):
                raise Exception('Script already exists: %s' % filepath)
            else:
                open(filepath, "w").close()
            self.versions[ver]._add_script(filepath)
        
    @classmethod
    def clear(cls):
        super(Collection,cls).clear()
    

class extensions:
    """A namespace for file extensions"""
    py='py'
    sql='sql'


class Version(object):  # formerly inherit from: (pathed.Pathed):
    """A single version in a repository
    """
    def __init__(self,vernum,path,filelist):
        # Version must be numeric
        try:
            self.version=VerNum(vernum)
        except:
            raise exceptions.InvalidVersionError(vernum)
        # Collect scripts in this folder
        self.sql = dict()
        self.python = None

        for script in filelist:
            # skip __init__.py, because we assume that it's
            # just there to mark the package
            if script == '__init__.py':
                continue
            self._add_script(os.path.join(path,script))
    
    def script(self,database=None,operation=None):
        #if database is None and operation is None:
        #    return self._script_py()
        #print database,operation,self.sql
        
        try:
            # Try to return a .sql script first
            return self._script_sql(database,operation)
        except KeyError:
            pass  # No .sql script exists
            
        try:
            # Try to return the default .sql script
            return self._script_sql('default',operation)
        except KeyError:
            pass  # No .sql script exists

        ret = self._script_py()

        assert ret is not None
        return ret
    def _script_py(self):
        return self.python
    def _script_sql(self,database,operation):
        return self.sql[database][operation]

    @classmethod
    def create(cls,path):
        os.mkdir(path)
        # craete the version as a proper Python package
        initfile = os.path.join(path, "__init__.py")
        if not os.path.exists(initfile):
            # just touch the file
            open(initfile, "w").close()
        try:
            ret=cls(path)
        except:
            os.rmdir(path)
            raise
        return ret

    def _add_script(self,path):
        if path.endswith(extensions.py):
            self._add_script_py(path)
        elif path.endswith(extensions.sql):
            self._add_script_sql(path)

    SQL_FILENAME = re.compile(r'^(\d+)_([^_]+)_([^_]+).sql')
    def _add_script_sql(self,path):
        match = self.SQL_FILENAME.match(os.path.basename(path))
        if match:
            version, dbms, op = match.group(1), match.group(2), match.group(3)
        else:
            raise exceptions.ScriptError("Invalid sql script name %s"%path)

        # File the script into a dictionary
        dbmses = self.sql
        if dbms not in dbmses:
            dbmses[dbms] = dict()
        ops = dbmses[dbms]
        ops[op] = script.SqlScript(path)
    def _add_script_py(self,path):
        if self.python is not None:
            raise Exception('You can only have one Python script per version, but you have: %s and %s' % (self.python, path))
        self.python = script.PythonScript(path)

    def _rm_ignore(self,path):
        """Try to remove a path; ignore failure"""
        try:
            os.remove(path)
        except OSError:
            pass

