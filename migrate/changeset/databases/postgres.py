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
    def _do_quote_table_identifier(self, identifier):
        return identifier
    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier

class PGColumnDropper(ansisql.ANSIColumnDropper, PGSchemaGeneratorMixin):
    def _do_quote_table_identifier(self, identifier):
        return identifier
    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier

class PGSchemaChanger(ansisql.ANSISchemaChanger, PGSchemaGeneratorMixin):
    def _do_quote_table_identifier(self, identifier):
        return identifier
    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier

class PGConstraintGenerator(ansisql.ANSIConstraintGenerator, PGSchemaGeneratorMixin):
    def _do_quote_table_identifier(self, identifier):
        return identifier
    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier

class PGConstraintDropper(ansisql.ANSIConstraintDropper, PGSchemaGeneratorMixin):
    def _do_quote_table_identifier(self, identifier):
        return identifier
    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier

class PGDialect(ansisql.ANSIDialect):
    columngenerator = PGColumnGenerator
    columndropper = PGColumnDropper
    schemachanger = PGSchemaChanger
    constraintgenerator = PGConstraintGenerator
    constraintdropper = PGConstraintDropper
