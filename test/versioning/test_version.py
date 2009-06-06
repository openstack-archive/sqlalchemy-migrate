#!/usr/bin/env python
# -*- coding: utf-8 -*-

from test import fixture
from migrate.versioning.version import *


class TestVerNum(fixture.Base):
    def test_invalid(self):
        """Disallow invalid version numbers"""
        versions = ('-1', -1, 'Thirteen', '')
        for version in versions:
            self.assertRaises(ValueError, VerNum, version)

    def test_is(self):
        """Two version with the same number should be equal"""
        a = VerNum(1)
        b = VerNum(1)
        self.assert_(a is b)

        self.assertEqual(VerNum(VerNum(2)), VerNum(2))

    def test_add(self):
        self.assertEqual(VerNum(1) + VerNum(1), VerNum(2))
        self.assertEqual(VerNum(1) + 1, 2)
        self.assertEqual(VerNum(1) + 1, '2')
        self.assert_(isinstance(VerNum(1) + 1, VerNum))

    def test_sub(self):
        self.assertEqual(VerNum(1) - 1, 0)
        self.assert_(isinstance(VerNum(1) - 1, VerNum))
        self.assertRaises(ValueError, lambda: VerNum(0) - 1)

    def test_eq(self):
        """Two versions are equal"""
        self.assertEqual(VerNum(1), VerNum('1'))
        self.assertEqual(VerNum(1), 1)
        self.assertEqual(VerNum(1), '1')
        self.assertNotEqual(VerNum(1), 2)

    def test_ne(self):
        self.assert_(VerNum(1) != 2)
        self.assertFalse(VerNum(1) != 1)

    def test_lt(self):
        self.assertFalse(VerNum(1) < 1)
        self.assert_(VerNum(1) < 2)
        self.assertFalse(VerNum(2) < 1)

    def test_le(self):
        self.assert_(VerNum(1) <= 1)
        self.assert_(VerNum(1) <= 2)
        self.assertFalse(VerNum(2) <= 1)

    def test_gt(self):
        self.assertFalse(VerNum(1) > 1)
        self.assertFalse(VerNum(1) > 2)
        self.assert_(VerNum(2) > 1)

    def test_ge(self):
        self.assert_(VerNum(1) >= 1)
        self.assert_(VerNum(2) >= 1)
        self.assertFalse(VerNum(1) >= 2)
        
class TestVersion(fixture.Pathed):

    def setUp(self):
        super(TestVersion, self).setUp()

    def test_str_to_filename(self):
        self.assertEquals(str_to_filename(''), '')
        self.assertEquals(str_to_filename('__'), '_')
        self.assertEquals(str_to_filename('a'), 'a')
        self.assertEquals(str_to_filename('Abc Def'), 'Abc_Def')
        self.assertEquals(str_to_filename('Abc "D" Ef'), 'Abc_D_Ef')
        self.assertEquals(str_to_filename("Abc's Stuff"), 'Abc_s_Stuff')
        self.assertEquals(str_to_filename("a      b"), 'a_b')

    def test_collection(self):
        """Let's see how we handle versions collection"""
        coll = Collection(self.temp_usable_dir)
        coll.create_new_python_version("foo bar")
        coll.create_new_sql_version("postgres")
        coll.create_new_sql_version("sqlite")
        coll.create_new_python_version("")

        self.assertEqual(coll.latest, 4)
        self.assertEqual(len(coll.versions), 4)
        self.assertEqual(coll.version(4), coll.version(coll.latest))

        coll2 = Collection(self.temp_usable_dir)
        self.assertEqual(coll.versions, coll2.versions)

    #def test_collection_unicode(self):
    #    pass

    def test_create_new_python_version(self):
        coll = Collection(self.temp_usable_dir)
        coll.create_new_python_version("foo bar")

        ver = coll.version()
        self.assert_(ver.script().source())

    def test_create_new_sql_version(self):
        coll = Collection(self.temp_usable_dir)
        coll.create_new_sql_version("sqlite")

        ver = coll.version()
        ver_up = ver.script('sqlite', 'upgrade')
        ver_down = ver.script('sqlite', 'downgrade')
        ver_up.source()
        ver_down.source()

    def test_selection(self):
        """Verify right sql script is selected"""
        
        # Create empty directory.
        path = self.tmp_repos()
        os.mkdir(path)
        
        # Create files -- files must be present or you'll get an exception later.
        python_file = '001_initial_.py'
        sqlite_upgrade_file = '001_sqlite_upgrade.sql'
        default_upgrade_file = '001_default_upgrade.sql'
        for file_ in [sqlite_upgrade_file, default_upgrade_file, python_file]:
            filepath = '%s/%s' % (path, file_)
            open(filepath, 'w').close()

        ver = Version(1, path, [sqlite_upgrade_file])
        self.assertEquals(os.path.basename(ver.script('sqlite', 'upgrade').path), sqlite_upgrade_file)
    
        ver = Version(1, path, [default_upgrade_file])
        self.assertEquals(os.path.basename(ver.script('default', 'upgrade').path), default_upgrade_file)
    
        ver = Version(1, path, [sqlite_upgrade_file, default_upgrade_file])
        self.assertEquals(os.path.basename(ver.script('sqlite', 'upgrade').path), sqlite_upgrade_file)
    
        ver = Version(1, path, [sqlite_upgrade_file, default_upgrade_file, python_file])
        self.assertEquals(os.path.basename(ver.script('postgres', 'upgrade').path), default_upgrade_file)

        ver = Version(1, path, [sqlite_upgrade_file, python_file])
        self.assertEquals(os.path.basename(ver.script('postgres', 'upgrade').path), python_file)
