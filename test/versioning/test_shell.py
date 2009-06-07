#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import traceback
from types import FileType
from StringIO import StringIO

from sqlalchemy import MetaData,Table

from migrate.versioning.repository import Repository
from migrate.versioning import genmodel, shell, api
from migrate.versioning.exceptions import *
from test import fixture


python_version = sys.version[:3]

class Shell(fixture.Shell):

    _cmd = os.path.join('python migrate', 'versioning', 'shell.py')

    @classmethod
    def cmd(cls, *args):
        safe_parameters = map(lambda arg: str(arg), args)
        return ' '.join([cls._cmd] + safe_parameters)

    def execute(self, shell_cmd, runshell=None, **kwargs):
        """A crude simulation of a shell command, to speed things up"""

        # If we get an fd, the command is already done
        if isinstance(shell_cmd, (FileType, StringIO)):
            return shell_cmd

        # Analyze the command; see if we can 'fake' the shell
        try:
            # Forced to run in shell?
            # if runshell or '--runshell' in sys.argv:
            if runshell:
                raise Exception
            # Remove the command prefix
            if not shell_cmd.startswith(self._cmd):
                raise Exception
            cmd = shell_cmd[(len(self._cmd) + 1):]
            params = cmd.split(' ')
            command = params[0]
        except:
            return super(Shell, self).execute(shell_cmd)

        # Redirect stdout to an object; redirect stderr to stdout
        fd = StringIO()
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        sys.stdout = fd
        sys.stderr = fd
        # Execute this command
        try:
            try:
                shell.main(params, **kwargs)
            except SystemExit, e:
                # Simulate the exit status
                fd_close = fd.close
                def close_():
                    fd_close()
                    return e.args[0]
                fd.close = close_
            except Exception, e:
                # Print the exception, but don't re-raise it
                traceback.print_exc()
                # Simulate a nonzero exit status
                fd_close = fd.close
                def close_():
                    fd_close()
                    return 2
                fd.close = close_
        finally:
            # Clean up
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            fd.seek(0)
        return fd

    def cmd_version(self, repos_path):
        fd = self.execute(self.cmd('version', repos_path))
        result = int(fd.read().strip())
        self.assertSuccess(fd)
        return result

    def cmd_db_version(self, url, repos_path):
        fd = self.execute(self.cmd('db_version', url, repos_path))
        txt = fd.read()
        #print txt
        ret = int(txt.strip())
        self.assertSuccess(fd)
        return ret

class TestShellCommands(Shell):
    """Tests migrate.py commands"""

    def test_help(self):
        """Displays default help dialog"""
        self.assertSuccess(self.cmd('-h'), runshell=True)
        self.assertSuccess(self.cmd('--help'), runshell=True)
        self.assertSuccess(self.cmd('help'), runshell=True)
        self.assertSuccess(self.cmd('help'))

        self.assertRaises(UsageError, api.help)
        self.assertRaises(UsageError, api.help, 'foobar')
        self.assert_(isinstance(api.help('create'), str))

    def test_help_commands(self):
        """Display help on a specific command"""
        for cmd in shell.api.__all__:
            fd = self.execute(self.cmd('help', cmd))
            # Description may change, so best we can do is ensure it shows up
            output = fd.read()
            self.assertNotEquals(output, '')
            self.assertSuccess(fd)

    def test_create(self):
        """Repositories are created successfully"""
        repos = self.tmp_repos()

        # Creating a file that doesn't exist should succeed
        cmd = self.cmd('create', repos, 'repository_name')
        self.assertSuccess(cmd)

        # Files should actually be created
        self.assert_(os.path.exists(repos))

        # The default table should not be None
        repos_ = Repository(repos)
        self.assertNotEquals(repos_.config.get('db_settings', 'version_table'), 'None')

        # Can't create it again: it already exists
        self.assertFailure(cmd)
    
    def test_script(self):
        """We can create a migration script via the command line"""
        repos = self.tmp_repos()
        self.assertSuccess(self.cmd('create', repos, 'repository_name'))

        self.assertSuccess(self.cmd('script', '--repository=%s' % repos, 'Desc'))
        self.assert_(os.path.exists('%s/versions/001_Desc.py' % repos))

        self.assertSuccess(self.cmd('script', '--repository=%s' % repos, 'More'))
        self.assert_(os.path.exists('%s/versions/002_More.py' % repos))

        self.assertSuccess(self.cmd('script', '--repository=%s' % repos, '"Some Random name"'), runshell=True)
        self.assert_(os.path.exists('%s/versions/003_Some_Random_name.py' % repos))

    def test_script_sql(self):
        """We can create a migration sql script via the command line"""
        repos = self.tmp_repos()
        self.assertSuccess(self.cmd('create', repos, 'repository_name'))

        self.assertSuccess(self.cmd('script_sql', '--repository=%s' % repos, 'mydb'))
        self.assert_(os.path.exists('%s/versions/001_mydb_upgrade.sql' % repos))
        self.assert_(os.path.exists('%s/versions/001_mydb_downgrade.sql' % repos))

        # Test creating a second
        self.assertSuccess(self.cmd('script_sql', '--repository=%s' % repos, 'postgres'))
        self.assert_(os.path.exists('%s/versions/002_postgres_upgrade.sql' % repos))
        self.assert_(os.path.exists('%s/versions/002_postgres_downgrade.sql' % repos))

    def test_manage(self):
        """Create a project management script"""
        script = self.tmp_py()
        self.assert_(not os.path.exists(script))

        # No attempt is made to verify correctness of the repository path here
        self.assertSuccess(self.cmd('manage', script, '--repository=/path/to/repository'))
        self.assert_(os.path.exists(script))

