from migrate.changeset import ansisql
from sqlalchemy.databases import postgres as sa_base
#import sqlalchemy as sa

PGSchemaGenerator = sa_base.PGSchemaGenerator

class PGSchemaGeneratorMixin(object):
    def _do_quote_table_identifier(self, identifier):
        return identifier
    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier

class PGColumnGenerator(PGSchemaGenerator,ansisql.ANSIColumnGenerator, PGSchemaGeneratorMixin):
    pass

class PGColumnDropper(ansisql.ANSIColumnDropper, PGSchemaGeneratorMixin):
    pass

class PGSchemaChanger(ansisql.ANSISchemaChanger, PGSchemaGeneratorMixin):
    pass

class PGConstraintGenerator(ansisql.ANSIConstraintGenerator, PGSchemaGeneratorMixin):
    pass

class PGConstraintDropper(ansisql.ANSIConstraintDropper, PGSchemaGeneratorMixin):
    pass

class PGDialect(ansisql.ANSIDialect):
    columngenerator = PGColumnGenerator
    columndropper = PGColumnDropper
    schemachanger = PGSchemaChanger
    constraintgenerator = PGConstraintGenerator
    constraintdropper = PGConstraintDropper
