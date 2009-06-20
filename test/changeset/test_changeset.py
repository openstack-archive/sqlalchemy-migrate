#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlalchemy
from sqlalchemy import *

from migrate import changeset
from migrate.changeset import *
from migrate.changeset.schema import _ColumnDelta
from test import fixture


# TODO: test quoting
# TODO: test all other constraints on create column, test defaults

class TestAddDropColumn(fixture.DB):
    """Test add/drop column through all possible interfaces
    also test for constraints"""
    level = fixture.DB.CONNECT
    table_name = 'tmp_adddropcol'
    table_int = 0

    def _setup(self, url):
        super(TestAddDropColumn, self)._setup(url)
        self.meta = MetaData()
        self.table = Table(self.table_name, self.meta,
            Column('id', Integer, unique=True),
        )
        self.meta.bind = self.engine
        if self.engine.has_table(self.table.name):
            self.table.drop()
        self.table.create()

    def _teardown(self):
        if self.engine.has_table(self.table.name):
            self.table.drop()
        self.meta.clear()
        super(TestAddDropColumn,self)._teardown()

    def run_(self, create_column_func, drop_column_func, *col_p, **col_k):
        col_name = 'data'

        def assert_numcols(num_of_expected_cols):
            # number of cols should be correct in table object and in database
            self.refresh_table(self.table_name)
            result = len(self.table.c)
            
            self.assertEquals(result, num_of_expected_cols),
            if col_k.get('primary_key', None):
                # new primary key: check its length too
                result = len(self.table.primary_key)
                self.assertEquals(result, num_of_expected_cols)
            
        assert_numcols(1)
        if len(col_p) == 0:
            col_p = [String(40)]
        col = Column(col_name, *col_p, **col_k)
        create_column_func(col)
        assert_numcols(2)
        col2 = getattr(self.table.c, col_name)
        self.assertEquals(col2, col)
        drop_column_func(col2)
        assert_numcols(1)

    @fixture.usedb()
    def test_undefined(self):
        """Add/drop columns not yet defined in the table"""
        def add_func(col):
            return create_column(col, self.table)
        def drop_func(col):
            return drop_column(col, self.table)
        return self.run_(add_func, drop_func)

    @fixture.usedb()
    def test_defined(self):
        """Add/drop columns already defined in the table"""
        def add_func(col):
            self.meta.clear()
            self.table = Table(self.table_name, self.meta,
                Column('id', Integer, primary_key=True),
                col,
            )
            return create_column(col)
        def drop_func(col):
            return drop_column(col)
        return self.run_(add_func, drop_func)

    @fixture.usedb()
    def test_method_bound(self):
        """Add/drop columns via column methods; columns bound to a table
        ie. no table parameter passed to function
        """
        def add_func(col):
            self.assert_(col.table is None, col.table)
            self.table.append_column(col)
            return col.create()
        def drop_func(col):
            #self.assert_(col.table is None,col.table)
            #self.table.append_column(col)
            return col.drop()
        return self.run_(add_func, drop_func)

    @fixture.usedb()
    def test_method_notbound(self):
        """Add/drop columns via column methods; columns not bound to a table"""
        def add_func(col):
            return col.create(self.table)
        def drop_func(col):
            return col.drop(self.table)
        return self.run_(add_func, drop_func)

    @fixture.usedb()
    def test_tablemethod_obj(self):
        """Add/drop columns via table methods; by column object"""
        def add_func(col):
            return self.table.create_column(col)
        def drop_func(col):
            return self.table.drop_column(col)
        return self.run_(add_func, drop_func)

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
        return self.run_(add_func, drop_func)
        
    @fixture.usedb()
    def test_byname(self):
        """Add/drop columns via functions; by table object and column name"""
        def add_func(col):
            self.table.append_column(col)
            return create_column(col.name, self.table)
        def drop_func(col):
            return drop_column(col.name, self.table)
        return self.run_(add_func, drop_func)

    @fixture.usedb()
    def test_drop_column_not_in_table(self):
        """Drop column by name"""
        def add_func(col):
            return self.table.create_column(col)
        def drop_func(col):
            self.table.c.remove(col)
            return self.table.drop_column(col.name)
        self.run_(add_func, drop_func)

    @fixture.usedb()
    def test_fk(self):
        """Can create columns with foreign keys"""
        # create FK's target
        reftable = Table('tmp_ref', self.meta,
            Column('id', Integer, primary_key=True),
        )
        if self.engine.has_table(reftable.name):
            reftable.drop()
        reftable.create()

        # create column with fk
        col = Column('data', Integer, ForeignKey(reftable.c.id))
        if self.url.startswith('sqlite'):
            self.assertRaises(changeset.exceptions.NotSupportedError,
                col.create, self.table)
        else:
            col.create(self.table)

            # check if constraint is added
            for cons in self.table.constraints:
                if isinstance(cons, sqlalchemy.schema.ForeignKeyConstraint):
                    break
            else:
                self.fail('No constraint found')

            # TODO: test on db level if constraints work

            self.assertEqual(reftable.c.id.name, col.foreign_keys[0].column.name)
            col.drop(self.table)

        if self.engine.has_table(reftable.name):
            reftable.drop()

    @fixture.usedb(not_supported='sqlite')
    def test_pk(self):
        """Can create columns with primary key"""
        col = Column('data', Integer)
        self.assertRaises(changeset.exceptions.InvalidConstraintError,
            col.create, self.table, primary_key_name=True)
        col.create(self.table, primary_key_name='data_pkey')

        # check if constraint was added (cannot test on objects)
        self.table.insert(values={'data': 4}).execute()
        try:
            self.table.insert(values={'data': 4}).execute()
        except sqlalchemy.exc.IntegrityError:
            pass
        else:
            self.fail()

        col.drop()
    
    @fixture.usedb(not_supported='mysql')
    def test_check(self):
        """Can create columns with check constraint"""
        col = Column('data',
                     Integer,
                     sqlalchemy.schema.CheckConstraint('data > 4'))
        col.create(self.table)

        # check if constraint was added (cannot test on objects)
        self.table.insert(values={'data': 5}).execute()
        try:
            self.table.insert(values={'data': 3}).execute()
        except sqlalchemy.exc.IntegrityError:
            pass
        else:
            self.fail()

        col.drop()

    @fixture.usedb(not_supported='sqlite')
    def test_unique(self):
        """Can create columns with unique constraint"""
        self.assertRaises(changeset.exceptions.InvalidConstraintError,
            Column('data', Integer, unique=True).create, self.table)
        col = Column('data', Integer)
        col.create(self.table, unique_name='data_unique')

        # check if constraint was added (cannot test on objects)
        self.table.insert(values={'data': 5}).execute()
        try:
            self.table.insert(values={'data': 5}).execute()
        except sqlalchemy.exc.IntegrityError:
            pass
        else:
            self.fail()

        col.drop(self.table)

    @fixture.usedb()
    def test_index(self):
        """Can create columns with indexes"""
        self.assertRaises(changeset.exceptions.InvalidConstraintError,
            Column('data', Integer).create, self.table, index_name=True)
        col = Column('data', Integer)
        col.create(self.table, index_name='ix_data')

        # check if index was added
        self.table.insert(values={'data': 5}).execute()
        try:
            self.table.insert(values={'data': 5}).execute()
        except sqlalchemy.exc.IntegrityError:
            pass
        else:
            self.fail()

        col.drop()

    @fixture.usedb()
    def test_server_defaults(self):
        """Can create columns with server_default values"""
        col = Column('data', String(244), server_default='foobar')
        col.create(self.table)

        self.table.insert().execute()
        row = self.table.select(autocommit=True).execute().fetchone()
        self.assertEqual(u'foobar', row['data'])

        col.drop()

    # TODO: test sequence
    # TODO: test that if column is appended on creation and removed on deletion


