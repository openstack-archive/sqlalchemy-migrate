"""
   Extensions to SQLAlchemy for altering existing tables.

   At the moment, this isn't so much based off of ANSI as much as
   things that just happen to work with multiple databases.
"""
import sqlalchemy as sa
from sqlalchemy.engine.base import Connection, Dialect
from sqlalchemy.sql.compiler import SchemaGenerator
from sqlalchemy.schema import ForeignKeyConstraint
from migrate.changeset import constraint, exceptions

SchemaIterator = sa.engine.SchemaIterator


class RawAlterTableVisitor(object):
    """Common operations for ``ALTER TABLE`` statements."""

    def _to_table(self, param):
        """Returns the table object for the given param object."""
        if isinstance(param, (sa.Column, sa.Index, sa.schema.Constraint)):
            ret = param.table
        else:
            ret = param
        return ret

    def _to_table_name(self, param):
        """Returns the table name for the given param object."""
        ret = self._to_table(param)
        if isinstance(ret, sa.Table):
            ret = ret.fullname
        return ret

    def _do_quote_table_identifier(self, identifier):
        """Returns a quoted version of the given table identifier."""
        return '"%s"'%identifier

    def start_alter_table(self, param):
        """Returns the start of an ``ALTER TABLE`` SQL-Statement.

        Use the param object to determine the table name and use it
        for building the SQL statement.

        :param param: object to determine the table from
        :type param: :class:`sqlalchemy.Column`, :class:`sqlalchemy.Index`,
          :class:`sqlalchemy.schema.Constraint`, :class:`sqlalchemy.Table`,
          or string (table name)
        """
        table = self._to_table(param)
        table_name = self._to_table_name(table)
        self.append('\nALTER TABLE %s ' % \
                        self._do_quote_table_identifier(table_name))
        return table

    def _pk_constraint(self, table, column, status):
        """Create a primary key constraint from a table, column.

        Status: true if the constraint is being added; false if being dropped
        """
        if isinstance(column, basestring):
            column = getattr(table.c, name)

        ret = constraint.PrimaryKeyConstraint(*table.primary_key)
        if status:
            # Created PK
            ret.c.append(column)
        else:
            # Dropped PK
            names = [c.name for c in cons.c]
            index = names.index(col.name)
            del ret.c[index]

        # Allow explicit PK name assignment
        if isinstance(pk, basestring):
            ret.name = pk
        return ret


class AlterTableVisitor(SchemaIterator, RawAlterTableVisitor):
    """Common operations for ``ALTER TABLE`` statements"""
    pass


class ANSIColumnGenerator(AlterTableVisitor, SchemaGenerator):
    """Extends ansisql generator for column creation (alter table add col)"""

    def visit_column(self, column):
        """Create a column (table already exists).

        :param column: column object
        :type column: :class:`sqlalchemy.Column`
        """
        table = self.start_alter_table(column)
        self.append(" ADD ")
        colspec = self.get_column_specification(column)
        self.append(colspec)
        self.execute()

    def visit_table(self, table):
        """Default table visitor, does nothing.

        :param table: table object
        :type table: :class:`sqlalchemy.Table`
        """
        pass


class ANSIColumnDropper(AlterTableVisitor):
    """Extends ANSI SQL dropper for column dropping (``ALTER TABLE
    DROP COLUMN``)."""

    def visit_column(self, column):
        """Drop a column from its table.

        :param column: the column object
        :type column: :class:`sqlalchemy.Column`
        """
        table = self.start_alter_table(column)
        self.append(' DROP COLUMN %s' % \
                        self._do_quote_column_identifier(column.name))
        self.execute()


