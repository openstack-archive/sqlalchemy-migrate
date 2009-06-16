"""
   Extensions to SQLAlchemy for altering existing tables.

   At the moment, this isn't so much based off of ANSI as much as
   things that just happen to work with multiple databases.
"""
import sqlalchemy as sa
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.sql.compiler import SchemaGenerator, SchemaDropper
from sqlalchemy.schema import (ForeignKeyConstraint,
                               PrimaryKeyConstraint,
                               CheckConstraint,
                               UniqueConstraint)

from migrate.changeset import exceptions, constraint


SchemaIterator = sa.engine.SchemaIterator


class AlterTableVisitor(SchemaIterator):
    """Common operations for ``ALTER TABLE`` statements."""

    def _to_table(self, param):
        """Returns the table object for the given param object."""
        if isinstance(param, (sa.Column, sa.Index, sa.schema.Constraint)):
            ret = param.table
        else:
            ret = param
        return ret

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
        self.append('\nALTER TABLE %s ' % self.preparer.format_table(table))
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


class ANSIColumnGenerator(AlterTableVisitor, SchemaGenerator):
    """Extends ansisql generator for column creation (alter table add col)"""

    def visit_column(self, column):
        """Create a column (table already exists).

        :param column: column object
        :type column: :class:`sqlalchemy.Column` instance
        """
        table = self.start_alter_table(column)
        self.append("ADD ")
        colspec = self.get_column_specification(column)
        self.append(colspec)
        self.execute()

        # add in foreign keys
        if column.foreign_keys:
            self.visit_alter_foriegn_keys(column)

    def visit_alter_foriegn_keys(self, column):
        for fk in column.foreign_keys:
            self.define_foreign_key(fk.constraint)

    def visit_table(self, table):
        """Default table visitor, does nothing.

        :param table: table object
        :type table: :class:`sqlalchemy.Table` instance
        """
        pass



class ANSIColumnDropper(AlterTableVisitor, SchemaDropper):
    """Extends ANSI SQL dropper for column dropping (``ALTER TABLE
    DROP COLUMN``).
    """

    def visit_column(self, column):
        """Drop a column from its table.

        :param column: the column object
        :type column: :class:`sqlalchemy.Column`
        """
        table = self.start_alter_table(column)
        self.append(' DROP COLUMN %s' % self.preparer.format_column(column))
        self.execute()


class ANSISchemaChanger(AlterTableVisitor, SchemaGenerator):
    """Manages changes to existing schema elements.

    Note that columns are schema elements; ``ALTER TABLE ADD COLUMN``
    is in SchemaGenerator.

    All items may be renamed. Columns can also have many of their properties -
    type, for example - changed.

    Each function is passed a tuple, containing (object, name); where
    object is a type of object you'd expect for that function
    (ie. table for visit_table) and name is the object's new
    name. NONE means the name is unchanged.
    """

    def visit_table(self, table):
        """Rename a table. Other ops aren't supported."""
        self.start_alter_table(table)
        self.append("RENAME TO %s" % self.preparer.quote(table.new_name, table.quote))
        self.execute()

    def visit_index(self, index):
        """Rename an index"""
        self.append("ALTER INDEX %s RENAME TO %s" %
            (self.preparer.quote(self._validate_identifier(index.name, True), index.quote),
             self.preparer.quote(self._validate_identifier(index.new_name, True) , index.quote)))
        self.execute()

    def visit_column(self, column):
        """Rename/change a column."""
        # ALTER COLUMN is implemented as several ALTER statements
        delta = column.delta
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

    def _run_subvisit(self, delta, func):
        """Runs visit method based on what needs to be changed on column"""
        table = self._to_table(delta.table)
        col_name = delta.current_name
        ret = func(table, col_name, delta)
        self.execute()

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

    def _visit_column_nullable(self, table, col_name, delta):
        nullable = delta['nullable']
        table = self._to_table(table)
        self.start_alter_table(table)
        # TODO: use preparer.format_column
        self.append("ALTER COLUMN %s " % self.preparer.quote_identifier(col_name))
        if nullable:
            self.append("DROP NOT NULL")
        else:
            self.append("SET NOT NULL")

    def _visit_column_default(self, table, col_name, delta):
        server_default = delta['server_default']
        # Dummy column: get_col_default_string needs a column for some
        # reason
        dummy = sa.Column(None, None, server_default=server_default)
        default_text = self.get_column_default_string(dummy)
        self.start_alter_table(table)
        # TODO: use preparer.format_column
        self.append("ALTER COLUMN %s " % self.preparer.quote_identifier(col_name))
        if default_text is not None:
            self.append("SET DEFAULT %s" % default_text)
        else:
            self.append("DROP DEFAULT")

    def _visit_column_type(self, table, col_name, delta):
        type_ = delta['type']
        if not isinstance(type_, sa.types.AbstractType):
            # It's the class itself, not an instance... make an
            # instance
            type_ = type_()
        type_text = type_.dialect_impl(self.dialect).get_col_spec()
        self.start_alter_table(table)
        # TODO: does type need formating?
        # TODO: use preparer.format_column
        self.append("ALTER COLUMN %s TYPE %s" %
            (self.preparer.quote_identifier(col_name), type_text))

    def _visit_column_name(self, table, col_name, delta):
        new_name = delta['name']
        self.start_alter_table(table)
        # TODO: use preparer.format_column
        self.append('RENAME COLUMN %s TO %s' % \
                        (self.preparer.quote_identifier(col_name),
                         self.preparer.quote_identifier(new_name)))