class TestRename(fixture.DB):
    """Tests for table and index rename methods"""
    level = fixture.DB.CONNECT
    meta = MetaData()

    def _setup(self, url):
        super(TestRename, self)._setup(url)
        self.meta.bind = self.engine

    @fixture.usedb()
    def test_rename_table(self):
        """Tables can be renamed"""
        c_name = 'col_1'
        table_name1 = 'name_one'
        table_name2 = 'name_two'
        index_name1 = 'x' + table_name1
        index_name2 = 'x' + table_name2

        self.meta.clear()
        self.column = Column(c_name, Integer)
        self.table = Table(table_name1, self.meta, self.column)
        self.index = Index(index_name1, self.column, unique=False)

        if self.engine.has_table(self.table.name):
            self.table.drop()
        if self.engine.has_table(table_name2):
            tmp = Table(table_name2, self.meta, autoload=True)
            tmp.drop()
            tmp.deregister()
            del tmp
        self.table.create()

        def assert_table_name(expected, skip_object_check=False):
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
            self.meta.clear()
            self.table = Table(newname, self.meta, autoload=True)
            self.assertEquals(self.table.name, expected)

        def assert_index_name(expected, skip_object_check=False):
            if not skip_object_check:
                # Index object check
                self.assertEquals(self.index.name, expected)
            else:
                # object is inconsistent
                self.index.name = expected
            # TODO: Index DB check
            
        try:
            # Table renames
            assert_table_name(table_name1)
            rename_table(self.table, table_name2)
            assert_table_name(table_name2)
            self.table.rename(table_name1)
            assert_table_name(table_name1)

            # test by just the string
            rename_table(table_name1, table_name2, engine=self.engine)
            assert_table_name(table_name2, True)   # object not updated
    
            # Index renames
            if self.url.startswith('sqlite') or self.url.startswith('mysql'):
                self.assertRaises(changeset.exceptions.NotSupportedError,
                    self.index.rename, index_name2)
            else:
                assert_index_name(index_name1)
                rename_index(self.index, index_name2, engine=self.engine)
                assert_index_name(index_name2)
                self.index.rename(index_name1)
                assert_index_name(index_name1)

                # test by just the string
                rename_index(index_name1, index_name2, engine=self.engine)
                assert_index_name(index_name2, True)

        finally:
            if self.table.exists():
                self.table.drop()


