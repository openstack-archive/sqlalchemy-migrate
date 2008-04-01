from keyedinstance import KeyedInstance
from importpath import import_path

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
    
