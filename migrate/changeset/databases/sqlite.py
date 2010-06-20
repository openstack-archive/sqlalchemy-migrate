"""
   `SQLite`_ database specific implementations of changeset classes.

   .. _`SQLite`: http://www.sqlite.org/
"""
from UserDict import DictMixin
from copy import copy

from sqlalchemy.databases import sqlite as sa_base

from migrate.changeset import ansisql, exceptions, SQLA_06

if not SQLA_06:
    SQLiteSchemaGenerator = sa_base.SQLiteSchemaGenerator
else:
    SQLiteSchemaGenerator = sa_base.SQLiteDDLCompiler

class SQLiteCommon(object):

    def _not_supported(self, op):
        raise exceptions.NotSupportedError("SQLite does not support "
            "%s; see http://www.sqlite.org/lang_altertable.html" % op)


class SQLiteHelper(SQLiteCommon):

    def visit_column(self, delta):
        if isinstance(delta, DictMixin):
            column = delta.result_column
            table = self._to_table(delta.table)
        else:
            column = delta
            table = self._to_table(column.table)
        table_name = self.preparer.format_table(table)

        # we remove all constraints, indexes so it doesnt recreate them
        ixbackup = copy(table.indexes)
        consbackup = copy(table.constraints)
        table.indexes = set()
        table.constraints = set()

        self.append('ALTER TABLE %s RENAME TO migration_tmp' % table_name)
        self.execute()

        insertion_string = self._modify_table(table, column, delta)

        table.create()
        self.append(insertion_string % {'table_name': table_name})
        self.execute()
        self.append('DROP TABLE migration_tmp')
        self.execute()

        # restore indexes, constraints
        table.indexes = ixbackup
        table.constraints = consbackup

class SQLiteColumnGenerator(SQLiteSchemaGenerator, SQLiteCommon, 
                            ansisql.ANSIColumnGenerator):
    """SQLite ColumnGenerator"""

    def add_foreignkey(self, constraint):
        """Does not support ALTER TABLE ADD FOREIGN KEY"""
        self._not_supported("ALTER TABLE ADD CONSTRAINT")


class SQLiteColumnDropper(SQLiteHelper, ansisql.ANSIColumnDropper):
    """SQLite ColumnDropper"""

    def _modify_table(self, table, column, delta):
        columns = ' ,'.join(map(self.preparer.format_column, table.columns))
        return 'INSERT INTO %(table_name)s SELECT ' + columns + \
            ' from migration_tmp'


class SQLiteSchemaChanger(SQLiteHelper, ansisql.ANSISchemaChanger):
    """SQLite SchemaChanger"""

    def _modify_table(self, table, column, delta):
        column = table.columns[delta.current_name]
        return 'INSERT INTO %(table_name)s SELECT * from migration_tmp'

    def visit_index(self, index):
        """Does not support ALTER INDEX"""
        self._not_supported('ALTER INDEX')


class SQLiteConstraintGenerator(ansisql.ANSIConstraintGenerator, SQLiteCommon):

    def visit_migrate_primary_key_constraint(self, constraint):
        tmpl = "CREATE UNIQUE INDEX %s ON %s ( %s )"
        cols = ', '.join(map(self.preparer.format_column, constraint.columns))
        tname = self.preparer.format_table(constraint.table)
        name = self.get_constraint_name(constraint)
        msg = tmpl % (name, tname, cols)
        self.append(msg)
        self.execute()

    def visit_migrate_foreign_key_constraint(self, *p, **k):
        self._not_supported('ALTER TABLE ADD CONSTRAINT')

    def visit_migrate_unique_constraint(self, *p, **k):
        self._not_supported('ALTER TABLE ADD CONSTRAINT')


class SQLiteConstraintDropper(ansisql.ANSIColumnDropper,
                              SQLiteCommon,
                              ansisql.ANSIConstraintCommon):

    def visit_migrate_primary_key_constraint(self, constraint):
        tmpl = "DROP INDEX %s "
        name = self.get_constraint_name(constraint)
        msg = tmpl % (name)
        self.append(msg)
        self.execute()

    def visit_migrate_foreign_key_constraint(self, *p, **k):
        self._not_supported('ALTER TABLE DROP CONSTRAINT')

    def visit_migrate_check_constraint(self, *p, **k):
        self._not_supported('ALTER TABLE DROP CONSTRAINT')

    def visit_migrate_unique_constraint(self, *p, **k):
        self._not_supported('ALTER TABLE DROP CONSTRAINT')


# TODO: technically primary key is a NOT NULL + UNIQUE constraint, should add NOT NULL to index

class SQLiteDialect(ansisql.ANSIDialect):
    columngenerator = SQLiteColumnGenerator
    columndropper = SQLiteColumnDropper
    schemachanger = SQLiteSchemaChanger
    constraintgenerator = SQLiteConstraintGenerator
    constraintdropper = SQLiteConstraintDropper
