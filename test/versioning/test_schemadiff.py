import os
import sqlalchemy
from sqlalchemy import *
from test import fixture
from migrate.versioning import genmodel, schemadiff


class TestSchemaDiff(fixture.DB):
    level=fixture.DB.CONNECT
    table_name = 'tmp_schemadiff'

    def assertEqualsIgnoreWhitespace(self, v1, v2):
        
        def createLines(s):
            s = s.replace(' ', '')
            lines = s.split('\n')
            return [ line for line in lines if line ]
        
        lines1 = createLines(v1)
        lines2 = createLines(v2)
        self.assertEquals(len(lines1), len(lines2))
        for line1, line2 in zip(lines1, lines2):
            self.assertEquals(line1, line2)

    def setUp(self):
        fixture.DB.setUp(self)
        self.meta = MetaData(self.engine)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('name',UnicodeText()),
            Column('data',UnicodeText()),
        )
        if self.table.exists():
            self.table.drop()
        WANT_ENGINE_ECHO = os.environ.get('WANT_ENGINE_ECHO', 'F')  # to get debugging: set this to T and run py.test with --pdb
        if WANT_ENGINE_ECHO == 'T':
            self.engine.echo = True
    
    def tearDown(self):
        if self.table.exists():
            self.table.drop()
        fixture.DB.tearDown(self)
        
    def _applyLatestModel(self):
        diff = schemadiff.getDiffOfModelAgainstDatabase(self.meta, self.engine)
        genmodel.ModelGenerator(diff).applyModel()
        
    @fixture.usedb()
    def test_rundiffs(self):
        
        # Yuck! We have to import from changeset to apply the monkey-patch to allow column adding/dropping.
        from migrate.changeset import schema
        
        def assertDiff(isDiff, tablesMissingInDatabase, tablesMissingInModel, tablesWithDiff):
            diff = schemadiff.getDiffOfModelAgainstDatabase(self.meta, self.engine)
            self.assertEquals(bool(diff), isDiff)
            self.assertEquals( ([t.name for t in diff.tablesMissingInDatabase], [t.name for t in diff.tablesMissingInModel], [t.name for t in diff.tablesWithDiff]),
                           (tablesMissingInDatabase, tablesMissingInModel, tablesWithDiff) )
                
        # Model is defined but database is empty.
        assertDiff(True, [self.table_name], [], [])
        
        # Check Python upgrade of database from updated model.
        diff = schemadiff.getDiffOfModelAgainstDatabase(self.meta, self.engine)
        decl, commands = genmodel.ModelGenerator(diff).toUpgradePython()
        self.assertEqualsIgnoreWhitespace(decl, '''
        meta = MetaData(migrate_engine)
        tmp_schemadiff = Table('tmp_schemadiff',meta,
            Column('id',Integer(),primary_key=True,nullable=False),
            Column('name',UnicodeText(length=None)),
            Column('data',UnicodeText(length=None)),
        )
        ''')
        self.assertEqualsIgnoreWhitespace(commands, '''tmp_schemadiff.create()''')
        
        # Create table in database, now model should match database.
        self._applyLatestModel()
        assertDiff(False, [], [], [])
        
        # Check Python code gen from database.
        diff = schemadiff.getDiffOfModelAgainstDatabase(MetaData(), self.engine)
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
            Column('data2',UnicodeText(),nullable=True),
        )
        assertDiff(True, [], [], [self.table_name])
        
        # Apply latest model changes and find no more diffs.
        self._applyLatestModel()
        assertDiff(False, [], [], [])
        
        # Make sure data is still present.
        result = self.engine.execute(self.table.select(), id=dataId)
        rows = result.fetchall()
        self.assertEquals(len(rows), 1)
        self.assertEquals(rows[0].name, 'mydata')
        
        # Change column type in model.
        self.meta.remove(self.table)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('name',UnicodeText(length=None)),
            Column('data2',Integer(),nullable=True),
        )
        assertDiff(True, [], [], [self.table_name])  # TODO test type diff
        
        # Apply latest model changes and find no more diffs.
        self._applyLatestModel()
        assertDiff(False, [], [], [])
        
        # Delete data, since we're about to make a required column.
        # Not even using sqlalchemy.PassiveDefault helps because we're doing explicit column select.
        self.engine.execute(self.table.delete(), id=dataId)
        
        # Change column nullable in model.
        self.meta.remove(self.table)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('name',UnicodeText(length=None)),
            Column('data2',Integer(),nullable=False),
        )
        assertDiff(True, [], [], [self.table_name])  # TODO test nullable diff
        
        # Apply latest model changes and find no more diffs.
        self._applyLatestModel()
        assertDiff(False, [], [], [])
        
        # Remove table from model.
        self.meta.remove(self.table)
        assertDiff(True, [], [self.table_name], [])
        
