"""
   MySQL database specific implementations of changeset classes.
"""

from migrate.changeset import ansisql, exceptions, SQLA_06
from sqlalchemy.databases import mysql as sa_base

if not SQLA_06:
    MySQLSchemaGenerator = sa_base.MySQLSchemaGenerator
else:
    MySQLSchemaGenerator = sa_base.MySQLDDLCompiler

class MySQLColumnGenerator(MySQLSchemaGenerator, ansisql.ANSIColumnGenerator):
    pass


class MySQLColumnDropper(ansisql.ANSIColumnDropper):
    pass


class MySQLSchemaChanger(MySQLSchemaGenerator, ansisql.ANSISchemaChanger):

    def visit_column(self, delta):
        table = delta.table
        colspec = self.get_column_specification(delta.result_column)
        old_col_name = self.preparer.quote(delta.current_name, table.quote)

        self.start_alter_table(table)

        self.append("CHANGE COLUMN %s " % old_col_name)
        self.append(colspec)
        self.execute()

    def visit_index(self, param):
        # If MySQL can do this, I can't find how
        raise exceptions.NotSupportedError("MySQL cannot rename indexes")


class MySQLConstraintGenerator(ansisql.ANSIConstraintGenerator):
    pass

if SQLA_06:
    class MySQLConstraintDropper(MySQLSchemaGenerator, ansisql.ANSIConstraintDropper):
        def visit_migrate_check_constraint(self, *p, **k):
            raise exceptions.NotSupportedError("MySQL does not support CHECK"
                " constraints, use triggers instead.")

else:
    class MySQLConstraintDropper(ansisql.ANSIConstraintDropper):

        def visit_migrate_primary_key_constraint(self, constraint):
            self.start_alter_table(constraint)
            self.append("DROP PRIMARY KEY")
            self.execute()

        def visit_migrate_foreign_key_constraint(self, constraint):
            self.start_alter_table(constraint)
            self.append("DROP FOREIGN KEY ")
            constraint.name = self.get_constraint_name(constraint)
            self.append(self.preparer.format_constraint(constraint))
            self.execute()

        def visit_migrate_check_constraint(self, *p, **k):
            raise exceptions.NotSupportedError("MySQL does not support CHECK"
                " constraints, use triggers instead.")

        def visit_migrate_unique_constraint(self, constraint, *p, **k):
            self.start_alter_table(constraint)
            self.append('DROP INDEX ')
            constraint.name = self.get_constraint_name(constraint)
            self.append(self.preparer.format_constraint(constraint))
            self.execute()


class MySQLDialect(ansisql.ANSIDialect):
    columngenerator = MySQLColumnGenerator
    columndropper = MySQLColumnDropper
    schemachanger = MySQLSchemaChanger
    constraintgenerator = MySQLConstraintGenerator
    constraintdropper = MySQLConstraintDropper
