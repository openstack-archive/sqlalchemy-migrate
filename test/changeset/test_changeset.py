import sqlalchemy
from sqlalchemy import *
from test import fixture
from migrate import changeset
from migrate.changeset import *
from migrate.changeset.schema import _ColumnDelta
from sqlalchemy.databases import information_schema

import migrate
from migrate.run import driver

class TestAddDropColumn(fixture.DB):
    level=fixture.DB.CONNECT
    meta = MetaData()
    # We'll be adding the 'data' column
    table_name = 'tmp_adddropcol'
    table_int = 0

    def setUp(self):
        fixture.DB.setUp(self)
        self._connect(self.url)
        self.meta.clear()
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer,primary_key=True),
        )
        super(TestAddDropColumn,self).setUp()
        self.meta.bind = self.engine
        if self.engine.has_table(self.table.name):
            self.table.drop()
        self.table.create()
    def tearDown(self):
        super(TestAddDropColumn,self).tearDown()
        if self.engine.has_table(self.table.name):
            self.table.drop()
        self.meta.clear()

    def run_(self,create_column_func,drop_column_func,*col_p,**col_k):
        col_name = 'data'

        def _assert_numcols(expected,type_):
            result = len(self.table.c)
            self.assertEquals(result,expected,
                "# %s cols incorrect: %s != %s"%(type_,result,expected))
            if not col_k.get('primary_key',None):
                return
            # new primary key: check its length too
            result = len(self.table.primary_key)
            self.assertEquals(result,expected,
                "# %s pks incorrect: %s != %s"%(type_,result,expected))
        def assert_numcols(expected):
            # number of cols should be correct in table object and in database
            # Changed: create/drop shouldn't mess with the objects
            #_assert_numcols(expected,'object')
            # Detect # database cols via autoload
            self.meta.clear()
            self.table=Table(self.table_name,self.meta,autoload=True)
            _assert_numcols(expected,'database')
        assert_numcols(1)
        if len(col_p) == 0:
            col_p = [String(40)]
        col = Column(col_name,*col_p,**col_k)
        create_column_func(col)
        #create_column(col,self.table)
        assert_numcols(2)
        self.assertEquals(getattr(self.table.c,col_name),col)
        #drop_column(col,self.table)
        col = getattr(self.table.c,col_name)
        # SQLite can't do drop column: stop here
        if self.url.startswith('sqlite://'):
            self.assertRaises(changeset.exceptions.NotSupportedError,drop_column_func,col)
            return
        drop_column_func(col)
        assert_numcols(1)

    @fixture.usedb()
    def test_undefined(self):
        """Add/drop columns not yet defined in the table"""
        def add_func(col):
            return create_column(col,self.table)
        def drop_func(col):
            return drop_column(col,self.table)
        return self.run_(add_func,drop_func)

    @fixture.usedb()
    def test_defined(self):
        """Add/drop columns already defined in the table"""
        def add_func(col):
            self.meta.clear()
            self.table = Table(self.table_name,self.meta,
                Column('id',Integer,primary_key=True),
                col,
            )
            return create_column(col,self.table)
        def drop_func(col):
            return drop_column(col,self.table)
        return self.run_(add_func,drop_func)

    @fixture.usedb()
    def test_method_bound(self):
        """Add/drop columns via column methods; columns bound to a table
        ie. no table parameter passed to function
        """
        def add_func(col):
            self.assert_(col.table is None,col.table)
            self.table.append_column(col)
            return col.create()
        def drop_func(col):
            #self.assert_(col.table is None,col.table)
            #self.table.append_column(col)
            return col.drop()
        return self.run_(add_func,drop_func)

    @fixture.usedb()
    def test_method_notbound(self):
        """Add/drop columns via column methods; columns not bound to a table"""
        def add_func(col):
            return col.create(self.table)
        def drop_func(col):
            return col.drop(self.table)
        return self.run_(add_func,drop_func)

    @fixture.usedb()
    def test_tablemethod_obj(self):
        """Add/drop columns via table methods; by column object"""
        def add_func(col):
            return self.table.create_column(col)
        def drop_func(col):
            return self.table.drop_column(col)
        return self.run_(add_func,drop_func)

    @fixture.usedb()
    def test_tablemethod_name(self):
        """Add/drop columns via table methods; by column name"""
        def add_func(col):
            # must be bound to table
            self.table.append_column(col)
            return self.table.create_column(col.name)
        def drop_func(col):
            # Not necessarily bound to table
            return self.table.drop_column(col.name)
        return self.run_(add_func,drop_func)
        
    @fixture.usedb()
    def test_byname(self):
        """Add/drop columns via functions; by table object and column name"""
        def add_func(col):
            self.table.append_column(col)
            return create_column(col.name,self.table)
        def drop_func(col):
            return drop_column(col.name,self.table)
        return self.run_(add_func,drop_func)

    @fixture.usedb()
    def test_fk(self):
        """Can create columns with foreign keys"""
        reftable = Table('tmp_ref',self.meta,
            Column('id',Integer,primary_key=True),
        )
        def add_func(col):
            # create FK's target
            if self.engine.has_table(reftable.name):
                reftable.drop()
            reftable.create()
            self.table.append_column(col)
            return create_column(col.name,self.table)
        def drop_func(col):
            ret = drop_column(col.name,self.table)
            if self.engine.has_table(reftable.name):
                reftable.drop()
            return ret
        return self.run_(add_func,drop_func,Integer,ForeignKey('tmp_ref.id'))

    #@fixture.usedb()
    #def xtest_pk(self):
    #    """Can create/drop primary key columns
    #    Not supported
    #    """
    #    def add_func(col):
    #        create_column(col,self.table)
    #    def drop_func(col):
    #        drop_column(col,self.table)
    #    # Primary key length is checked in run_
    #    return self.run_(add_func,drop_func,Integer,primary_key=True)

