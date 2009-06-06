#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings
from decorator import decorator
from pkg_resources import EntryPoint

from sqlalchemy import create_engine

from migrate.versioning import exceptions
from migrate.versioning.util.keyedinstance import KeyedInstance
from migrate.versioning.util.importpath import import_path


def load_model(dotted_name):
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
    if obj in (True, False):
        return bool(obj)
    else:
        raise ValueError("String is not true/false: %r" % obj)

def guess_obj_type(obj):
    """Do everything to guess object type from string"""
    result = None

    try:
        result = int(obj)
    except:
        pass

    if result is None:
        try:
            result = asbool(obj)
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

def construct_engine(url, **opts):
    """Constructs and returns SQLAlchemy engine.

    Currently, there are 2 ways to pass create_engine options to api functions:

        * keyword parameters (starting with `engine_arg_*`)
        * python dictionary of options (`engine_dict`)

    NOTE: keyword parameters override `engine_dict` values.

    .. versionadded:: 0.5.4
    """
    # TODO: include docs
    
    # get options for create_engine
    if opts.get('engine_dict') and isinstance(opts['engine_dict'], dict):
        kwargs = opts['engine_dict']
    else:
        kwargs = dict()

    # DEPRECATED: handle echo the old way
    echo = asbool(opts.get('echo', False))
    if echo:
        warnings.warn('echo=True parameter is deprecated, pass '
            'engine_arg_echo=True or engine_dict={"echo": True}',
            DeprecationWarning)
        kwargs['echo'] = echo
    
    # parse keyword arguments
    for key, value in opts.iteritems():
        if key.startswith('engine_arg_'):
            kwargs[key[11:]] = guess_obj_type(value)
    
    return create_engine(url, **kwargs)
