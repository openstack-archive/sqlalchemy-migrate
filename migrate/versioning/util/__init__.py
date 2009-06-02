#!/usr/bin/env python
# -*- coding: utf-8 -*-

from decorator import decorator

from migrate.versioning import exceptions
from migrate.versioning.util.keyedinstance import KeyedInstance
from migrate.versioning.util.importpath import import_path


def loadModel(model):
    ''' Import module and use module-level variable -- assume model is of form "mod1.mod2.varname". '''
    if isinstance(model, basestring):
        varname = model.split('.')[-1]
        modules = '.'.join(model.split('.')[:-1])
        module = __import__(modules, globals(), {}, ['dummy-not-used'], -1)
        return getattr(module, varname)
    else:
        # Assume it's already loaded.
        return model

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

@decorator
def catch_known_errors(f, *a, **kw):
    """Decorator that catches known api usage errors"""

    try:
        f(*a, **kw)
    except exceptions.PathFoundError, e:
        raise exceptions.KnownError("The path %s already exists" % e.args[0])
