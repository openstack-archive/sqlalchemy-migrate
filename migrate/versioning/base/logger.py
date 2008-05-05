"""Manages logging (to stdout) for our versioning system.
"""
import logging

log=logging.getLogger('migrate.versioning')
log.setLevel(logging.WARNING)
log.addHandler(logging.StreamHandler())

__all__=['log','logging']