class ANSIConstraintCommon(AlterTableVisitor):
    """
    Migrate's constraints require a separate creation function from
    SA's: Migrate's constraints are created independently of a table;
    SA's are created at the same time as the table.
    """

    def get_constraint_name(self, cons):
        """Gets a name for the given constraint.

        If the name is already set it will be used otherwise the
        constraint's :meth:`autoname <migrate.changeset.constraint.ConstraintChangeset.autoname>`
        method is used.

        :param cons: constraint object
        """
        if cons.name is not None:
            ret = cons.name
        else:
            ret = cons.name = cons.autoname()
        return self.preparer.quote(ret, cons.quote)

    def visit_migrate_primary_key_constraint(self, *p, **k):
        self._visit_constraint(*p, **k)

    def visit_migrate_foreign_key_constraint(self, *p, **k):
        self._visit_constraint(*p, **k)

    def visit_migrate_check_constraint(self, *p, **k):
        self._visit_constraint(*p, **k)

    def visit_migrate_unique_constraint(self, *p, **k):
        self._visit_constraint(*p, **k)


class ANSIConstraintGenerator(ANSIConstraintCommon, SchemaGenerator):

    def get_constraint_specification(self, cons, **kwargs):
        """Constaint SQL generators.
        
        We cannot use SA visitors because they append comma.
        """
        if isinstance(cons, PrimaryKeyConstraint):
            if cons.name is not None:
                self.append("CONSTRAINT %s " % self.preparer.format_constraint(cons))
            self.append("PRIMARY KEY ")
            self.append("(%s)" % ', '.join(self.preparer.quote(c.name, c.quote)
                                           for c in cons))
            self.define_constraint_deferrability(cons)
        elif isinstance(cons, ForeignKeyConstraint):
            self.define_foreign_key(cons)
        elif isinstance(cons, CheckConstraint):
            if cons.name is not None:
                self.append("CONSTRAINT %s " %
                            self.preparer.format_constraint(cons))
            self.append(" CHECK (%s)" % cons.sqltext)
            self.define_constraint_deferrability(cons)
        elif isinstance(cons, UniqueConstraint):
            if cons.name is not None:
                self.append("CONSTRAINT %s " %
                            self.preparer.format_constraint(cons))
            self.append(" UNIQUE (%s)" % \
                (', '.join(self.preparer.quote(c.name, c.quote) for c in cons)))
            self.define_constraint_deferrability(cons)
        else:
            raise exceptions.InvalidConstraintError(cons)

    def _visit_constraint(self, constraint):
        table = self.start_alter_table(constraint)
        constraint.name = self.get_constraint_name(constraint)
        self.append("ADD ")
        self.get_constraint_specification(constraint)
        self.execute()


class ANSIConstraintDropper(ANSIConstraintCommon, SchemaDropper):

    def _visit_constraint(self, constraint):
        self.start_alter_table(constraint)
        self.append("DROP CONSTRAINT ")
        self.append(self.get_constraint_name(constraint))
        if constraint.cascade:
            self.append(" CASCADE")
        self.execute()


class ANSIDialect(DefaultDialect):
    columngenerator = ANSIColumnGenerator
    columndropper = ANSIColumnDropper
    schemachanger = ANSISchemaChanger
    constraintgenerator = ANSIConstraintGenerator
    constraintdropper = ANSIConstraintDropper
