"""The migrate command-line tool.
"""
import sys
from migrate.versioning.base import *
from optparse import OptionParser,Values
from migrate.versioning import api,exceptions
import inspect

alias = dict(
    s=api.script,
    ci=api.commit,
    vc=api.version_control,
    dbv=api.db_version,
    v=api.version,
)
def alias_setup():
    global alias
    for key,val in alias.iteritems():
        setattr(api,key,val)
alias_setup()

class ShellUsageError(Exception):
    def die(self,exitcode=None):
        usage="""%%prog COMMAND ...
        Available commands:
        %s

        Enter "%%prog help COMMAND" for information on a particular command.
        """
        usage = usage.replace("\n"+" "*8,"\n")
        commands = list(api.__all__)
        commands.sort()
        commands = '\n'.join(map((lambda x:'\t'+x),commands))
        message = usage%commands
        try:
            message = message.replace('%prog',sys.argv[0])
        except IndexError:
            pass

        if self.args[0] is not None:
            message += "\nError: %s\n"%str(self.args[0])
            if exitcode is None:
                exitcode = 1
        if exitcode is None:
            exitcode = 0
        die(message,exitcode)

def die(message,exitcode=1):
    if message is not None:
        sys.stderr.write(message)
        sys.stderr.write("\n")
    raise SystemExit(int(exitcode))

kwmap = dict(
    v='verbose',
    d='debug',
    f='force',
)

def kwparse(arg):
    ret = arg.split('=',1)
    if len(ret) == 1:
        # No value specified (--kw, not --kw=stuff): use True
        ret = [ret[0],True]
    return ret

def parse_arg(arg,argnames):
    global kwmap
    if arg.startswith('--'):
        # Keyword-argument; either --keyword or --keyword=value
        kw,val = kwparse(arg[2:])
    elif arg.startswith('-'):
        # Short form of a keyword-argument; map it to a keyword
        try:
            parg = kwmap.get(arg)
        except KeyError:
            raise ShellUsageError("Invalid argument: %s"%arg)
        kw,val = kwparse(parg)
    else:
        # Simple positional parameter
        val = arg
        try:
            kw = argnames.pop(0)
        except IndexError,e:
            raise ShellUsageError("Too many arguments to command")
    return kw,val

def parse_args(*args,**kwargs):
    """Map positional arguments to keyword-args"""
    args=list(args)
    try:
        cmdname = args.pop(0)
    except IndexError:
        # No command specified: no error message; just show usage
        raise ShellUsageError(None)

    # Special cases: -h and --help should act like 'help'
    if cmdname == '-h' or cmdname == '--help':
        cmdname = 'help'

    cmdfunc = getattr(api,cmdname,None)
    if cmdfunc is None or cmdname.startswith('_'):
        raise ShellUsageError("Invalid command %s"%cmdname)

    argnames, p,k, defaults = inspect.getargspec(cmdfunc)
    argnames_orig = list(argnames)

    for arg in args:
        kw,val = parse_arg(arg,argnames)
        kwargs[kw] = val

    if defaults is not None:
        num_defaults = len(defaults)
    else:
        num_defaults = 0
    req_argnames = argnames_orig[:len(argnames_orig)-num_defaults]
    for name in req_argnames:
        if name not in kwargs:
            raise ShellUsageError("Too few arguments: %s not specified"%name)
    
    return cmdfunc,kwargs

def main(argv=None,**kwargs):
    if argv is None:
        argv = list(sys.argv[1:])

    try:
        command, kwargs = parse_args(*argv,**kwargs)
    except ShellUsageError,e:
        e.die()

    try:
        ret = command(**kwargs)
        if ret is not None:
            print ret
    except exceptions.UsageError,e:
        e = ShellUsageError(e.args[0])
        e.die()
    except exceptions.KnownError,e:
        die(e.args[0])

if __name__=="__main__":
    main()
