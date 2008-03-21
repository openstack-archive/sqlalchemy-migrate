import sys
import traceback
from StringIO import StringIO
import os,shutil
from test import fixture
from migrate.versioning.repository import Repository
from migrate.versioning import shell
from sqlalchemy import MetaData,Table

python_version = sys.version[0:3]

class Shell(fixture.Shell):
    _cmd=os.path.join('python migrate', 'versioning', 'shell.py')
    @classmethod
    def cmd(cls,*p):
        p = map(lambda s: str(s),p)
        ret = ' '.join([cls._cmd]+p)
        return ret
    def execute(self,shell_cmd,runshell=None):
        """A crude simulation of a shell command, to speed things up"""
        # If we get an fd, the command is already done
        if isinstance(shell_cmd,file) or isinstance(shell_cmd,StringIO):
            return shell_cmd
        # Analyze the command; see if we can 'fake' the shell
        try:
            # Forced to run in shell?
            #if runshell or '--runshell' in sys.argv:
            if runshell:
                raise Exception
            # Remove the command prefix
            if not shell_cmd.startswith(self._cmd):
                raise Exception
            cmd = shell_cmd[(len(self._cmd)+1):]
            params = cmd.split(' ')
            command = params[0]
        except: 
            return super(Shell,self).execute(shell_cmd)

        # Redirect stdout to an object; redirect stderr to stdout
        fd = StringIO()
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        sys.stdout = fd
        sys.stderr = fd
        # Execute this command
        try:
            try:
                shell.main(params)
            except SystemExit,e:
                # Simulate the exit status
                fd_close=fd.close
                def close_():
                    fd_close()
                    return e.args[0]
                fd.close = close_
            except Exception,e:
                # Print the exception, but don't re-raise it
                traceback.print_exc()
                # Simulate a nonzero exit status
                fd_close=fd.close
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

    def cmd_version(self,repos_path):
        fd = self.execute(self.cmd('version',repos_path))
        ret = int(fd.read().strip())
        self.assertSuccess(fd)
        return ret
    def cmd_db_version(self,url,repos_path):
        fd = self.execute(self.cmd('db_version',url,repos_path))
        txt = fd.read()
        #print txt
        ret = int(txt.strip())
        self.assertSuccess(fd)
        return ret

class TestShellCommands(Shell):
    """Tests migrate.py commands"""

    def test_run(self):
        """Runs; displays help"""
        # Force this to run in shell...
        self.assertSuccess(self.cmd('-h'),runshell=True)
        self.assertSuccess(self.cmd('--help'),runshell=True)

    def test_help(self):
        """Display help on a specific command"""
        self.assertSuccess(self.cmd('-h'),runshell=True)
        self.assertSuccess(self.cmd('--help'),runshell=True)
        for cmd in shell.api.__all__:
            fd=self.execute(self.cmd('help',cmd))
            # Description may change, so best we can do is ensure it shows up
            #self.assertNotEquals(fd.read(),'')
            output = fd.read()
            self.assertNotEquals(output,'')
            self.assertSuccess(fd)
    
    def test_create(self):
        """Repositories are created successfully"""
        repos=self.tmp_repos()
        name='name'
        # Creating a file that doesn't exist should succeed
        cmd=self.cmd('create',repos,name)
        self.assertSuccess(cmd)
        # Files should actually be created
        self.assert_(os.path.exists(repos))
        # The default table should not be None
        repos_ = Repository(repos)
        self.assertNotEquals(repos_.config.get('db_settings','version_table'),'None')
        # Can't create it again: it already exists
        self.assertFailure(cmd)
    
    def test_script(self):
        """We can create a migration script via the command line"""
        script=self.tmp_py()
        # Creating a file that doesn't exist should succeed
        self.assertSuccess(self.cmd('script',script))
        self.assert_(os.path.exists(script))
        # 's' instead of 'script' should work too
        os.remove(script)
        self.assert_(not os.path.exists(script))
        self.assertSuccess(self.cmd('s',script))
        self.assert_(os.path.exists(script))
        # Can't create it again: it already exists
        self.assertFailure(self.cmd('script',script))

    def test_manage(self):
        """Create a project management script"""
        script=self.tmp_py()
        self.assert_(not os.path.exists(script))
        # No attempt is made to verify correctness of the repository path here
        self.assertSuccess(self.cmd('manage',script,'--repository=/path/to/repository'))
        self.assert_(os.path.exists(script))