class TestShellRepository(Shell):
    """Shell commands on an existing repository/python script"""

    def setUp(self):
        """Create repository, python change script"""
        super(TestShellRepository, self).setUp()
        self.path_repos = repos = self.tmp_repos()
        self.assertSuccess(self.cmd('create', repos, 'repository_name'))

    def test_version(self):
        """Correctly detect repository version"""
        # Version: 0 (no scripts yet); successful execution
        fd = self.execute(self.cmd('version','--repository=%s' % self.path_repos))
        self.assertEquals(fd.read().strip(), "0")
        self.assertSuccess(fd)

        # Also works as a positional param
        fd = self.execute(self.cmd('version', self.path_repos))
        self.assertEquals(fd.read().strip(), "0")
        self.assertSuccess(fd)

        # Create a script and version should increment
        self.assertSuccess(self.cmd('script', '--repository=%s' % self.path_repos, 'Desc'))
        fd = self.execute(self.cmd('version',self.path_repos))
        self.assertEquals(fd.read().strip(), "1")
        self.assertSuccess(fd)

    def test_source(self):
        """Correctly fetch a script's source"""
        self.assertSuccess(self.cmd('script', '--repository=%s' % self.path_repos, 'Desc'))

        filename = '%s/versions/001_Desc.py' % self.path_repos
        source = open(filename).read()
        self.assert_(source.find('def upgrade') >= 0)

        # Version is now 1
        fd = self.execute(self.cmd('version', self.path_repos))
        self.assert_(fd.read().strip() == "1")
        self.assertSuccess(fd)

        # Output/verify the source of version 1
        fd = self.execute(self.cmd('source', 1, '--repository=%s' % self.path_repos))
        result = fd.read()
        self.assertSuccess(fd)
        self.assert_(result.strip() == source.strip())

        # We can also send the source to a file... test that too
        self.assertSuccess(self.cmd('source', 1, filename, '--repository=%s'%self.path_repos))
        self.assert_(os.path.exists(filename))
        fd = open(filename)
        result = fd.read()
        self.assert_(result.strip() == source.strip())

