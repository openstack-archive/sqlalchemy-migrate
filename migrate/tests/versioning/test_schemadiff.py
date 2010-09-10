# -*- coding: utf-8 -*-

import os

from sqlalchemy import *
from nose.tools import eq_

from migrate.versioning import schemadiff
from migrate.changeset import SQLA_06

from migrate.tests import fixture

class Test_getDiffOfModelAgainstDatabase(fixture.DB):

    level = fixture.DB.CONNECT
    
    def _make_table(self,*cols,**kw):
        self.table = Table('xtable', self.meta,
            Column('id',Integer(), primary_key=True),
            *cols
        )
        if kw.get('create',True):
            self.table.create()
        
    def _run_diff(self,**kw):
        return schemadiff.getDiffOfModelAgainstDatabase(
            self.meta, self.engine, **kw
            )
    @fixture.usedb()
    def test_getDiffOfModelAgainstDatabase_table_missing_in_db(self):
        self._make_table(create=False)
        diff = self._run_diff()
        self.assertTrue(diff)
        eq_('Schema diffs:\n  tables missing from database: xtable',
            str(diff))

    @fixture.usedb()
    def test_getDiffOfModelAgainstDatabase_table_missing_in_model(self):
        self._make_table()
        self.meta.clear()
        diff = self._run_diff()
        self.assertTrue(diff)
        eq_('Schema diffs:\n  tables missing from model: xtable',
            str(diff))

    @fixture.usedb()
    def test_getDiffOfModelAgainstDatabase_column_missing_in_db(self):
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
        eq_('Schema diffs:\n    xtable missing columns from database: xcol',
            str(diff))

    @fixture.usedb()
    def test_getDiffOfModelAgainstDatabase_column_missing_in_model(self):
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
        eq_('Schema diffs:\n    xtable missing columns from model: xcol',
            str(diff))

    @fixture.usedb()
    def test_getDiffOfModelAgainstDatabase_exclude_tables(self):
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
    def test_getDiffOfModelAgainstDatabase_identical_just_pk(self):
        self._make_table()
        diff = self._run_diff()
        self.assertFalse(diff)
        eq_('No schema diffs',str(diff))
        
    @fixture.usedb()
    def test_getDiffOfModelAgainstDatabase_integer_identical(self):
        self._make_table(
            Column('data', Integer()),
            )
        diff = self._run_diff()
        eq_('No schema diffs',str(diff))
        self.assertFalse(diff)
        
    @fixture.usedb()
    def test_getDiffOfModelAgainstDatabase_string_identical(self):
        self._make_table(
            Column('data', String(10)),
            )
        diff = self._run_diff()
        eq_('No schema diffs',str(diff))
        self.assertFalse(diff)

    @fixture.usedb()
    def test_getDiffOfModelAgainstDatabase_text_identical(self):
        self._make_table(
            Column('data', Text(255)),
            )
        diff = self._run_diff()
        eq_('No schema diffs',str(diff))
        self.assertFalse(diff)