class TestRename(fixture.DB):
    level=fixture.DB.CONNECT
    meta = MetaData()

    def setUp(self):
        fixture.DB.setUp(self)
        self._connect(self.url)
        self.meta.bind = self.engine #self.meta.connect(self.engine)

    @fixture.usedb()
    def test_rename_table(self):
        """Tables can be renamed"""
        #self.engine.echo=True
        name1 = 'name_one'
        name2 = 'name_two'
        xname1 = 'x'+name1
        xname2 = 'x'+name2
        self.column = Column(name1,Integer)
        self.meta.clear()
        self.table = Table(name1,self.meta,self.column)
        self.index = Index(xname1,self.column,unique=False)
        if self.engine.has_table(self.table.name):
            self.table.drop()
        if self.engine.has_table(name2):
            tmp = Table(name2,self.meta,autoload=True)
            tmp.drop()
            tmp.deregister()
            del tmp
        self.table.create()

        def assert_table_name(expected,skip_object_check=False):
            """Refresh a table via autoload
            SA has changed some since this test was written; we now need to do
            meta.clear() upon reloading a table - clear all rather than a
            select few. So, this works only if we're working with one table at
            a time (else, others will vanish too).
            """
            if not skip_object_check:
                # Table object check
                self.assertEquals(self.table.name,expected)
                newname = self.table.name
            else:
                # we know the object's name isn't consistent: just assign it
                newname = expected
            # Table DB check
            #table = self.refresh_table(self.table,newname)
            self.meta.clear()
            self.table = Table(newname, self.meta, autoload=True)
            self.assertEquals(self.table.name,expected)
        def assert_index_name(expected,skip_object_check=False):
            if not skip_object_check:
                # Index object check
                self.assertEquals(self.index.name,expected)
            else:
                # object is inconsistent
                self.index.name = expected
            # Index DB check
            #TODO

        try:
            # Table renames
            assert_table_name(name1)
            rename_table(self.table,name2)
            assert_table_name(name2)
            self.table.rename(name1)
            assert_table_name(name1)
            # ..by just the string
            rename_table(name1,name2,engine=self.engine)
            assert_table_name(name2,True)   # object not updated
    
            # Index renames
            if self.url.startswith('sqlite') or self.url.startswith('mysql'):
                self.assertRaises(changeset.exceptions.NotSupportedError,
                    self.index.rename,xname2)
            else:
                assert_index_name(xname1)
                rename_index(self.index,xname2,engine=self.engine)
                assert_index_name(xname2)
                self.index.rename(xname1)
                assert_index_name(xname1)
                # ..by just the string
                rename_index(xname1,xname2,engine=self.engine)
                assert_index_name(xname2,True)

        finally:
            #self.index.drop()
            if self.table.exists():
                self.table.drop()