class TestShellRepository(Shell):
    """Shell commands on an existing repository/python script"""
    def setUp(self):
        """Create repository, python change script"""
        self.path_repos=repos=self.tmp_repos()
        self.path_script=script=self.tmp_py()
        self.assertSuccess(self.cmd('create',repos,'repository_name'))
        self.assertSuccess(self.cmd('script',script))
    
    def test_commit_1(self):
        """Commits should work correctly; script should vanish after commit"""
        self.assert_(os.path.exists(self.path_script))
        self.assertSuccess(self.cmd('commit',self.path_script,self.path_repos))
        self.assert_(not os.path.exists(self.path_script))
    def test_commit_2(self):
        """Commits should work correctly with repository as a keyword param"""
        self.assert_(os.path.exists(self.path_script))
        self.assertSuccess(self.cmd('commit',self.path_script,'--repository=%s'%self.path_repos))
        self.assert_(not os.path.exists(self.path_script))
    def test_version(self):
        """Correctly detect repository version"""
        # Version: 0 (no scripts yet); successful execution
        fd=self.execute(self.cmd('version','--repository=%s'%self.path_repos))
        self.assertEquals(fd.read().strip(),"0")
        self.assertSuccess(fd)
        # Also works as a positional param
        fd=self.execute(self.cmd('version',self.path_repos))
        self.assertEquals(fd.read().strip(),"0")
        self.assertSuccess(fd)
        # Commit a script and version should increment
        self.assertSuccess(self.cmd('commit',self.path_script,'--repository=%s'%self.path_repos))
        fd=self.execute(self.cmd('version',self.path_repos))
        self.assertEquals(fd.read().strip(),"1")
        self.assertSuccess(fd)
    def test_source(self):
        """Correctly fetch a script's source"""
        source=open(self.path_script).read()
        self.assert_(source.find('def upgrade')>=0)
        self.assertSuccess(self.cmd('commit',self.path_script,'--repository=%s'%self.path_repos))
        # Later, we'll want to make repos optional somehow
        # Version is now 1
        fd=self.execute(self.cmd('version',self.path_repos))
        self.assert_(fd.read().strip()=="1")
        self.assertSuccess(fd)
        # Output/verify the source of version 1
        fd=self.execute(self.cmd('source',1,'--repository=%s'%self.path_repos))
        result=fd.read()
        self.assertSuccess(fd)
        self.assert_(result.strip()==source.strip())
        # We can also send the source to a file... test that too
        self.assertSuccess(self.cmd('source',1,self.path_script,'--repository=%s'%self.path_repos))
        self.assert_(os.path.exists(self.path_script))
        fd=open(self.path_script)
        result=fd.read()
        self.assert_(result.strip()==source.strip())
    def test_commit_replace(self):
        """Commit can replace a specified version"""
        # Commit the default script
        self.assertSuccess(self.cmd('commit',self.path_script,self.path_repos))
        self.assertEquals(self.cmd_version(self.path_repos),1)
        # Read the default script's text
        fd=self.execute(self.cmd('source',1,'--repository=%s'%self.path_repos))
        script_src_1 = fd.read()
        self.assertSuccess(fd)

        # Commit a new script
        script_text="""
        from sqlalchemy import *
        from migrate import *
        
        # Our test is just that the source is different; so we don't have to 
        # do anything useful in here.
        
        def upgrade():
            pass
        
        def downgrade():
            pass
        """.replace('\n        ','\n')
        fd=open(self.path_script,'w')
        fd.write(script_text)
        fd.close()
        self.assertSuccess(self.cmd('commit',self.path_script,self.path_repos,1))
        # We specified a version above - it should replace that, not create new
        self.assertEquals(self.cmd_version(self.path_repos),1)
        # Source should change
        fd=self.execute(self.cmd('source',1,'--repository=%s'%self.path_repos))
        script_src_2 = fd.read()
        self.assertSuccess(fd)
        self.assertNotEquals(script_src_1,script_src_2)
        # source should be reasonable
        self.assertEquals(script_src_2.strip(),script_text.strip())
        self.assert_(script_src_1.count('from migrate import'))
        self.assert_(script_src_1.count('from sqlalchemy import'))

