#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
from StringIO import StringIO

import migrate
from migrate.versioning import exceptions, genmodel, schemadiff
from migrate.versioning.base import operations
from migrate.versioning.template import template
from migrate.versioning.script import base
from migrate.versioning.util import import_path, load_model, construct_engine


class PythonScript(base.BaseScript):
    """Base for Python scripts"""

    @classmethod
    def create(cls, path, **opts):
        """Create an empty migration script at specified path
        
        :returns: :class:`PythonScript instance <migrate.versioning.script.py.PythonScript>`"""
        cls.require_notfound(path)

        # TODO: Use the default script template (defined in the template
        # module) for now, but we might want to allow people to specify a
        # different one later.
        template_file = None
        src = template.get_script(template_file)
        shutil.copy(src, path)

        return cls(path)

    @classmethod
    def make_update_script_for_model(cls, engine, oldmodel,
                                     model, repository, **opts):
        """Create a migration script based on difference between two SA models.
        
        :param repository: path to migrate repository
        :param oldmodel: dotted.module.name:SAClass or SAClass object
        :param model: dotted.module.name:SAClass or SAClass object
        :param engine: SQLAlchemy engine
        :type repository: string or :class:`Repository instance <migrate.versioning.repository.Repository>`
        :type oldmodel: string or Class
        :type model: string or Class
        :type engine: Engine instance
        :returns: Upgrade / Downgrade script
        :rtype: string
        """
        
        if isinstance(repository, basestring):
            # oh dear, an import cycle!
            from migrate.versioning.repository import Repository
            repository = Repository(repository)

        oldmodel = load_model(oldmodel)
        model = load_model(model)

        # Compute differences.
        diff = schemadiff.getDiffOfModelAgainstModel(
            oldmodel,
            model,
            engine,
            excludeTables=[repository.version_table])
        # TODO: diff can be False (there is no difference?)
        decls, upgradeCommands, downgradeCommands = \
            genmodel.ModelGenerator(diff).toUpgradeDowngradePython()

        # Store differences into file.
        # TODO: add custom templates
        src = template.get_script(None)
        f = open(src)
        contents = f.read()
        f.close()

        # generate source
        search = 'def upgrade():'
        contents = contents.replace(search, '\n\n'.join((decls, search)), 1)
        if upgradeCommands:
            contents = contents.replace('    pass', upgradeCommands, 1)
        if downgradeCommands:
            contents = contents.replace('    pass', downgradeCommands, 1)
        return contents

    @classmethod
    def verify_module(cls, path):
        """Ensure path is a valid script
        
        :param path: Script location
        :type path: string

        :raises: :exc:`InvalidScriptError <migrate.versioning.exceptions.InvalidScriptError>`
        :returns: Python module
        """
        # Try to import and get the upgrade() func
        try:
            module = import_path(path)
        except:
            # If the script itself has errors, that's not our problem
            raise
        try:
            assert callable(module.upgrade)
        except Exception, e:
            raise exceptions.InvalidScriptError(path + ': %s' % str(e))
        return module

    def preview_sql(self, url, step, **args):
        """Mocks SQLAlchemy Engine to store all executed calls in a string 
        and runs :meth:`PythonScript.run <migrate.versioning.script.py.PythonScript.run>`
        
        :returns: SQL file
        """
        buf = StringIO()
        args['engine_arg_strategy'] = 'mock'
        args['engine_arg_executor'] = lambda s, p='': buf.write(s + p)
        engine = construct_engine(url, **args)

        self.run(engine, step)

        return buf.getvalue()
            
    def run(self, engine, step):
        """Core method of Script file. 
        Exectues :func:`update` or :func:`downgrade` functions

        :param engine: SQLAlchemy Engine
        :param step: Operation to run
        :type engine: string
        :type step: int
        """
        if step > 0:
            op = 'upgrade'
        elif step < 0:
            op = 'downgrade'
        else:
            raise exceptions.ScriptError("%d is not a valid step" % step)
        funcname = base.operations[op]
        
        migrate.migrate_engine = engine
        #migrate.run.migrate_engine = migrate.migrate_engine = engine
        func = self._func(funcname)
        func()
        migrate.migrate_engine = None
        #migrate.run.migrate_engine = migrate.migrate_engine = None

    @property
    def module(self):
        """Calls :meth:`migrate.versioning.script.py.verify_module`
        and returns it.
        """
        if not hasattr(self, '_module'):
            self._module = self.verify_module(self.path)
        return self._module

    def _func(self, funcname):
        try:
            return getattr(self.module, funcname)
        except AttributeError:
            msg = "The function %s is not defined in this script"
            raise exceptions.ScriptError(msg % funcname)
