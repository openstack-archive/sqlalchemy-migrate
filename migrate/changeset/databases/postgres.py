"""
   `PostgreSQL`_ database specific implementations of changeset classes.

   .. _`PostgreSQL`: http://www.postgresql.org/
"""
from migrate.changeset import ansisql
from sqlalchemy.databases import postgres as sa_base
#import sqlalchemy as sa


PGSchemaGenerator = sa_base.PGSchemaGenerator


class PGSchemaGeneratorMixin(object):
    """Common code used by the PostgreSQL specific classes."""

    def _do_quote_table_identifier(self, identifier):
        return identifier

    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier


class PGColumnGenerator(PGSchemaGenerator, ansisql.ANSIColumnGenerator,
                        PGSchemaGeneratorMixin):
    """PostgreSQL column generator implementation."""
    pass


class PGColumnDropper(ansisql.ANSIColumnDropper, PGSchemaGeneratorMixin):
    """PostgreSQL column dropper implementation."""
    pass


class PGSchemaChanger(ansisql.ANSISchemaChanger, PGSchemaGeneratorMixin):
    """PostgreSQL schema changer implementation."""
    pass


class PGConstraintGenerator(ansisql.ANSIConstraintGenerator,
                            PGSchemaGeneratorMixin):
    """PostgreSQL constraint generator implementation."""
    pass


class PGConstraintDropper(ansisql.ANSIConstraintDropper,
                          PGSchemaGeneratorMixin):
    """PostgreSQL constaint dropper implementation."""
    pass


class PGDialect(ansisql.ANSIDialect):
    columngenerator = PGColumnGenerator
    columndropper = PGColumnDropper
    schemachanger = PGSchemaChanger
    constraintgenerator = PGConstraintGenerator
    constraintdropper = PGConstraintDropper
