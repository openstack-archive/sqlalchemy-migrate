#!/usr/bin/env python
# -*- coding: utf-8 -*-

from migrate.versioning.base import log,operations
from migrate.versioning import pathed,exceptions


class BaseScript(pathed.Pathed):
    """Base class for other types of scripts
    All scripts have the following properties:

    source (script.source())
      The source code of the script
    version (script.version())
      The version number of the script
    operations (script.operations())
      The operations defined by the script: upgrade(), downgrade() or both.
      Returns a tuple of operations.
      Can also check for an operation with ex. script.operation(Script.ops.up)
    """

    def __init__(self,path):
        log.info('Loading script %s...' % path)
        self.verify(path)
        super(BaseScript, self).__init__(path)
        log.info('Script %s loaded successfully' % path)
    
    @classmethod
    def verify(cls,path):
        """Ensure this is a valid script, or raise InvalidScriptError
        This version simply ensures the script file's existence
        """
        try:
            cls.require_found(path)
        except:
            raise exceptions.InvalidScriptError(path)

    def source(self):
        fd = open(self.path)
        ret = fd.read()
        fd.close()
        return ret

    def run(self, engine):
        raise NotImplementedError()