class TestColumnChange(fixture.DB):
    level = fixture.DB.CONNECT
    table_name = 'tmp_colchange'

    def _setup(self, url):
        super(TestColumnChange, self)._setup(url)
        self.meta = MetaData(self.engine)
        self.table = Table(self.table_name, self.meta,
            Column('id', Integer, primary_key=True),
            Column('data', String(40), server_default=DefaultClause("tluafed"),
                   nullable=True),
        )
        if self.table.exists():
            self.table.drop()
        try:
            self.table.create()
        except sqlalchemy.exceptions.SQLError, e:
            # SQLite: database schema has changed
            if not self.url.startswith('sqlite://'):
                raise

    def _teardown(self):
        if self.table.exists():
            try:
                self.table.drop(self.engine)
            except sqlalchemy.exceptions.SQLError,e:
                # SQLite: database schema has changed
                if not self.url.startswith('sqlite://'):
                    raise
        super(TestColumnChange, self)._teardown()

    @fixture.usedb()
    def test_rename(self):
        """Can rename a column"""
        def num_rows(col, content):
            return len(list(self.table.select(col == content).execute()))
        # Table content should be preserved in changed columns
        content = "fgsfds"
        self.engine.execute(self.table.insert(), data=content, id=42)
        self.assertEquals(num_rows(self.table.c.data, content), 1)

        # ...as a function, given a column object and the new name
        alter_column('data', name='data2', table=self.table)
        self.refresh_table()
        alter_column(self.table.c.data2, name='atad')
        self.refresh_table(self.table.name)
        self.assert_('data' not in self.table.c.keys())
        self.assert_('atad' in self.table.c.keys())
        #self.assertRaises(AttributeError,getattr,self.table.c,'data')
        self.table.c.atad   # Should not raise exception
        self.assertEquals(num_rows(self.table.c.atad, content), 1)

        # ...as a method, given a new name
        self.table.c.atad.alter(name='data')
        self.refresh_table(self.table.name)
        self.assert_('atad' not in self.table.c.keys())
        self.table.c.data # Should not raise exception
        self.assertEquals(num_rows(self.table.c.data, content), 1)

        # ...as a function, given a new object
        col = Column('atad', String(40), server_default=self.table.c.data.server_default)
        alter_column(self.table.c.data, col)
        self.refresh_table(self.table.name)
        self.assert_('data' not in self.table.c.keys())
        self.table.c.atad   # Should not raise exception
        self.assertEquals(num_rows(self.table.c.atad, content), 1)

        # ...as a method, given a new object
        col = Column('data', String(40), server_default=self.table.c.atad.server_default)
        self.table.c.atad.alter(col)
        self.refresh_table(self.table.name)
        self.assert_('atad' not in self.table.c.keys())
        self.table.c.data   # Should not raise exception
        self.assertEquals(num_rows(self.table.c.data,content), 1)
        
    #@fixture.usedb()
    #def test_fk(self):
    #    """Can add/drop foreign key constraints to/from a column
    #    Not supported
    #    """
    #    self.assert_(self.table.c.data.foreign_key is None)

    #    # add
    #    self.table.c.data.alter(foreign_key=ForeignKey(self.table.c.id))
    #    self.refresh_table(self.table.name)
    #    self.assert_(self.table.c.data.foreign_key is not None)

    #    # drop
    #    self.table.c.data.alter(foreign_key=None)
    #    self.refresh_table(self.table.name)
    #    self.assert_(self.table.c.data.foreign_key is None)

    @fixture.usedb()
    def test_type(self):
        """Can change a column's type"""
        # Entire column definition given
        self.table.c.data.alter(Column('data', String(42)))
        self.refresh_table(self.table.name)
        self.assert_(isinstance(self.table.c.data.type, String))
        self.assertEquals(self.table.c.data.type.length, 42)

        # Just the new type
        self.table.c.data.alter(type=String(21))
        self.refresh_table(self.table.name)
        self.assert_(isinstance(self.table.c.data.type, String))
        self.assertEquals(self.table.c.data.type.length, 21)

        # Different type
        self.assert_(isinstance(self.table.c.id.type, Integer))
        self.assertEquals(self.table.c.id.nullable, False)
        self.table.c.id.alter(type=String(20))
        self.assertEquals(self.table.c.id.nullable, False)
        self.refresh_table(self.table.name)
        self.assert_(isinstance(self.table.c.id.type, String))

    @fixture.usedb(not_supported='mysql')
    def test_default(self):
        """Can change a column's server_default value (DefaultClauses only)
        Only DefaultClauses are changed here: others are managed by the 
        application / by SA
        """
        #self.engine.echo=True
        self.assertEquals(self.table.c.data.server_default.arg, 'tluafed')

        # Just the new default 
        default = 'my_default'
        self.table.c.data.alter(server_default=DefaultClause(default))
        self.refresh_table(self.table.name)
        #self.assertEquals(self.table.c.data.server_default.arg,default)
        # TextClause returned by autoload
        self.assert_(default in str(self.table.c.data.server_default.arg))

        # Column object
        default = 'your_default'
        self.table.c.data.alter(Column('data', String(40), server_default=DefaultClause(default)))
        self.refresh_table(self.table.name)
        self.assert_(default in str(self.table.c.data.server_default.arg))

        # Remove default
        self.table.c.data.alter(server_default=None)
        self.refresh_table(self.table.name)
        # server_default isn't necessarily None for Oracle
        #self.assert_(self.table.c.data.server_default is None,self.table.c.data.server_default)
        self.engine.execute(self.table.insert(), id=11)
        row = self.table.select().execute().fetchone()
        self.assert_(row['data'] is None, row['data'])
        

    @fixture.usedb()
    def test_null(self):
        """Can change a column's null constraint"""
        self.assertEquals(self.table.c.data.nullable, True)
        
        # Column object
        self.table.c.data.alter(Column('data', String(40), nullable=False))
        self.table.nullable=None
        self.refresh_table(self.table.name)
        self.assertEquals(self.table.c.data.nullable, False)

        # Just the new status
        self.table.c.data.alter(nullable=True)
        self.refresh_table(self.table.name)
        self.assertEquals(self.table.c.data.nullable, True)

    #@fixture.usedb()
    #def test_pk(self):
    #    """Can add/drop a column to/from its table's primary key
    #    Not supported
    #    """
    #    self.engine.echo = True
    #    self.assertEquals(len(self.table.primary_key), 1)

    #    # Entire column definition
    #    self.table.c.data.alter(Column('data', String, primary_key=True))
    #    self.refresh_table(self.table.name)
    #    self.assertEquals(len(self.table.primary_key), 2)

    #    # Just the new status
    #    self.table.c.data.alter(primary_key=False)
    #    self.refresh_table(self.table.name)
    #    self.assertEquals(len(self.table.primary_key), 1)


