"""Each migration script must import everything in this file."""
#from sqlalchemy import *
#from migrate.changeset import *
#from migrate.versioning import logengine

#__all__=[
#    'engine',
#]

# 'migrate_engine' is assigned elsewhere, and used during scripts
#migrate_engine = None

def driver(engine):
    """Given an engine, return the name of the database driving it: 
    
    'postgres','mysql','sqlite'...
    """
    from warnings import warn
    warn("Use engine.name instead; http://erosson.com/migrate/trac/ticket/80",
        DeprecationWarning)
    return engine.name