class ANSISchemaChanger(AlterTableVisitor, SchemaGenerator):
    """Manages changes to existing schema elements.

    Note that columns are schema elements; ``ALTER TABLE ADD COLUMN``
    is in SchemaGenerator.

    All items may be renamed. Columns can also have many of their properties -
    type, for example - changed.

    Each function is passed a tuple, containing (object,name); where
    object is a type of object you'd expect for that function
    (ie. table for visit_table) and name is the object's new
    name. NONE means the name is unchanged.
    """

    def _do_quote_column_identifier(self, identifier):
        """override this function to define how identifiers (table and
        column names) should be written in the SQL.  For instance, in
        PostgreSQL, double quotes should surround the identifier
        """
        return identifier

    def visit_table(self, param):
        """Rename a table. Other ops aren't supported."""
        table, newname = param
        self.start_alter_table(table)
        self.append("RENAME TO %s"%newname)
        self.execute()

    def visit_column(self, delta):
        """Rename/change a column."""
        # ALTER COLUMN is implemented as several ALTER statements
        keys = delta.keys()
        if 'type' in keys:
            self._run_subvisit(delta, self._visit_column_type)
        if 'nullable' in keys:
            self._run_subvisit(delta, self._visit_column_nullable)
        if 'server_default' in keys:
            # Skip 'default': only handle server-side defaults, others
            # are managed by the app, not the db.
            self._run_subvisit(delta, self._visit_column_default)
        if 'name' in keys:
            self._run_subvisit(delta, self._visit_column_name)

    def _run_subvisit(self, delta, func, col_name=None, table_name=None):
        if table_name is None:
            table_name = self._to_table(delta.table)
        if col_name is None:
            col_name = delta.current_name
        ret = func(table_name, col_name, delta)
        self.execute()
        return ret

    def _visit_column_foreign_key(self, delta):
        table = delta.table
        column = getattr(table.c, delta.current_name)
        cons = constraint.ForeignKeyConstraint(column, autoload=True)
        fk = delta['foreign_key']
        if fk:
            # For now, cons.columns is limited to one column:
            # no multicolumn FKs
            column.foreign_key = ForeignKey(*cons.columns)
        else:
            column_foreign_key = None
        cons.drop()
        cons.create()

    def _visit_column_primary_key(self, delta):
        table = delta.table
        col = getattr(table.c, delta.current_name)
        pk = delta['primary_key']
        cons = self._pk_constraint(table, col, pk)
        cons.drop()
        cons.create()

    def _visit_column_nullable(self, table_name, col_name, delta):
        nullable = delta['nullable']
        table = self._to_table(delta)
        self.start_alter_table(table_name)
        self.append("ALTER COLUMN %s " % \
                        self._do_quote_column_identifier(col_name))
        if nullable:
            self.append("DROP NOT NULL")
        else:
            self.append("SET NOT NULL")

    def _visit_column_default(self, table_name, col_name, delta):
        server_default = delta['server_default']
        # Dummy column: get_col_default_string needs a column for some
        # reason
        dummy = sa.Column(None, None, server_default=server_default)
        default_text = self.get_column_default_string(dummy)
        self.start_alter_table(table_name)
        self.append("ALTER COLUMN %s " % \
                        self._do_quote_column_identifier(col_name))
        if default_text is not None:
            self.append("SET DEFAULT %s"%default_text)
        else:
            self.append("DROP DEFAULT")

    def _visit_column_type(self, table_name, col_name, delta):
        type = delta['type']
        if not isinstance(type, sa.types.AbstractType):
            # It's the class itself, not an instance... make an
            # instance
            type = type()
        type_text = type.dialect_impl(self.dialect).get_col_spec()
        self.start_alter_table(table_name)
        self.append("ALTER COLUMN %s TYPE %s" % \
                        (self._do_quote_column_identifier(col_name),
                         type_text))

    def _visit_column_name(self, table_name, col_name, delta):
        new_name = delta['name']
        self.start_alter_table(table_name)
        self.append('RENAME COLUMN %s TO %s' % \
                        (self._do_quote_column_identifier(col_name),
                         self._do_quote_column_identifier(new_name)))

    def visit_index(self, param):
        """Rename an index; #36"""
        index, newname = param
        self.append("ALTER INDEX %s RENAME TO %s" % (index.name, newname))
        self.execute()


