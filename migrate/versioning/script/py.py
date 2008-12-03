import shutil
#import migrate.run
from migrate.versioning import exceptions, genmodel, schemadiff
from migrate.versioning.base import operations
from migrate.versioning.template import template
from migrate.versioning.script import base
from migrate.versioning.util import import_path, loadModel
import migrate

class PythonScript(base.BaseScript):
    @classmethod
    def create(cls,path,**opts):
        """Create an empty migration script"""
        cls.require_notfound(path)

        # TODO: Use the default script template (defined in the template
        # module) for now, but we might want to allow people to specify a
        # different one later.
        template_file = None
        src = template.get_script(template_file)
        shutil.copy(src,path)

    @classmethod
    def make_update_script_for_model(cls,engine,oldmodel,model,repository,**opts):
        """Create a migration script"""
        
        # Compute differences.
        if isinstance(repository, basestring):
            from migrate.versioning.repository import Repository  # oh dear, an import cycle!
            repository=Repository(repository)
        oldmodel = loadModel(oldmodel)
        model = loadModel(model)
        diff = schemadiff.getDiffOfModelAgainstModel(oldmodel, model, engine, excludeTables=[repository.version_table])
        decls, upgradeCommands, downgradeCommands = genmodel.ModelGenerator(diff).toUpgradeDowngradePython()

        # Store differences into file.
        template_file = None
        src = template.get_script(template_file)
        contents = open(src).read()
        search = 'def upgrade():'
        contents = contents.replace(search, decls + '\n\n' + search, 1)
        if upgradeCommands: contents = contents.replace('    pass', upgradeCommands, 1)
        if downgradeCommands: contents = contents.replace('    pass', downgradeCommands, 1)
        return contents

    @classmethod
    def verify_module(cls,path):
        """Ensure this is a valid script, or raise InvalidScriptError"""
        # Try to import and get the upgrade() func
        try:
            module=import_path(path)
        except:
            # If the script itself has errors, that's not our problem
            raise
        try:
            assert callable(module.upgrade)
        except Exception,e:
            raise exceptions.InvalidScriptError(path+': %s'%str(e))
        return module

    def _get_module(self):
        if not hasattr(self,'_module'):
            self._module = self.verify_module(self.path)
        return self._module
    module = property(_get_module)


    def _func(self,funcname):
        fn = getattr(self.module, funcname, None)
        if not fn:
            msg = "The function %s is not defined in this script"
            raise exceptions.ScriptError(msg%funcname)
        return fn
            
    def run(self,engine,step):
        if step > 0:
            op = 'upgrade'
        elif step < 0:
            op = 'downgrade'
        else:
            raise exceptions.ScriptError("%d is not a valid step"%step)
        funcname = base.operations[op]
        
        migrate.migrate_engine = engine
        #migrate.run.migrate_engine = migrate.migrate_engine = engine
        func = self._func(funcname)
        func()
        migrate.migrate_engine = None
        #migrate.run.migrate_engine = migrate.migrate_engine = None
