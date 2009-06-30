#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from migrate.versioning.genmodel import *
from migrate.versioning.exceptions import *

from test import fixture


class TestModelGenerator(fixture.Pathed, fixture.DB):
    level = fixture.DB.TXN