class ANSIConstraintCommon(AlterTableVisitor):
    """
    Migrate's constraints require a separate creation function from
    SA's: Migrate's constraints are created independently of a table;
    SA's are created at the same time as the table.
    """

    def get_constraint_name(self, cons):
        """Gets a name for the given constraint.

        If the name is already set it will be used otherwise the
        constraint's :meth:`autoname
        <migrate.changeset.constraint.ConstraintChangeset.autoname>`
        method is used.

        :param cons: constraint object
        :type cons: :class:`migrate.changeset.constraint.ConstraintChangeset`
        """
        if cons.name is not None:
            ret = cons.name
        else:
            ret = cons.name = cons.autoname()
        return ret


class ANSIConstraintGenerator(ANSIConstraintCommon):

    def get_constraint_specification(self, cons, **kwargs):
        if isinstance(cons, constraint.PrimaryKeyConstraint):
            col_names = ','.join([i.name for i in cons.columns])
            ret = "PRIMARY KEY (%s)" % col_names
            if cons.name:
                # Named constraint
                ret = ("CONSTRAINT %s " % cons.name)+ret
        elif isinstance(cons, constraint.ForeignKeyConstraint):
            params = dict(
                columns=','.join([c.name for c in cons.columns]),
                reftable=cons.reftable,
                referenced=','.join([c.name for c in cons.referenced]),
                name=self.get_constraint_name(cons),
            )
            ret = "CONSTRAINT %(name)s FOREIGN KEY (%(columns)s) "\
                "REFERENCES %(reftable)s (%(referenced)s)" % params
            if cons.onupdate:
                ret = ret + " ON UPDATE %s" % cons.onupdate
            if cons.ondelete:
                ret = ret + " ON DELETE %s" % cons.ondelete
        elif isinstance(cons, constraint.CheckConstraint):
            ret = "CHECK (%s)" % cons.sqltext
        else:
            raise exceptions.InvalidConstraintError(cons)
        return ret

    def _visit_constraint(self, constraint):
        table = self.start_alter_table(constraint)
        self.append("ADD ")
        spec = self.get_constraint_specification(constraint)
        self.append(spec)
        self.execute()

    def visit_migrate_primary_key_constraint(self, *p, **k):
        return self._visit_constraint(*p, **k)

    def visit_migrate_foreign_key_constraint(self, *p, **k):
        return self._visit_constraint(*p, **k)

    def visit_migrate_check_constraint(self, *p, **k):
        return self._visit_constraint(*p, **k)


class ANSIConstraintDropper(ANSIConstraintCommon):

    def _visit_constraint(self, constraint):
        self.start_alter_table(constraint)
        self.append("DROP CONSTRAINT ")
        self.append(self.get_constraint_name(constraint))
        self.execute()

    def visit_migrate_primary_key_constraint(self, *p, **k):
        return self._visit_constraint(*p, **k)

    def visit_migrate_foreign_key_constraint(self, *p, **k):
        return self._visit_constraint(*p, **k)

    def visit_migrate_check_constraint(self, *p, **k):
        return self._visit_constraint(*p, **k)


class ANSIFKGenerator(AlterTableVisitor, SchemaGenerator):
    """Extends ansisql generator for column creation (alter table add col)"""

    def __init__(self, *args, **kwargs):
        self.fk = kwargs.get('fk', None)
        if self.fk:
            del kwargs['fk']
        super(ANSIFKGenerator, self).__init__(*args, **kwargs)

    def visit_column(self, column):
        """Create foreign keys for a column (table already exists); #32"""

        if self.fk:
            self.add_foreignkey(self.fk.constraint)

        if self.buffer.getvalue() !='':
            self.execute()

    def visit_table(self, table):
        pass


class ANSIDialect(object):
    columngenerator = ANSIColumnGenerator
    columndropper = ANSIColumnDropper
    schemachanger = ANSISchemaChanger
    columnfkgenerator = ANSIFKGenerator

    @classmethod
    def visitor(self, name):
        return getattr(self, name)

    def reflectconstraints(self, connection, table_name):
        raise NotImplementedError()
