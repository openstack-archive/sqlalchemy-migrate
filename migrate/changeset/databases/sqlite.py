"""
   `SQLite`_ database specific implementations of changeset classes.

   .. _`SQLite`: http://www.sqlite.org/
"""
from migrate.changeset import ansisql, constraint, exceptions
from sqlalchemy.databases import sqlite as sa_base
from sqlalchemy import Table, MetaData
#import sqlalchemy as sa

SQLiteSchemaGenerator = sa_base.SQLiteSchemaGenerator


class SQLiteHelper(object):

    def visit_column(self, param):
        try:
            table = self._to_table(param.table)
        except:
            table = self._to_table(param)
            raise
        table_name = self._to_table_name(table)
        self.append('ALTER TABLE %s RENAME TO migration_tmp' % table_name)
        self.execute()

        insertion_string = self._modify_table(table, param)

        table.create()
        self.append(insertion_string % {'table_name': table_name})
        self.execute()
        self.append('DROP TABLE migration_tmp')
        self.execute()


class SQLiteColumnGenerator(SQLiteSchemaGenerator,
                            ansisql.ANSIColumnGenerator):
    pass


class SQLiteColumnDropper(SQLiteHelper, ansisql.ANSIColumnDropper):

    def _modify_table(self, table, column):
        del table.columns[column.name]
        columns = ','.join([c.name for c in table.columns])
        return 'INSERT INTO %(table_name)s SELECT ' + columns + \
            ' from migration_tmp'


class SQLiteSchemaChanger(SQLiteHelper, ansisql.ANSISchemaChanger):

    def _not_supported(self, op):
        raise exceptions.NotSupportedError("SQLite does not support "
            "%s; see http://www.sqlite.org/lang_altertable.html"%op)

    def _modify_table(self, table, delta):
        column = table.columns[delta.current_name]
        for k, v in delta.items():
            setattr(column, k, v)
        return 'INSERT INTO %(table_name)s SELECT * from migration_tmp'

    def visit_index(self, param):
        self._not_supported('ALTER INDEX')

    def _do_quote_column_identifier(self, identifier):
        return '"%s"'%identifier


class SQLiteConstraintGenerator(ansisql.ANSIConstraintGenerator):

    def visit_migrate_primary_key_constraint(self, constraint):
        tmpl = "CREATE UNIQUE INDEX %s ON %s ( %s )"
        cols = ','.join([c.name for c in constraint.columns])
        tname = constraint.table.name
        name = constraint.name
        msg = tmpl % (name, tname, cols)
        self.append(msg)
        self.execute()


class SQLiteFKGenerator(SQLiteSchemaChanger, ansisql.ANSIFKGenerator):
    def visit_column(self, column):
        """Create foreign keys for a column (table already exists); #32"""

        if self.fk:
            self._not_supported("ALTER TABLE ADD FOREIGN KEY")

        if self.buffer.getvalue() !='':
            self.execute()


class SQLiteConstraintDropper(ansisql.ANSIColumnDropper):

    def visit_migrate_primary_key_constraint(self, constraint):
        tmpl = "DROP INDEX %s "
        name = constraint.name
        msg = tmpl % (name)
        self.append(msg)
        self.execute()


class SQLiteDialect(ansisql.ANSIDialect):
    columngenerator = SQLiteColumnGenerator
    columndropper = SQLiteColumnDropper
    schemachanger = SQLiteSchemaChanger
    constraintgenerator = SQLiteConstraintGenerator
    constraintdropper = SQLiteConstraintDropper
    columnfkgenerator = SQLiteFKGenerator
