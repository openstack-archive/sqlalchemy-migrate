''' Script to migrate repository. This shouldn't use any other migrate modules, so that it can work in any version. '''

import os, sys


def usage():
    
    print '''Usage: %(prog)s repository-to-migrate

Upgrade your repository to the new flat format.

NOTE: You should probably make a backup before running this.
''' % {'prog': sys.argv[0]}

    raise SystemExit(1)


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
        pass # finish TODO xxx
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
    migrate_repository(sys.argv[1])

