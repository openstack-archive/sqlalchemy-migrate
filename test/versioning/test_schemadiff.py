import os
import sqlalchemy
from sqlalchemy import *
from test import fixture
from migrate.versioning import genmodel, schemadiff
from nose.tools import eq_


class TestSchemaDiff(fixture.DB):
    level=fixture.DB.CONNECT
    table_name = 'tmp_schemadiff'

    def _setup(self, url):
        
        super(TestSchemaDiff, self)._setup(url)
        self.meta = MetaData(self.engine, reflect=True)
        self.meta.drop_all()  # in case junk tables are lying around in the test database
        self.meta = MetaData(self.engine, reflect=True)  # needed if we just deleted some tables
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('name',UnicodeText()),
            Column('data',UnicodeText()),
        )
        WANT_ENGINE_ECHO = os.environ.get('WANT_ENGINE_ECHO', 'F')  # to get debugging: set this to T and run py.test with --pdb
        if WANT_ENGINE_ECHO == 'T':
            self.engine.echo = True
    
    def _teardown(self):
        if self.table.exists():
            #self.table.drop()  # bummer, this doesn't work because the list of tables is out of date, but calling reflect didn't work
            self.meta = MetaData(self.engine, reflect=True)
            self.meta.drop_all()
        super(TestSchemaDiff, self)._teardown()
        
    def _applyLatestModel(self):
        diff = schemadiff.getDiffOfModelAgainstDatabase(self.meta, self.engine, excludeTables=['migrate_version'])
        genmodel.ModelGenerator(diff).applyModel()
        
    @fixture.usedb()
    def test_rundiffs(self):
        
        # Yuck! We have to import from changeset to apply the monkey-patch to allow column adding/dropping.
        from migrate.changeset import schema
        
        def assertDiff(isDiff, tablesMissingInDatabase, tablesMissingInModel, tablesWithDiff):
            diff = schemadiff.getDiffOfModelAgainstDatabase(self.meta, self.engine, excludeTables=['migrate_version'])
            eq_(bool(diff), isDiff)
            eq_( ([t.name for t in diff.tablesMissingInDatabase], [t.name for t in diff.tablesMissingInModel], [t.name for t in diff.tablesWithDiff]),
                           (tablesMissingInDatabase, tablesMissingInModel, tablesWithDiff) )
                
        # Model is defined but database is empty.
        assertDiff(True, [self.table_name], [], [])
        
        # Check Python upgrade and downgrade of database from updated model.
        diff = schemadiff.getDiffOfModelAgainstDatabase(self.meta, self.engine, excludeTables=['migrate_version'])
        decls, upgradeCommands, downgradeCommands = genmodel.ModelGenerator(diff).toUpgradeDowngradePython()
        self.assertEqualsIgnoreWhitespace(decls, '''
        meta = MetaData(migrate_engine)
        tmp_schemadiff = Table('tmp_schemadiff',meta,
            Column('id',Integer(),primary_key=True,nullable=False),
            Column('name',UnicodeText(length=None)),
            Column('data',UnicodeText(length=None)),
        )
        ''')
        self.assertEqualsIgnoreWhitespace(upgradeCommands, '''tmp_schemadiff.create()''')
        self.assertEqualsIgnoreWhitespace(downgradeCommands, '''tmp_schemadiff.drop()''')
        
        # Create table in database, now model should match database.
        self._applyLatestModel()
        assertDiff(False, [], [], [])
        
        # Check Python code gen from database.
        diff = schemadiff.getDiffOfModelAgainstDatabase(MetaData(), self.engine, excludeTables=['migrate_version'])
        src = genmodel.ModelGenerator(diff).toPython()
        src = src.replace(genmodel.HEADER, '')
        self.assertEqualsIgnoreWhitespace(src, '''
        tmp_schemadiff = Table('tmp_schemadiff',meta,
            Column('id',Integer(),primary_key=True,nullable=False),
            Column('name',Text(length=None,convert_unicode=False,assert_unicode=None)),
            Column('data',Text(length=None,convert_unicode=False,assert_unicode=None)),
        )
        ''')
        
        # Add data, later we'll make sure it's still present.
        result = self.engine.execute(self.table.insert(), id=1, name=u'mydata')
        dataId = result.last_inserted_ids()[0]
        
        # Modify table in model (by removing it and adding it back to model) -- drop column data and add column data2.
        self.meta.remove(self.table)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('name',UnicodeText(length=None)),
            Column('data2',Integer(),nullable=True),
        )
        assertDiff(True, [], [], [self.table_name])
        
        # Apply latest model changes and find no more diffs.
        self._applyLatestModel()
        assertDiff(False, [], [], [])
        
        # Make sure data is still present.
        result = self.engine.execute(self.table.select(self.table.c.id==dataId))
        rows = result.fetchall()
        eq_(len(rows), 1)
        eq_(rows[0].name, 'mydata')
        
        # Add data, later we'll make sure it's still present.
        result = self.engine.execute(self.table.insert(), id=2, name=u'mydata2', data2=123)
        dataId2 = result.last_inserted_ids()[0]
        
        # Change column type in model.
        self.meta.remove(self.table)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('name',UnicodeText(length=None)),
            Column('data2',UnicodeText(),nullable=True),
        )
        assertDiff(True, [], [], [self.table_name])  # TODO test type diff
        
        # Apply latest model changes and find no more diffs.
        self._applyLatestModel()
        assertDiff(False, [], [], [])
        
        # Make sure data is still present.
        result = self.engine.execute(self.table.select(self.table.c.id==dataId2))
        rows = result.fetchall()
        self.assertEquals(len(rows), 1)
        self.assertEquals(rows[0].name, 'mydata2')
        self.assertEquals(rows[0].data2, '123')
        
        # Delete data, since we're about to make a required column.
        # Not even using sqlalchemy.PassiveDefault helps because we're doing explicit column select.
        self.engine.execute(self.table.delete(), id=dataId)
        
        # Change column nullable in model.
        self.meta.remove(self.table)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('name',UnicodeText(length=None)),
            Column('data2',UnicodeText(),nullable=False),
        )
        assertDiff(True, [], [], [self.table_name])  # TODO test nullable diff
        
        # Apply latest model changes and find no more diffs.
        self._applyLatestModel()
        assertDiff(False, [], [], [])
        
        # Remove table from model.
        self.meta.remove(self.table)
        assertDiff(True, [], [self.table_name], [])
        