class TestShellDatabase(Shell, fixture.DB):
    """Commands associated with a particular database"""
    # We'll need to clean up after ourself, since the shell creates its own txn;
    # we need to connect to the DB to see if things worked

    level = fixture.DB.CONNECT
        
    @fixture.usedb()
    def test_version_control(self):
        """Ensure we can set version control on a database"""
        path_repos = repos = self.tmp_repos()
        self.assertSuccess(self.cmd('create', path_repos, 'repository_name'))
        self.exitcode(self.cmd('drop_version_control', self.url, path_repos))
        self.assertSuccess(self.cmd('version_control', self.url, path_repos))

        # Clean up
        self.assertSuccess(self.cmd('drop_version_control',self.url,path_repos))
        # Attempting to drop vc from a database without it should fail
        self.assertFailure(self.cmd('drop_version_control',self.url,path_repos))

    @fixture.usedb()
    def test_wrapped_kwargs(self):
        """Commands with default arguments set by manage.py"""
        path_repos = repos = self.tmp_repos()
        self.assertSuccess(self.cmd('create', '--', '--name=repository_name'), repository=path_repos)
        self.exitcode(self.cmd('drop_version_control'), url=self.url, repository=path_repos)
        self.assertSuccess(self.cmd('version_control'), url=self.url, repository=path_repos)

        # Clean up
        self.assertSuccess(self.cmd('drop_version_control'), url=self.url, repository=path_repos)
        # Attempting to drop vc from a database without it should fail
        self.assertFailure(self.cmd('drop_version_control'), url=self.url, repository=path_repos)

    @fixture.usedb()
    def test_version_control_specified(self):
        """Ensure we can set version control to a particular version"""
        path_repos = self.tmp_repos()
        self.assertSuccess(self.cmd('create', path_repos, 'repository_name'))
        self.exitcode(self.cmd('drop_version_control', self.url, path_repos))

        # Fill the repository
        path_script = self.tmp_py()
        version = 1
        for i in range(version):
            self.assertSuccess(self.cmd('script', '--repository=%s' % path_repos, 'Desc'))

        # Repository version is correct
        fd = self.execute(self.cmd('version', path_repos))
        self.assertEquals(fd.read().strip(), str(version))
        self.assertSuccess(fd)

        # Apply versioning to DB
        self.assertSuccess(self.cmd('version_control', self.url, path_repos, version))

        # Test version number
        fd = self.execute(self.cmd('db_version', self.url, path_repos))
        self.assertEquals(fd.read().strip(), str(version))
        self.assertSuccess(fd)

        # Clean up
        self.assertSuccess(self.cmd('drop_version_control', self.url, path_repos))

    @fixture.usedb()
    def test_upgrade(self):
        """Can upgrade a versioned database"""
        # Create a repository
        repos_name = 'repos_name'
        repos_path = self.tmp()
        self.assertSuccess(self.cmd('create', repos_path,repos_name))
        self.assertEquals(self.cmd_version(repos_path), 0)

        # Version the DB
        self.exitcode(self.cmd('drop_version_control', self.url, repos_path))
        self.assertSuccess(self.cmd('version_control', self.url, repos_path))

        # Upgrades with latest version == 0
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)
        self.assertSuccess(self.cmd('upgrade', self.url, repos_path))
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)
        self.assertSuccess(self.cmd('upgrade', self.url, repos_path, 0))
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)
        self.assertFailure(self.cmd('upgrade', self.url, repos_path, 1))
        self.assertFailure(self.cmd('upgrade', self.url, repos_path, -1))

        # Add a script to the repository; upgrade the db
        self.assertSuccess(self.cmd('script', '--repository=%s' % repos_path, 'Desc'))
        self.assertEquals(self.cmd_version(repos_path), 1)
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)

        # Test preview
        self.assertSuccess(self.cmd('upgrade', self.url, repos_path, 0, "--preview_sql"))
        self.assertSuccess(self.cmd('upgrade', self.url, repos_path, 0, "--preview_py"))

        self.assertSuccess(self.cmd('upgrade', self.url, repos_path))
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 1)
        
        # Downgrade must have a valid version specified
        self.assertFailure(self.cmd('downgrade', self.url, repos_path))
        self.assertFailure(self.cmd('downgrade', self.url, repos_path, '-1', 2))
        #self.assertFailure(self.cmd('downgrade', self.url, repos_path, '1', 2))
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 1)
        
        self.assertSuccess(self.cmd('downgrade', self.url, repos_path, 0))
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)
        
        self.assertFailure(self.cmd('downgrade',self.url, repos_path, 1))
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)

        self.assertSuccess(self.cmd('drop_version_control', self.url, repos_path))

    def _run_test_sqlfile(self, upgrade_script, downgrade_script):
        # TODO: add test script that checks if db really changed

        repos_path = self.tmp()
        repos_name = 'repos'
        self.assertSuccess(self.cmd('create', repos_path, repos_name))
        self.exitcode(self.cmd('drop_version_control', self.url, repos_path))
        self.assertSuccess(self.cmd('version_control', self.url, repos_path))
        self.assertEquals(self.cmd_version(repos_path), 0)
        self.assertEquals(self.cmd_db_version(self.url,repos_path), 0)

        beforeCount = len(os.listdir(os.path.join(repos_path, 'versions')))  # hmm, this number changes sometimes based on running from svn
        self.assertSuccess(self.cmd('script_sql', '--repository=%s' % repos_path, 'postgres'))
        self.assertEquals(self.cmd_version(repos_path), 1)
        self.assertEquals(len(os.listdir(os.path.join(repos_path,'versions'))), beforeCount + 2)

        open('%s/versions/001_postgres_upgrade.sql' % repos_path, 'a').write(upgrade_script)
        open('%s/versions/001_postgres_downgrade.sql' % repos_path, 'a').write(downgrade_script)

        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)
        self.assertRaises(Exception, self.engine.text('select * from t_table').execute)

        self.assertSuccess(self.cmd('upgrade', self.url,repos_path))
        self.assertEquals(self.cmd_db_version(self.url,repos_path), 1)
        self.engine.text('select * from t_table').execute()

        self.assertSuccess(self.cmd('downgrade', self.url, repos_path, 0))
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)
        self.assertRaises(Exception, self.engine.text('select * from t_table').execute)

    # The tests below are written with some postgres syntax, but the stuff
    # being tested (.sql files) ought to work with any db. 
    @fixture.usedb(supported='postgres')
    def test_sqlfile(self):
        upgrade_script = """
        create table t_table (
            id serial,
            primary key(id)
        );
        """
        downgrade_script = """
        drop table t_table;
        """
        self.meta.drop_all()
        self._run_test_sqlfile(upgrade_script, downgrade_script)
        
        
    @fixture.usedb(supported='postgres')
    def test_sqlfile_comment(self):
        upgrade_script = """
        -- Comments in SQL break postgres autocommit
        create table t_table (
            id serial,
            primary key(id)
        );
        """
        downgrade_script = """
        -- Comments in SQL break postgres autocommit
        drop table t_table;
        """
        self._run_test_sqlfile(upgrade_script,downgrade_script)

    @fixture.usedb()
    def test_test(self):
        repos_name = 'repos_name'
        repos_path = self.tmp()

        self.assertSuccess(self.cmd('create', repos_path, repos_name))
        self.exitcode(self.cmd('drop_version_control', self.url, repos_path))
        self.assertSuccess(self.cmd('version_control', self.url, repos_path))
        self.assertEquals(self.cmd_version(repos_path), 0)
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)

        # Empty script should succeed
        self.assertSuccess(self.cmd('script', '--repository=%s' % repos_path, 'Desc'))
        self.assertSuccess(self.cmd('test', repos_path, self.url))
        self.assertEquals(self.cmd_version(repos_path), 1)
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)

        # Error script should fail
        script_path = self.tmp_py()
        script_text="""
        from sqlalchemy import *
        from migrate import *
        
        def upgrade():
            print 'fgsfds'
            raise Exception()
        
        def downgrade():
            print 'sdfsgf'
            raise Exception()
        """.replace("\n        ","\n")
        file = open(script_path, 'w')
        file.write(script_text)
        file.close()

        self.assertFailure(self.cmd('test', repos_path, self.url, 'blah blah'))
        self.assertEquals(self.cmd_version(repos_path), 1)
        self.assertEquals(self.cmd_db_version(self.url, repos_path),0)

        # Nonempty script using migrate_engine should succeed
        script_path = self.tmp_py()
        script_text="""
        from sqlalchemy import *
        from migrate import *
        
        meta = MetaData(migrate_engine)
        account = Table('account',meta,
            Column('id',Integer,primary_key=True),
            Column('login',String(40)),
            Column('passwd',String(40)),
        )
        def upgrade():
            # Upgrade operations go here. Don't create your own engine; use the engine
            # named 'migrate_engine' imported from migrate.
            meta.create_all()
        
        def downgrade():
            # Operations to reverse the above upgrade go here.
            meta.drop_all()
        """.replace("\n        ","\n")
        file = open(script_path, 'w')
        file.write(script_text)
        file.close()
        self.assertSuccess(self.cmd('test', repos_path, self.url))
        self.assertEquals(self.cmd_version(repos_path), 1)
        self.assertEquals(self.cmd_db_version(self.url, repos_path), 0)
        
    @fixture.usedb()
    def test_rundiffs_in_shell(self):
        # This is a variant of the test_schemadiff tests but run through the shell level.
        # These shell tests are hard to debug (since they keep forking processes), so they shouldn't replace the lower-level tests.
        repos_name = 'repos_name'
        repos_path = self.tmp()
        script_path = self.tmp_py()
        old_model_path = self.tmp_named('oldtestmodel.py')
        model_path = self.tmp_named('testmodel.py')

        # Create empty repository.
        self.meta = MetaData(self.engine, reflect=True)
        self.meta.drop_all()  # in case junk tables are lying around in the test database
        self.assertSuccess(self.cmd('create',repos_path,repos_name))
        self.exitcode(self.cmd('drop_version_control',self.url,repos_path))
        self.assertSuccess(self.cmd('version_control',self.url,repos_path))
        self.assertEquals(self.cmd_version(repos_path),0)
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)

        # Setup helper script.
        model_module = 'testmodel:meta'
        self.assertSuccess(self.cmd('manage',script_path,'--repository=%s --url=%s --model=%s' % (repos_path, self.url, model_module)))
        self.assert_(os.path.exists(script_path))
        
        # Write old and new model to disk - old model is empty!
        script_preamble="""
        from sqlalchemy import *
        
        meta = MetaData()
        """.replace("\n        ","\n")
        
        script_text="""
        """.replace("\n        ","\n")
        open(old_model_path, 'w').write(script_preamble + script_text)
        
        script_text="""
        tmp_account_rundiffs = Table('tmp_account_rundiffs',meta,
            Column('id',Integer,primary_key=True),
            Column('login',String(40)),
            Column('passwd',String(40)),
        )
        """.replace("\n        ","\n")
        open(model_path, 'w').write(script_preamble + script_text)
        
        # Model is defined but database is empty.
        output, exitcode = self.output_and_exitcode('python %s compare_model_to_db' % script_path)
        assert "tables missing in database: tmp_account_rundiffs" in output, output

        # Test Deprecation
        output, exitcode = self.output_and_exitcode('python %s compare_model_to_db --model=testmodel.meta' % script_path)
        assert "tables missing in database: tmp_account_rundiffs" in output, output
        
        # Update db to latest model.
        output, exitcode = self.output_and_exitcode('python %s update_db_from_model' % script_path)
        self.assertEquals(exitcode, None)
        self.assertEquals(self.cmd_version(repos_path),0)
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)  # version did not get bumped yet because new version not yet created
        output, exitcode = self.output_and_exitcode('python %s compare_model_to_db' % script_path)
        assert "No schema diffs" in output, output
        output, exitcode = self.output_and_exitcode('python %s create_model' % script_path)
        output = output.replace(genmodel.HEADER.strip(), '')  # need strip b/c output_and_exitcode called strip
        assert """tmp_account_rundiffs = Table('tmp_account_rundiffs', meta,
  Column('id', Integer(),  primary_key=True, nullable=False),
  Column('login', String(length=None, convert_unicode=False, assert_unicode=None)),
  Column('passwd', String(length=None, convert_unicode=False, assert_unicode=None)),""" in output.strip(), output
        
        # We're happy with db changes, make first db upgrade script to go from version 0 -> 1.
        output, exitcode = self.output_and_exitcode('python %s make_update_script_for_model' % script_path)  # intentionally omit a parameter
        self.assertEquals('Not enough arguments' in output, True)
        output, exitcode = self.output_and_exitcode('python %s make_update_script_for_model --oldmodel=oldtestmodel.meta' % script_path)
        assert  """from sqlalchemy import *
from migrate import *

meta = MetaData(migrate_engine)
tmp_account_rundiffs = Table('tmp_account_rundiffs', meta,
  Column('id', Integer(),  primary_key=True, nullable=False),
  Column('login', String(length=40, convert_unicode=False, assert_unicode=None)),
  Column('passwd', String(length=40, convert_unicode=False, assert_unicode=None)),
)

def upgrade():
    # Upgrade operations go here. Don't create your own engine; use the engine
    # named 'migrate_engine' imported from migrate.
    tmp_account_rundiffs.create()

def downgrade():
    # Operations to reverse the above upgrade go here.
    tmp_account_rundiffs.drop()""" in output, output
    
        # Save the upgrade script.
        self.assertSuccess(self.cmd('script', '--repository=%s' % repos_path, 'Desc'))
        upgrade_script_path = '%s/versions/001_Desc.py' % repos_path
        open(upgrade_script_path, 'w').write(output)
        #output, exitcode = self.output_and_exitcode('python %s test %s' % (script_path, upgrade_script_path))  # no, we already upgraded the db above
        #self.assertEquals(output, "")
        output, exitcode = self.output_and_exitcode('python %s update_db_from_model' % script_path)  # bump the db_version
        self.assertEquals(exitcode, None)
        self.assertEquals(self.cmd_version(repos_path),1)
        self.assertEquals(self.cmd_db_version(self.url,repos_path),1)
