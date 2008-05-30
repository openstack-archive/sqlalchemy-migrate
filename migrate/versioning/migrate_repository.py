''' Script to migrate repository. This shouldn't use any other migrate modules, so that it can work in any version. '''

import os, os.path, sys


def usage():
    
    print '''Usage: %(prog)s repository-to-migrate

Upgrade your repository to the new flat format.

NOTE: You should probably make a backup before running this.
''' % {'prog': sys.argv[0]}

    raise SystemExit(1)


def deleteFile(filepath):
    print '    Deleting file: %s' % filepath
    os.remove(filepath)

def moveFile(src, tgt):
    print '    Moving file %s to %s' % (src, tgt)
    if os.path.exists(tgt):
        raise Exception('Cannot move file %s because target %s already exists' % (src, tgt))
    os.rename(src, tgt)

def deleteDirectory(dirpath):
    print '    Deleting directory: %s' % dirpath
    os.rmdir(dirpath)
    

def migrate_repository(repos):
    print 'Migrating repository at: %s to new format' % repos
    versions = '%s/versions' % repos
    dirs = os.listdir(versions)
    numdirs = [ int(dir) for dir in dirs if dir.isdigit() ]  # Only use int's in list.
    numdirs.sort()  # Sort list.
    for dir in numdirs:
        origdir = '%s/%s' % (versions, dir)
        print '  Working on directory: %s' % origdir
        files = os.listdir(origdir)
        files.sort()
        for file in files:
            
            # Delete compiled Python files.
            if file.endswith('.pyc') or file.endswith('.pyo'):
                deleteFile('%s/%s' % (origdir, file))
                
            # Delete empty __init__.py files.
            origfile = '%s/__init__.py' % origdir
            if os.path.exists(origfile) and len(open(origfile).read()) == 0:
                deleteFile(origfile)

            # Move sql upgrade scripts.
            if file.endswith('.sql'):
                version, dbms, op, ext = file.split('.', 3)
                origfile = '%s/%s' % (origdir, file)
                # For instance:  2.postgres.upgrade.sql -> 002_postgres_upgrade.sql
                tgtfile = '%s/%03d_%s_%s.sql' % (versions, int(version), dbms, op)
                moveFile(origfile, tgtfile)

        # Move Python upgrade script.
        pyfile = '%s.py' % dir
        pyfilepath = '%s/%s' % (origdir, pyfile)
        if os.path.exists(pyfilepath):
            tgtfile = '%s/%03d.py' % (versions, int(dir))
            moveFile(pyfilepath, tgtfile)

        # Try to remove directory. Will fail if it's not empty.
        deleteDirectory(origdir)
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
    migrate_repository(sys.argv[1])