class TestColumnChange(fixture.DB):
    level=fixture.DB.CONNECT
    table_name = 'tmp_colchange'

    def setUp(self):
        fixture.DB.setUp(self)
        self._connect(self.url)
        #self.engine.echo=True
        self.meta = MetaData(self.engine)
        self.table = Table(self.table_name,self.meta,
            Column('id',Integer,primary_key=True),
            Column('data',String(40),server_default=PassiveDefault("tluafed"),nullable=True),
        )
        if self.table.exists():
            self.table.drop()
        try:
            self.table.create()
        except sqlalchemy.exceptions.SQLError,e:
            # SQLite: database schema has changed
            if not self.url.startswith('sqlite://'):
                raise
    def tearDown(self):
        if self.table.exists():
            try:
                self.table.drop(self.engine)
            except sqlalchemy.exceptions.SQLError,e:
                # SQLite: database schema has changed
                if not self.url.startswith('sqlite://'):
                    raise
        #self.engine.echo=False
        fixture.DB.tearDown(self)

    @fixture.usedb(supported='sqlite')
    def test_sqlite_not_supported(self):
        self.assertRaises(changeset.exceptions.NotSupportedError,
            self.table.c.data.alter,server_default=PassiveDefault('tluafed'))
        self.assertRaises(changeset.exceptions.NotSupportedError,
            self.table.c.data.alter,nullable=True)
        self.assertRaises(changeset.exceptions.NotSupportedError,
            self.table.c.data.alter,type=String(21))
        self.assertRaises(changeset.exceptions.NotSupportedError,
            self.table.c.data.alter,name='atad')

    @fixture.usedb(not_supported='sqlite')
    def test_rename(self):
        """Can rename a column"""
        def num_rows(col,content):
            return len(list(self.table.select(col==content).execute()))
        # Table content should be preserved in changed columns
        content = "fgsfds"
        self.engine.execute(self.table.insert(),data=content,id=42)
        self.assertEquals(num_rows(self.table.c.data,content),1)

        # ...as a function, given a column object and the new name
        alter_column(self.table.c.data, name='atad')
        self.refresh_table(self.table.name)
        self.assert_('data' not in self.table.c.keys())
        self.assert_('atad' in self.table.c.keys())
        #self.assertRaises(AttributeError,getattr,self.table.c,'data')
        self.table.c.atad   # Should not raise exception
        self.assertEquals(num_rows(self.table.c.atad,content),1)

        # ...as a method, given a new name
        self.table.c.atad.alter(name='data')
        self.refresh_table(self.table.name)
        self.assert_('atad' not in self.table.c.keys())
        self.table.c.data # Should not raise exception
        self.assertEquals(num_rows(self.table.c.data,content),1)

        # ...as a function, given a new object
        col = Column('atad',String(40),server_default=self.table.c.data.server_default)
        alter_column(self.table.c.data, col)
        self.refresh_table(self.table.name)
        self.assert_('data' not in self.table.c.keys())
        self.table.c.atad   # Should not raise exception
        self.assertEquals(num_rows(self.table.c.atad,content),1)

        # ...as a method, given a new object
        col = Column('data',String(40),server_default=self.table.c.atad.server_default)
        self.table.c.atad.alter(col)
        self.refresh_table(self.table.name)
        self.assert_('atad' not in self.table.c.keys())
        self.table.c.data   # Should not raise exception
        self.assertEquals(num_rows(self.table.c.data,content),1)
        
    @fixture.usedb(not_supported='sqlite')
    def xtest_fk(self):
        """Can add/drop foreign key constraints to/from a column
        Not supported
        """
        self.assert_(self.table.c.data.foreign_key is None)

        # add
        self.table.c.data.alter(foreign_key=ForeignKey(self.table.c.id))
        self.refresh_table(self.table.name)
        self.assert_(self.table.c.data.foreign_key is not None)

        # drop
        self.table.c.data.alter(foreign_key=None)
        self.refresh_table(self.table.name)
        self.assert_(self.table.c.data.foreign_key is None)

    @fixture.usedb(not_supported='sqlite')
    def test_type(self):
        """Can change a column's type"""
        # Entire column definition given
        self.table.c.data.alter(Column('data',String(42)))
        self.refresh_table(self.table.name)
        self.assert_(isinstance(self.table.c.data.type,String))
        self.assertEquals(self.table.c.data.type.length,42)

        # Just the new type
        self.table.c.data.alter(type=String(21))
        self.refresh_table(self.table.name)
        self.assert_(isinstance(self.table.c.data.type,String))
        self.assertEquals(self.table.c.data.type.length,21)

        # Different type
        self.assert_(isinstance(self.table.c.id.type,Integer))
        self.assertEquals(self.table.c.id.nullable,False)
        self.table.c.id.alter(type=String(20))
        self.assertEquals(self.table.c.id.nullable,False)
        self.refresh_table(self.table.name)
        self.assert_(isinstance(self.table.c.id.type,String))

    @fixture.usedb(not_supported='sqlite')
    def test_default(self):
        """Can change a column's server_default value (PassiveDefaults only)
        Only PassiveDefaults are changed here: others are managed by the 
        application / by SA
        """
        #self.engine.echo=True
        self.assertEquals(self.table.c.data.server_default.arg,'tluafed')

        # Just the new default
        default = 'my_default'
        self.table.c.data.alter(server_default=PassiveDefault(default))
        self.refresh_table(self.table.name)
        #self.assertEquals(self.table.c.data.server_default.arg,default)
        # TextClause returned by autoload
        self.assert_(default in str(self.table.c.data.server_default.arg))

        # Column object
        default = 'your_default'
        self.table.c.data.alter(Column('data',String(40),server_default=PassiveDefault(default)))
        self.refresh_table(self.table.name)
        self.assert_(default in str(self.table.c.data.server_default.arg))

        # Remove default
        self.table.c.data.alter(server_default=None)
        self.refresh_table(self.table.name)
        # server_default isn't necessarily None for Oracle
        #self.assert_(self.table.c.data.server_default is None,self.table.c.data.server_default)
        self.engine.execute(self.table.insert(),id=11)
        row = self.table.select().execute().fetchone()
        self.assert_(row['data'] is None,row['data'])
        

    @fixture.usedb(not_supported='sqlite')
    def test_null(self):
        """Can change a column's null constraint"""
        self.assertEquals(self.table.c.data.nullable,True)
        
        # Column object
        self.table.c.data.alter(Column('data',String(40),nullable=False))
        self.table.nullable=None
        self.refresh_table(self.table.name)
        self.assertEquals(self.table.c.data.nullable,False)

        # Just the new status
        self.table.c.data.alter(nullable=True)
        self.refresh_table(self.table.name)
        self.assertEquals(self.table.c.data.nullable,True)

    @fixture.usedb(not_supported='sqlite')
    def xtest_pk(self):
        """Can add/drop a column to/from its table's primary key
        Not supported
        """
        self.assertEquals(len(self.table.primary_key),1)

        # Entire column definition
        self.table.c.data.alter(Column('data',String,primary_key=True))
        self.refresh_table(self.table.name)
        self.assertEquals(len(self.table.primary_key),2)

        # Just the new status
        self.table.c.data.alter(primary_key=False)
        self.refresh_table(self.table.name)
        self.assertEquals(len(self.table.primary_key),1)

