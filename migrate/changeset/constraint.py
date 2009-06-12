"""
   This module defines standalone schema constraint classes.
"""
import sqlalchemy
from sqlalchemy import schema


class ConstraintChangeset(object):
    """Base class for Constraint classes."""

    def _normalize_columns(self, cols, table_name=False):
        """Given: column objects or names; return col names and
        (maybe) a table"""
        colnames = []
        table = None
        for col in cols:
            if isinstance(col, schema.Column):
                if col.table is not None and table is None:
                    table = col.table
                if table_name:
                    col = '.'.join((col.table.name, col.name))
                else:
                    col = col.name
            colnames.append(col)
        return colnames, table

    def create(self, *args, **kwargs):
        """Create the constraint in the database.

        :param engine: the database engine to use. If this is \
        :keyword:`None` the instance's engine will be used
        :type engine: :class:`sqlalchemy.engine.base.Engine`
        """
        from migrate.changeset.databases.visitor import get_engine_visitor
        visitorcallable = get_engine_visitor(self.table.bind,
                                             'constraintgenerator')
        _engine_run_visitor(self.table.bind, visitorcallable, self)

    def drop(self, *args, **kwargs):
        """Drop the constraint from the database.

        :param engine: the database engine to use. If this is
          :keyword:`None` the instance's engine will be used
        :type engine: :class:`sqlalchemy.engine.base.Engine`
        """
        from migrate.changeset.databases.visitor import get_engine_visitor
        visitorcallable = get_engine_visitor(self.table.bind,
                                             'constraintdropper')
        _engine_run_visitor(self.table.bind, visitorcallable, self)
        self.columns.clear()
        return self

    def accept_schema_visitor(self, visitor, *p, **k):
        """Call the visitor only if it defines the given function"""
        return getattr(visitor, self._func)(self)

    def autoname(self):
        """Automatically generate a name for the constraint instance.

        Subclasses must implement this method.
        """


def _engine_run_visitor(engine, visitorcallable, element, **kwargs):
    conn = engine.connect()
    try:
        element.accept_schema_visitor(visitorcallable(conn))
    finally:
        conn.close()


class PrimaryKeyConstraint(ConstraintChangeset, schema.PrimaryKeyConstraint):
    """Primary key constraint class."""

    _func = 'visit_migrate_primary_key_constraint'

    def __init__(self, *cols, **kwargs):
        colnames, table = self._normalize_columns(cols)
        table = kwargs.pop('table', table)
        super(PrimaryKeyConstraint, self).__init__(*colnames, **kwargs)
        if table is not None:
            self._set_parent(table)

    def autoname(self):
        """Mimic the database's automatic constraint names"""
        return "%s_pkey" % self.table.name


class ForeignKeyConstraint(ConstraintChangeset, schema.ForeignKeyConstraint):
    """Foreign key constraint class."""

    _func = 'visit_migrate_foreign_key_constraint'

    def __init__(self, columns, refcolumns, *p, **k):
        colnames, table = self._normalize_columns(columns)
        table = k.pop('table', table)
        refcolnames, reftable = self._normalize_columns(refcolumns,
                                                        table_name=True)
        super(ForeignKeyConstraint, self).__init__(colnames, refcolnames, *p,
                                                   **k)
        if table is not None:
            self._set_parent(table)

    @property
    def referenced(self):
        return [e.column for e in self.elements]

    @property
    def reftable(self):
        return self.referenced[0].table

    def autoname(self):
        """Mimic the database's automatic constraint names"""
        ret = "%(table)s_%(reftable)s_fkey" % dict(
            table=self.table.name,
            reftable=self.reftable.name,)
        return ret


class CheckConstraint(ConstraintChangeset, schema.CheckConstraint):
    """Check constraint class."""

    _func = 'visit_migrate_check_constraint'

    def __init__(self, sqltext, *args, **kwargs):
        cols = kwargs.pop('columns')
        colnames, table = self._normalize_columns(cols)
        table = kwargs.pop('table', table)
        ConstraintChangeset.__init__(self, *args, **kwargs)
        schema.CheckConstraint.__init__(self, sqltext, *args, **kwargs)
        if table is not None:
            self._set_parent(table)
        self.colnames = colnames

    def autoname(self):
        return "%(table)s_%(cols)s_check" % \
            dict(table=self.table.name, cols="_".join(self.colnames))
