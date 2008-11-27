from migrate.changeset import ansisql
from sqlalchemy.databases import postgres as sa_base
#import sqlalchemy as sa

PGSchemaGenerator = sa_base.PGSchemaGenerator

class PGColumnGenerator(PGSchemaGenerator,ansisql.ANSIColumnGenerator):
    def _do_quote_table_identifier(self, identifier):
        return identifier

class PGColumnDropper(ansisql.ANSIColumnDropper):
    def _do_quote_table_identifier(self, identifier):
        return identifier

class PGSchemaChanger(ansisql.ANSISchemaChanger):
    def _do_quote_table_identifier(self, identifier):
        return identifier
    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier


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
