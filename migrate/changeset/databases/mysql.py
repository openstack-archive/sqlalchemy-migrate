"""
   MySQL database specific implementations of changeset classes.
"""

from migrate.changeset import ansisql, exceptions
from sqlalchemy.databases import mysql as sa_base
#import sqlalchemy as sa

MySQLSchemaGenerator = sa_base.MySQLSchemaGenerator


class MySQLColumnGenerator(MySQLSchemaGenerator, ansisql.ANSIColumnGenerator):

    def _do_quote_table_identifier(self, identifier):
        return '%s'%identifier
    pass


class MySQLColumnDropper(ansisql.ANSIColumnDropper):

    def _do_quote_table_identifier(self, identifier):
        return '%s'%identifier

    def _do_quote_column_identifier(self, identifier):
        return '%s'%identifier


class MySQLSchemaChanger(MySQLSchemaGenerator, ansisql.ANSISchemaChanger):

    def visit_column(self, delta):
        keys = delta.keys()
        if 'type' in keys or 'nullable' in keys or 'name' in keys:
            self._run_subvisit(delta, self._visit_column_change)
        if 'server_default' in keys:
            # Column name might have changed above
            col_name = delta.get('name', delta.current_name)
            self._run_subvisit(delta, self._visit_column_default,
                               col_name=col_name)

    def _visit_column_change(self, table_name, col_name, delta):
        if not hasattr(delta, 'result_column'):
            # Mysql needs the whole column definition, not just a lone
            # name/type
            raise exceptions.NotSupportedError(
                "A column object is required to do this")

        column = delta.result_column
        # needed by get_column_specification
        if not column.table:
            column.table = delta.table
        colspec = self.get_column_specification(column)
        self.start_alter_table(table_name)
        self.append("CHANGE COLUMN ")
        self.append(col_name)
        self.append(' ')
        self.append(colspec)

    def visit_index(self, param):
        # If MySQL can do this, I can't find how
        raise exceptions.NotSupportedError("MySQL cannot rename indexes")

    def _do_quote_table_identifier(self, identifier):
        return '%s'%identifier


class MySQLConstraintGenerator(ansisql.ANSIConstraintGenerator):

    def _do_quote_table_identifier(self, identifier):
        return '%s'%identifier


class MySQLConstraintDropper(ansisql.ANSIConstraintDropper):
    #def visit_constraint(self,constraint):
    #    if isinstance(constraint,sqlalchemy.schema.PrimaryKeyConstraint):
    #        return self._visit_constraint_pk(constraint)
    #    elif isinstance(constraint,sqlalchemy.schema.ForeignKeyConstraint):
    #        return self._visit_constraint_fk(constraint)
    #    return super(MySQLConstraintDropper,self).visit_constraint(constraint)

    def visit_migrate_primary_key_constraint(self, constraint):
        self.start_alter_table(constraint)
        self.append("DROP PRIMARY KEY")
        self.execute()

    def visit_migrate_foreign_key_constraint(self, constraint):
        self.start_alter_table(constraint)
        self.append("DROP FOREIGN KEY ")
        self.append(constraint.name)
        self.execute()

    def _do_quote_table_identifier(self, identifier):
        return '%s'%identifier


class MySQLDialect(ansisql.ANSIDialect):
    columngenerator = MySQLColumnGenerator
    columndropper = MySQLColumnDropper
    schemachanger = MySQLSchemaChanger
    constraintgenerator = MySQLConstraintGenerator
    constraintdropper = MySQLConstraintDropper
