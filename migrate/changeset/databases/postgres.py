from migrate.changeset import ansisql
from sqlalchemy.databases import postgres as sa_base
#import sqlalchemy as sa

PGSchemaGenerator = sa_base.PGSchemaGenerator

class PGColumnGenerator(PGSchemaGenerator,ansisql.ANSIColumnGenerator):
    pass
class PGColumnDropper(ansisql.ANSIColumnDropper):
    pass
class PGSchemaChanger(ansisql.ANSISchemaChanger):
    pass
class PGConstraintGenerator(ansisql.ANSIConstraintGenerator):
    pass
class PGConstraintDropper(ansisql.ANSIConstraintDropper):
    pass

class PGDialect(ansisql.ANSIDialect):
    columngenerator = PGColumnGenerator
    columndropper = PGColumnDropper
    schemachanger = PGSchemaChanger
    constraintgenerator = PGConstraintGenerator
    constraintdropper = PGConstraintDropper
