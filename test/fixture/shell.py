from pathed import *
import os
import shutil
import sys

class Shell(Pathed):
    """Base class for command line tests"""
    def execute(self,command,*p,**k):
        """Return the fd of a command; can get output (stdout/err) and exitcode"""
        # We might be passed a file descriptor for some reason; if so, just return it
        if type(command) is file:
            return command
        # Redirect stderr to stdout
        # This is a bit of a hack, but I've not found a better way
        fd=os.popen(command+' 2>&1',*p,**k)
        return fd
    def output_and_exitcode(self,*p,**k):
        fd=self.execute(*p,**k)
        output = fd.read()
        exitcode = fd.close()
        if k.pop('emit',False):
            print output
        return (output,exitcode)
    def exitcode(self,*p,**k):
        """Execute a command and return its exit code
        ...without printing its output/errors
        """
        ret = self.output_and_exitcode(*p,**k)
        return ret[1]

    def assertFailure(self,*p,**k):
        output,exitcode = self.output_and_exitcode(*p,**k)
        assert (exitcode), output
    def assertSuccess(self,*p,**k):
        output,exitcode = self.output_and_exitcode(*p,**k)
        #self.assert_(not exitcode, output)
        assert (not exitcode), output
