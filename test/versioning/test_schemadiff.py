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
            Column('data',UnicodeText()),
        )
        if self.table.exists():
            self.table.drop()
        #self.engine.echo = True
    
    def tearDown(self):
        if self.table.exists():
            self.table.drop()
        fixture.DB.tearDown(self)
        
    @fixture.usedb()
    def test_rundiffs(self):
        
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
            Column('data',UnicodeText(length=None)),
        )
        ''')
        self.assertEqualsIgnoreWhitespace(commands, '''tmp_schemadiff.create()''')
        
        # Create table in database, now model should match database.
        self.table.create()
        assertDiff(False, [], [], [])
        
        # Check Python code gen from database.
        diff = schemadiff.getDiffOfModelAgainstDatabase(MetaData(), self.engine)
        src = genmodel.ModelGenerator(diff).toPython()
        src = src.replace(genmodel.HEADER, '')
        self.assertEqualsIgnoreWhitespace(src, '''
        tmp_schemadiff = Table('tmp_schemadiff',meta,
            Column('id',Integer(),primary_key=True,nullable=False),
            Column('data',Text(length=None,convert_unicode=False,assert_unicode=None)),
        )
        ''')
        
        # Modify table in model (by removing it and adding it back to model).
        self.meta.remove(self.table)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('data2',UnicodeText(),nullable=True),
        )
        assertDiff(True, [], [], [self.table_name])
        
        # Apply latest model changes and find no more diffs.
        self.table.drop()
        self.table.create()
        assertDiff(False, [], [], [])
        
        # Change column type in model.
        self.meta.remove(self.table)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('data2',Integer(),nullable=True),
        )
        assertDiff(True, [], [], [self.table_name])  # TODO test type diff
        
        # Apply latest model changes and find no more diffs.
        self.table.drop()
        self.table.create()
        assertDiff(False, [], [], [])
        
        # Change column nullable in model.
        self.meta.remove(self.table)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer(),primary_key=True),
            Column('data2',Integer(),nullable=False),
        )
        assertDiff(True, [], [], [self.table_name])  # TODO test nullable diff
        
        # Apply latest model changes and find no more diffs.
        self.table.drop()
        self.table.create()
        assertDiff(False, [], [], [])
        
        # Remove table from model.
        self.meta.remove(self.table)
        assertDiff(True, [], [self.table_name], [])
        
