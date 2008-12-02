from test import fixture
from migrate.versioning.schema import *
from migrate.versioning import script,exceptions
import os,shutil

class TestControlledSchema(fixture.Pathed,fixture.DB):
    # Transactions break postgres in this test; we'll clean up after ourselves
    level=fixture.DB.CONNECT
    
    def _setup(self, url):
        super(TestControlledSchema, self)._setup(url)
        path_repos=self.tmp_repos()
        self.repos=Repository.create(path_repos,'repository_name')
        # drop existing version table if necessary
        try:
            ControlledSchema(self.engine,self.repos).drop()
        except:
            # No table to drop; that's fine, be silent
            pass

    @fixture.usedb()
    def test_version_control(self):
        """Establish version control on a particular database"""
        # Establish version control on this database
        dbcontrol=ControlledSchema.create(self.engine,self.repos)
        
        # We can load a controlled DB this way, too
        dbcontrol0=ControlledSchema(self.engine,self.repos)
        self.assertEquals(dbcontrol,dbcontrol0)
        # We can also use a repository path, instead of a repository
        dbcontrol0=ControlledSchema(self.engine,self.repos.path)
        self.assertEquals(dbcontrol,dbcontrol0)
        # We don't have to use the same connection
        engine=create_engine(self.url)
        dbcontrol0=ControlledSchema(self.engine,self.repos.path)
        self.assertEquals(dbcontrol,dbcontrol0)

        # Trying to create another DB this way fails: table exists
        self.assertRaises(exceptions.ControlledSchemaError,
            ControlledSchema.create,self.engine,self.repos)

        # Clean up: 
        # un-establish version control
        dbcontrol.drop()
        # Attempting to drop vc from a db without it should fail
        self.assertRaises(exceptions.DatabaseNotControlledError,dbcontrol.drop)

    @fixture.usedb()
    def test_version_control_specified(self):
        """Establish version control with a specified version"""
        # Establish version control on this database
        version=0
        dbcontrol=ControlledSchema.create(self.engine,self.repos,version)
        self.assertEquals(dbcontrol.version,version)
        
        # Correct when we load it, too
        dbcontrol=ControlledSchema(self.engine,self.repos)
        self.assertEquals(dbcontrol.version,version)

        dbcontrol.drop()

        # Now try it with a nonzero value
        version=10
        for i in range(version):
            self.repos.create_script('')
        self.assertEquals(self.repos.latest,version)

        # Test with some mid-range value
        dbcontrol=ControlledSchema.create(self.engine,self.repos,5)
        self.assertEquals(dbcontrol.version,5)
        dbcontrol.drop()

        # Test with max value
        dbcontrol=ControlledSchema.create(self.engine,self.repos,version)
        self.assertEquals(dbcontrol.version,version)
        dbcontrol.drop()

    @fixture.usedb()
    def test_version_control_invalid(self):
        """Try to establish version control with an invalid version"""
        versions=('Thirteen','-1',-1,'',13)
        # A fresh repository doesn't go up to version 13 yet
        for version in versions:
            #self.assertRaises(ControlledSchema.InvalidVersionError,
            # Can't have custom errors with assertRaises...
            try:
                ControlledSchema.create(self.engine,self.repos,version)
                self.assert_(False,repr(version))
            except exceptions.InvalidVersionError:
                pass
