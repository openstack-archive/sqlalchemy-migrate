#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings
from decorator import decorator
from pkg_resources import EntryPoint

from migrate.versioning import exceptions
from migrate.versioning.util.keyedinstance import KeyedInstance
from migrate.versioning.util.importpath import import_path


def loadModel(dotted_name):
    ''' Import module and use module-level variable -- assume model is of form "mod1.mod2:varname". '''
    if isinstance(dotted_name, basestring):
        if ':' not in dotted_name:
            # backwards compatibility
            warnings.warn('model should be in form of module.model:User'
                'and not module.model.User', DeprecationWarning)
            dotted_name = ':'.join(dotted_name.rsplit('.', 1))
        return EntryPoint.parse('x=%s' % dotted_name).load(False)
    else:
        # Assume it's already loaded.
        return dotted_name

def asbool(obj):
    """Do everything to use object as bool"""
    if isinstance(obj, (str, unicode)):
        obj = obj.strip().lower()
        if obj in ['true', 'yes', 'on', 'y', 't', '1']:
            return True
        elif obj in ['false', 'no', 'off', 'n', 'f', '0']:
            return False
        else:
            raise ValueError("String is not true/false: %r" % obj)
    return bool(obj)

def guess_obj_type(obj):
    """Do everything to guess object type from string"""
    result = None

    try:
        result = asbool(obj)
    except:
        pass

    if result is None:
        try:
            result = int(obj)
        except:
            pass

    if result is not None:
        return result
    else:
        return obj

@decorator
def catch_known_errors(f, *a, **kw):
    """Decorator that catches known api usage errors"""

    try:
        f(*a, **kw)
    except exceptions.PathFoundError, e:
        raise exceptions.KnownError("The path %s already exists" % e.args[0])