class TestColumnDelta(fixture.Base):
    def test_deltas(self):
        def mkcol(name='id', type=String, *p, **k):
            return Column(name, type, *p, **k)

        def verify(expected, original, *p, **k):
            delta = _ColumnDelta(original, *p, **k)
            result = delta.keys()
            result.sort()
            self.assertEquals(expected, result)
            return delta

        col_orig = mkcol(primary_key=True)

        verify([], col_orig)
        verify(['name'], col_orig, 'ids')
        # Parameters are always executed, even if they're 'unchanged'
        # (We can't assume given column is up-to-date)
        verify(['name', 'primary_key', 'type'],
               col_orig, 'id', Integer, primary_key=True)
        verify(['name', 'primary_key', 'type'],
               col_orig, name='id', type=Integer, primary_key=True)

        # Can compare two columns and find differences
        col_new = mkcol(name='ids', primary_key=True)
        verify([], col_orig, col_orig)
        verify(['name'], 'ids', table=Table('test', MetaData()), name='hey')
        verify(['name'], col_orig, col_orig, 'ids')
        verify(['name'], col_orig, col_orig, name='ids')
        verify(['name'], col_orig, col_new)
        verify(['name','type'], col_orig, col_new, type=String)

        # Change name, given an up-to-date definition and the current name
        delta = verify(['name'], col_new, current_name='id')
        self.assertEquals(delta.get('name'), 'ids')

        # Change other params at the same time
        verify(['name', 'type'], col_new, current_name='id', type=String)

        # Type comparisons
        verify([], mkcol(type=String), mkcol(type=String))
        verify(['type'], mkcol(type=String), mkcol(type=Integer))
        verify(['type'], mkcol(type=String), mkcol(type=String(42)))
        verify([], mkcol(type=String(42)), mkcol(type=String(42)))
        verify(['type'], mkcol(type=String(24)), mkcol(type=String(42)))

        # Other comparisons
        verify(['primary_key'], mkcol(nullable=False), mkcol(primary_key=True))

        # PK implies nullable=False
        verify(['nullable', 'primary_key'],
               mkcol(nullable=True), mkcol(primary_key=True))
        verify([], mkcol(primary_key=True), mkcol(primary_key=True))
        verify(['nullable'], mkcol(nullable=True), mkcol(nullable=False))
        verify([], mkcol(nullable=True), mkcol(nullable=True))
        verify(['default'], mkcol(default=None), mkcol(default='42'))
        verify([], mkcol(default=None), mkcol(default=None))
        verify([], mkcol(default='42'), mkcol(default='42'))