class TestShellDatabase(Shell,fixture.DB):
    """Commands associated with a particular database"""
    # We'll need to clean up after ourself, since the shell creates its own txn;
    # we need to connect to the DB to see if things worked
    level=fixture.DB.CONNECT
        
    @fixture.usedb()
    def test_version_control(self):
        """Ensure we can set version control on a database"""
        path_repos=repos=self.tmp_repos()
        self.assertSuccess(self.cmd('create',path_repos,'repository_name'))
        self.exitcode(self.cmd('drop_version_control',self.url,path_repos))
        self.assertSuccess(self.cmd('version_control',self.url,path_repos))
        # Clean up
        self.assertSuccess(self.cmd('drop_version_control',self.url,path_repos))
        # Attempting to drop vc from a database without it should fail
        self.assertFailure(self.cmd('drop_version_control',self.url,path_repos))

    @fixture.usedb()
    def test_version_control_specified(self):
        """Ensure we can set version control to a particular version"""
        path_repos=self.tmp_repos()
        self.assertSuccess(self.cmd('create',path_repos,'repository_name'))
        self.exitcode(self.cmd('drop_version_control',self.url,path_repos))
        # Fill the repository
        path_script = self.tmp_py()
        version=1
        for i in range(version):
            self.assertSuccess(self.cmd('script',path_script))
            self.assertSuccess(self.cmd('commit',path_script,path_repos))
        # Repository version is correct
        fd=self.execute(self.cmd('version',path_repos))
        self.assertEquals(fd.read().strip(),str(version))
        self.assertSuccess(fd)
        # Apply versioning to DB
        self.assertSuccess(self.cmd('version_control',self.url,path_repos,version))
        # Test version number
        fd=self.execute(self.cmd('db_version',self.url,path_repos))
        self.assertEquals(fd.read().strip(),str(version))
        self.assertSuccess(fd)
        # Clean up
        self.assertSuccess(self.cmd('drop_version_control',self.url,path_repos))

    @fixture.usedb()
    def test_upgrade(self):
        """Can upgrade a versioned database"""
        # Create a repository
        repos_name = 'repos_name'
        repos_path = self.tmp()
        script_path = self.tmp_py()
        self.assertSuccess(self.cmd('create',repos_path,repos_name))
        self.assertEquals(self.cmd_version(repos_path),0)
        # Version the DB
        self.exitcode(self.cmd('drop_version_control',self.url,repos_path))
        self.assertSuccess(self.cmd('version_control',self.url,repos_path))

        # Upgrades with latest version == 0
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)
        self.assertSuccess(self.cmd('upgrade',self.url,repos_path))
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)
        self.assertSuccess(self.cmd('upgrade',self.url,repos_path,0))
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)
        self.assertFailure(self.cmd('upgrade',self.url,repos_path,1))
        self.assertFailure(self.cmd('upgrade',self.url,repos_path,-1))

        # Add a script to the repository; upgrade the db
        self.assertSuccess(self.cmd('script',script_path))
        self.assertSuccess(self.cmd('commit',script_path,repos_path))
        self.assertEquals(self.cmd_version(repos_path),1)

        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)
        self.assertSuccess(self.cmd('upgrade',self.url,repos_path))
        self.assertEquals(self.cmd_db_version(self.url,repos_path),1)
        # Downgrade must have a valid version specified
        self.assertFailure(self.cmd('downgrade',self.url,repos_path))
        self.assertFailure(self.cmd('downgrade',self.url,repos_path,2))
        self.assertFailure(self.cmd('downgrade',self.url,repos_path,-1))
        self.assertEquals(self.cmd_db_version(self.url,repos_path),1)
        self.assertSuccess(self.cmd('downgrade',self.url,repos_path,0))
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)
        self.assertFailure(self.cmd('downgrade',self.url,repos_path,1))
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)

        self.assertSuccess(self.cmd('drop_version_control',self.url,repos_path))
    
    def _run_test_sqlfile(self,upgrade_script,downgrade_script):
        upgrade_path = self.tmp_sql()
        downgrade_path = self.tmp_sql()
        upgrade = (upgrade_path,upgrade_script)
        downgrade = (downgrade_path,downgrade_script)
        for file_path,file_text in (upgrade,downgrade):
            fd = open(file_path,'w')
            fd.write(file_text)
            fd.close()

        repos_path = self.tmp()
        repos_name = 'repos'
        self.assertSuccess(self.cmd('create',repos_path,repos_name))
        self.exitcode(self.cmd('drop_version_control',self.url,repos_path))
        self.assertSuccess(self.cmd('version_control',self.url,repos_path))
        self.assertEquals(self.cmd_version(repos_path),0)
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)

        self.assertSuccess(self.cmd('commit',upgrade_path,repos_path,'postgres','upgrade'))
        self.assertEquals(self.cmd_version(repos_path),1)
        self.assertEquals(len(os.listdir(os.path.join(repos_path,'versions','1'))),2)

        # Add, not replace
        self.assertSuccess(self.cmd('commit',downgrade_path,repos_path,'postgres','downgrade','--version=1'))
        self.assertEquals(len(os.listdir(os.path.join(repos_path,'versions','1'))),3)
        self.assertEquals(self.cmd_version(repos_path),1)


        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)
        self.assertRaises(Exception,self.engine.text('select * from t_table').execute)

        self.assertSuccess(self.cmd('upgrade',self.url,repos_path))
        self.assertEquals(self.cmd_db_version(self.url,repos_path),1)
        self.engine.text('select * from t_table').execute()

        self.assertSuccess(self.cmd('downgrade',self.url,repos_path,0))
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)
        self.assertRaises(Exception,self.engine.text('select * from t_table').execute)

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
        self._run_test_sqlfile(upgrade_script,downgrade_script)
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
        script_path = self.tmp_py()

        self.assertSuccess(self.cmd('create',repos_path,repos_name))
        self.exitcode(self.cmd('drop_version_control',self.url,repos_path))
        self.assertSuccess(self.cmd('version_control',self.url,repos_path))
        self.assertEquals(self.cmd_version(repos_path),0)
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)

        # Empty script should succeed
        self.assertSuccess(self.cmd('script',script_path))
        self.assertSuccess(self.cmd('test',script_path,repos_path,self.url))
        self.assertEquals(self.cmd_version(repos_path),0)
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)

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
        file=open(script_path,'w')
        file.write(script_text)
        file.close()
        self.assertFailure(self.cmd('test',script_path,repos_path,self.url))
        self.assertEquals(self.cmd_version(repos_path),0)
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)

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
        file=open(script_path,'w')
        file.write(script_text)
        file.close()
        self.assertSuccess(self.cmd('test',script_path,repos_path,self.url))
        self.assertEquals(self.cmd_version(repos_path),0)
        self.assertEquals(self.cmd_db_version(self.url,repos_path),0)
