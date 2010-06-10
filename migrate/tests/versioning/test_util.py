#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from sqlalchemy import *

from migrate.tests import fixture
from migrate.versioning.util import *


class TestUtil(fixture.Pathed):

    def test_construct_engine(self):
        """Construct engine the smart way"""
        url = 'sqlite://'

        engine = construct_engine(url)
        self.assert_(engine.name == 'sqlite')

        # keyword arg
        engine = construct_engine(url, engine_arg_encoding=True)
        self.assertTrue(engine.dialect.encoding)

        # dict
        engine = construct_engine(url, engine_dict={'encoding': True})
        self.assertTrue(engine.dialect.encoding)

        # engine parameter
        engine_orig = create_engine('sqlite://')
        engine = construct_engine(engine_orig)
        self.assertEqual(engine, engine_orig)

        # test precedance
        engine = construct_engine(url, engine_dict={'encoding': False},
            engine_arg_encoding=True)
        self.assertTrue(engine.dialect.encoding)

        # deprecated echo=True parameter
        engine = construct_engine(url, echo='True')
        self.assertTrue(engine.echo)

        # unsupported argument
        self.assertRaises(ValueError, construct_engine, 1)

    def test_asbool(self):
        """test asbool parsing"""
        result = asbool(True)
        self.assertEqual(result, True)

        result = asbool(False)
        self.assertEqual(result, False)

        result = asbool('y')
        self.assertEqual(result, True)

        result = asbool('n')
        self.assertEqual(result, False)

        self.assertRaises(ValueError, asbool, 'test')
        self.assertRaises(ValueError, asbool, object)


    def test_load_model(self):
        """load model from dotted name"""
        model_path = os.path.join(self.temp_usable_dir, 'test_load_model.py')

        f = open(model_path, 'w')
        f.write("class FakeFloat(int): pass")
        f.close()

        FakeFloat = load_model('test_load_model.FakeFloat')
        self.assert_(isinstance(FakeFloat(), int))

        FakeFloat = load_model('test_load_model:FakeFloat')
        self.assert_(isinstance(FakeFloat(), int))

        FakeFloat = load_model(FakeFloat)
        self.assert_(isinstance(FakeFloat(), int))

    def test_guess_obj_type(self):
        """guess object type from string"""
        result = guess_obj_type('7')
        self.assertEqual(result, 7)

        result = guess_obj_type('y')
        self.assertEqual(result, True)

        result = guess_obj_type('test')
        self.assertEqual(result, 'test')