class TestColumnDelta(fixture.Base):
    def test_deltas(self):
        def mkcol(name='id',type=String,*p,**k):
            return Column(name,type,*p,**k)
        col_orig = mkcol(primary_key=True)

        def verify(expected,original,*p,**k):
            delta = _ColumnDelta(original,*p,**k)
            result = delta.keys()
            result.sort()
            self.assertEquals(expected,result)
            return delta

        verify([],col_orig)
        verify(['name'],col_orig,'ids')
        # Parameters are always executed, even if they're 'unchanged'
        # (We can't assume given column is up-to-date)
        verify(['name','primary_key','type'],col_orig,'id',Integer,primary_key=True)
        verify(['name','primary_key','type'],col_orig,name='id',type=Integer,primary_key=True)

        # Can compare two columns and find differences
        col_new = mkcol(name='ids',primary_key=True)
        verify([],col_orig,col_orig)
        verify(['name'],col_orig,col_orig,'ids')
        verify(['name'],col_orig,col_orig,name='ids')
        verify(['name'],col_orig,col_new)
        verify(['name','type'],col_orig,col_new,type=String)
        # Change name, given an up-to-date definition and the current name
        delta = verify(['name'],col_new,current_name='id')
        self.assertEquals(delta.get('name'),'ids')
        # Change other params at the same time
        verify(['name','type'],col_new,current_name='id',type=String)
        # Type comparisons
        verify([],mkcol(type=String),mkcol(type=String))
        verify(['type'],mkcol(type=String),mkcol(type=Integer))
        verify(['type'],mkcol(type=String),mkcol(type=String(42)))
        verify([],mkcol(type=String(42)),mkcol(type=String(42)))
        verify(['type'],mkcol(type=String(24)),mkcol(type=String(42)))
        # Other comparisons
        verify(['primary_key'],mkcol(nullable=False),mkcol(primary_key=True))
        # PK implies nullable=False
        verify(['nullable','primary_key'],mkcol(nullable=True),mkcol(primary_key=True))
        verify([],mkcol(primary_key=True),mkcol(primary_key=True))
        verify(['nullable'],mkcol(nullable=True),mkcol(nullable=False))
        verify([],mkcol(nullable=True),mkcol(nullable=True))
        verify(['default'],mkcol(default=None),mkcol(default='42'))
        verify([],mkcol(default=None),mkcol(default=None))
        verify([],mkcol(default='42'),mkcol(default='42'))

class TestDriver(fixture.DB):
    @fixture.usedb()
    def test_driver(self):
        self.assertEquals(self.url.split(':',1)[0],driver(self.engine))
