# -*- coding: utf-8 -*-

import os

from sqlalchemy import *
from nose.tools import eq_

from migrate.versioning import schemadiff

from migrate.tests import fixture

class SchemaDiffBase(fixture.DB):

    level = fixture.DB.CONNECT
    
    def _make_table(self,*cols,**kw):
        self.table = Table('xtable', self.meta,
            Column('id',Integer(), primary_key=True),
            *cols
        )
        if kw.get('create',True):
            self.table.create()
        
    def _assert_diff(self,col_A,col_B):
        self._make_table(col_A)
        self.meta.clear()
        self._make_table(col_B,create=False)
        diff = self._run_diff()
        # print diff
        self.assertTrue(diff)
        eq_(1,len(diff.tables_different))
        td = diff.tables_different.values()[0]
        eq_(1,len(td.columns_different))
        cd = td.columns_different.values()[0]
        eq_(('Schema diffs:\n'
             '  table with differences: xtable\n'
             '    column with differences: data\n'
             '         model: %r\n'
             '      database: %r')%(
                cd.col_A,
                cd.col_B
                ),str(diff))
        
class Test_getDiffOfModelAgainstDatabase(SchemaDiffBase):
    
    def _run_diff(self,**kw):
        return schemadiff.getDiffOfModelAgainstDatabase(
            self.meta, self.engine, **kw
            )
    
    @fixture.usedb()
    def test_table_missing_in_db(self):
        self._make_table(create=False)
        diff = self._run_diff()
        self.assertTrue(diff)
        eq_('Schema diffs:\n  tables missing from database: xtable',
            str(diff))

    @fixture.usedb()
    def test_table_missing_in_model(self):
        self._make_table()
        self.meta.clear()
        diff = self._run_diff()
        self.assertTrue(diff)
        eq_('Schema diffs:\n  tables missing from model: xtable',
            str(diff))

    @fixture.usedb()
    def test_column_missing_in_db(self):
        # db
        Table('xtable', self.meta,
              Column('id',Integer(), primary_key=True),
              ).create()
        self.meta.clear()
        # model
        self._make_table(
            Column('xcol',Integer()),
            create=False
            )
        # run diff
        diff = self._run_diff()
        self.assertTrue(diff)
        eq_('Schema diffs:\n'
            '  table with differences: xtable\n'
            '    database missing these columns: xcol',
            str(diff))

    @fixture.usedb()
    def test_column_missing_in_model(self):
        # db
        self._make_table(
            Column('xcol',Integer()),
            )
        self.meta.clear()
        # model
        self._make_table(
            create=False
            )
        # run diff
        diff = self._run_diff()
        self.assertTrue(diff)
        eq_('Schema diffs:\n'
            '  table with differences: xtable\n'
            '    model missing these columns: xcol',
            str(diff))

    @fixture.usedb()
    def test_exclude_tables(self):
        # db
        Table('ytable', self.meta,
              Column('id',Integer(), primary_key=True),
              ).create()
        Table('ztable', self.meta,
              Column('id',Integer(), primary_key=True),
              ).create()
        self.meta.clear()
        # model
        self._make_table(
            create=False
            )
        Table('ztable', self.meta,
              Column('id',Integer(), primary_key=True),
              )
        # run diff
        diff = self._run_diff(excludeTables=('xtable','ytable'))
        # ytable only in database
        # xtable only in model
        # ztable identical on both
        # ...so we expect no diff!
        self.assertFalse(diff)
        eq_('No schema diffs',str(diff))

    @fixture.usedb()
    def test_identical_just_pk(self):
        self._make_table()
        diff = self._run_diff()
        self.assertFalse(diff)
        eq_('No schema diffs',str(diff))


    @fixture.usedb()
    def test_different_type(self):
        self._assert_diff(
            Column('data', String(10)),
            Column('data', Integer()),
            )

    @fixture.usedb()
    def test_int_vs_float(self):
        self._assert_diff(
            Column('data', Integer()),
            Column('data', Float()),
            )

    @fixture.usedb()
    def test_float_vs_numeric(self):
        self._assert_diff(
            Column('data', Float()),
            Column('data', Numeric()),
            )

    @fixture.usedb()
    def test_numeric_precision(self):
        self._assert_diff(
            Column('data', Numeric(precision=5)),
            Column('data', Numeric(precision=6)),
            )

    @fixture.usedb()
    def test_numeric_scale(self):
        self._assert_diff(
            Column('data', Numeric(precision=6,scale=0)),
            Column('data', Numeric(precision=6,scale=1)),
            )

    @fixture.usedb()
    def test_string_length(self):
        self._assert_diff(
            Column('data', String(10)),
            Column('data', String(20)),
            )
        
    @fixture.usedb()
    def test_integer_identical(self):
        self._make_table(
            Column('data', Integer()),
            )
        diff = self._run_diff()
        eq_('No schema diffs',str(diff))
        self.assertFalse(diff)
        
    @fixture.usedb()
    def test_string_identical(self):
        self._make_table(
            Column('data', String(10)),
            )
        diff = self._run_diff()
        eq_('No schema diffs',str(diff))
        self.assertFalse(diff)

    @fixture.usedb()
    def test_text_identical(self):
        self._make_table(
            Column('data', Text(255)),
            )
        diff = self._run_diff()
        eq_('No schema diffs',str(diff))
        self.assertFalse(diff)

