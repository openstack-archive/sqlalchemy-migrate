"""
   Oracle database specific implementations of changeset classes.
"""

from migrate.changeset import ansisql, exceptions
from sqlalchemy.databases import oracle as sa_base
import sqlalchemy as sa

OracleSchemaGenerator = sa_base.OracleSchemaGenerator


class OracleColumnGenerator(OracleSchemaGenerator,
                            ansisql.ANSIColumnGenerator):
    pass


class OracleColumnDropper(ansisql.ANSIColumnDropper):
    pass


class OracleSchemaChanger(OracleSchemaGenerator, ansisql.ANSISchemaChanger):

    def get_column_specification(self, column, **kwargs):
        # Ignore the NOT NULL generated
        override_nullable = kwargs.pop('override_nullable', None)
        if override_nullable:
            orig = column.nullable
            column.nullable = True
        ret = super(OracleSchemaChanger, self).get_column_specification(
            column, **kwargs)
        if override_nullable:
            column.nullable = orig
        return ret

    def visit_column(self, delta):
        keys = delta.keys()
        if 'type' in keys or 'nullable' in keys or 'default' in keys \
                or 'server_default' in keys:
            self._run_subvisit(delta, self._visit_column_change)
        if 'name' in keys:
            self._run_subvisit(delta, self._visit_column_name)

    def _visit_column_change(self, table_name, col_name, delta):
        if not hasattr(delta, 'result_column'):
            # Oracle needs the whole column definition, not just a
            # lone name/type
            raise exceptions.NotSupportedError(
                "A column object is required to do this")

        column = delta.result_column
        # Oracle cannot drop a default once created, but it can set it
        # to null.  We'll do that if default=None
        # http://forums.oracle.com/forums/message.jspa?\
        # messageID=1273234#1273234
        dropdefault_hack = (column.server_default is None \
                                and 'server_default' in delta.keys())
        # Oracle apparently doesn't like it when we say "not null" if
        # the column's already not null. Fudge it, so we don't need a
        # new function
        notnull_hack = ((not column.nullable) \
                            and ('nullable' not in delta.keys()))
        # We need to specify NULL if we're removing a NOT NULL
        # constraint
        null_hack = (column.nullable and ('nullable' in delta.keys()))

        if dropdefault_hack:
            column.server_default = sa.PassiveDefault(sa.sql.null())
        if notnull_hack:
            column.nullable = True
        colspec=self.get_column_specification(column,
                                              override_nullable=null_hack)
        if null_hack:
            colspec += ' NULL'
        if notnull_hack:
            column.nullable = False
        if dropdefault_hack:
            column.server_default = None

        self.start_alter_table(table_name)
        self.append("MODIFY ")
        self.append(colspec)


class OracleConstraintCommon(object):

    def get_constraint_name(self, cons):
        # Oracle constraints can't guess their name like other DBs
        if not cons.name:
            raise exceptions.NotSupportedError(
                "Oracle constraint names must be explicitly stated")
        return cons.name


class OracleConstraintGenerator(OracleConstraintCommon,
                                ansisql.ANSIConstraintGenerator):
    pass


class OracleConstraintDropper(OracleConstraintCommon,
                              ansisql.ANSIConstraintDropper):
    pass


class OracleDialect(ansisql.ANSIDialect):
    columngenerator = OracleColumnGenerator
    columndropper = OracleColumnDropper
    schemachanger = OracleSchemaChanger
    constraintgenerator = OracleConstraintGenerator
    constraintdropper = OracleConstraintDropper
