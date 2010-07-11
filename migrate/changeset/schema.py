"""
   Schema module providing common schema operations.
"""
import warnings
from UserDict import DictMixin

import sqlalchemy

from migrate.changeset import SQLA_06
from migrate.changeset.exceptions import *
from migrate.changeset.databases.visitor import (get_engine_visitor,
                                                 run_single_visitor)


__all__ = [
    'create_column',
    'drop_column',
    'alter_column',
    'rename_table',
    'rename_index',
    'ChangesetTable',
    'ChangesetColumn',
    'ChangesetIndex',
    'ChangesetDefaultClause',
    'ColumnDelta',
]

DEFAULT_ALTER_METADATA = True


def create_column(column, table=None, *p, **kw):
    """Create a column, given the table.
    
    API to :meth:`ChangesetColumn.create`.
    """
    if table is not None:
        return table.create_column(column, *p, **kw)
    return column.create(*p, **kw)


def drop_column(column, table=None, *p, **kw):
    """Drop a column, given the table.
    
    API to :meth:`ChangesetColumn.drop`.
    """
    if table is not None:
        return table.drop_column(column, *p, **kw)
    return column.drop(*p, **kw)


def rename_table(table, name, engine=None, **kw):
    """Rename a table.

    If Table instance is given, engine is not used.

    API to :meth:`ChangesetTable.rename`.

    :param table: Table to be renamed.
    :param name: New name for Table.
    :param engine: Engine instance.
    :type table: string or Table instance
    :type name: string
    :type engine: obj
    """
    table = _to_table(table, engine)
    table.rename(name, **kw)


def rename_index(index, name, table=None, engine=None, **kw):
    """Rename an index.

    If Index instance is given,
    table and engine are not used.

    API to :meth:`ChangesetIndex.rename`.

    :param index: Index to be renamed.
    :param name: New name for index.
    :param table: Table to which Index is reffered.
    :param engine: Engine instance.
    :type index: string or Index instance
    :type name: string
    :type table: string or Table instance
    :type engine: obj
    """
    index = _to_index(index, table, engine)
    index.rename(name, **kw)


def alter_column(*p, **k):
    """Alter a column.

    Direct API to :class:`ColumnDelta`.

    :param table: Table or table name (will issue reflection).
    :param engine: Will be used for reflection.
    :param alter_metadata: Defaults to True. It will alter changes also to objects.
    :returns: :class:`Columndelta` instance
    """
    
    k.setdefault('alter_metadata', DEFAULT_ALTER_METADATA)

    if 'table' not in k and isinstance(p[0], sqlalchemy.Column):
        k['table'] = p[0].table
    if 'engine' not in k:
        k['engine'] = k['table'].bind

    # deprecation
    if len(p) >= 2 and isinstance(p[1], sqlalchemy.Column):
        warnings.warn("Alter column with comparing columns is deprecated."
            " Just pass in parameters instead.", MigrateDeprecationWarning)
    engine = k['engine']
    delta = ColumnDelta(*p, **k)

    visitorcallable = get_engine_visitor(engine, 'schemachanger')
    engine._run_visitor(visitorcallable, delta)

    return delta


def _to_table(table, engine=None):
    """Return if instance of Table, else construct new with metadata"""
    if isinstance(table, sqlalchemy.Table):
        return table

    # Given: table name, maybe an engine
    meta = sqlalchemy.MetaData()
    if engine is not None:
        meta.bind = engine
    return sqlalchemy.Table(table, meta)


def _to_index(index, table=None, engine=None):
    """Return if instance of Index, else construct new with metadata"""
    if isinstance(index, sqlalchemy.Index):
        return index

    # Given: index name; table name required
    table = _to_table(table, engine)
    ret = sqlalchemy.Index(index)
    ret.table = table
    return ret


class ColumnDelta(DictMixin, sqlalchemy.schema.SchemaItem):
    """Extracts the differences between two columns/column-parameters

        May receive parameters arranged in several different ways:

        * **current_column, new_column, \*p, \*\*kw**
            Additional parameters can be specified to override column
            differences.

        * **current_column, \*p, \*\*kw**
            Additional parameters alter current_column. Table name is extracted
            from current_column object.
            Name is changed to current_column.name from current_name,
            if current_name is specified.

        * **current_col_name, \*p, \*\*kw**
            Table kw must specified.

        :param table: Table at which current Column should be bound to.\
        If table name is given, reflection will be used.
        :type table: string or Table instance
        :param alter_metadata: If True, it will apply changes to metadata.
        :type alter_metadata: bool
        :param metadata: If `alter_metadata` is true, \
        metadata is used to reflect table names into
        :type metadata: :class:`MetaData` instance
        :param engine: When reflecting tables, either engine or metadata must \
        be specified to acquire engine object.
        :type engine: :class:`Engine` instance
        :returns: :class:`ColumnDelta` instance provides interface for altered attributes to \
        `result_column` through :func:`dict` alike object.

        * :class:`ColumnDelta`.result_column is altered column with new attributes

        * :class:`ColumnDelta`.current_name is current name of column in db


    """

    # Column attributes that can be altered
    diff_keys = ('name', 'type', 'primary_key', 'nullable',
        'server_onupdate', 'server_default', 'autoincrement')
    diffs = dict()
    __visit_name__ = 'column'

    def __init__(self, *p, **kw):
        self.alter_metadata = kw.pop("alter_metadata", False)
        self.meta = kw.pop("metadata", None)
        self.engine = kw.pop("engine", None)

        # Things are initialized differently depending on how many column
        # parameters are given. Figure out how many and call the appropriate
        # method.
        if len(p) >= 1 and isinstance(p[0], sqlalchemy.Column):
            # At least one column specified
            if len(p) >= 2 and isinstance(p[1], sqlalchemy.Column):
                # Two columns specified
                diffs = self.compare_2_columns(*p, **kw)
            else:
                # Exactly one column specified
                diffs = self.compare_1_column(*p, **kw)
        else:
            # Zero columns specified
            if not len(p) or not isinstance(p[0], basestring):
                raise ValueError("First argument must be column name")
            diffs = self.compare_parameters(*p, **kw)

        self.apply_diffs(diffs)

    def __repr__(self):
        return '<ColumnDelta altermetadata=%r, %s>' % (self.alter_metadata,
            super(ColumnDelta, self).__repr__())

    def __getitem__(self, key):
        if key not in self.keys():
            raise KeyError("No such diff key, available: %s" % self.diffs )
        return getattr(self.result_column, key)

    def __setitem__(self, key, value):
        if key not in self.keys():
            raise KeyError("No such diff key, available: %s" % self.diffs )
        setattr(self.result_column, key, value)

    def __delitem__(self, key):
        raise NotImplementedError

    def keys(self):
        return self.diffs.keys()

    def compare_parameters(self, current_name, *p, **k):
        """Compares Column objects with reflection"""
        self.table = k.pop('table')
        self.result_column = self._table.c.get(current_name)
        if len(p):
            k = self._extract_parameters(p, k, self.result_column)
        return k

    def compare_1_column(self, col, *p, **k):
        """Compares one Column object"""
        self.table = k.pop('table', None)
        if self.table is None:
            self.table = col.table
        self.result_column = col
        if len(p):
            k = self._extract_parameters(p, k, self.result_column)
        return k

    def compare_2_columns(self, old_col, new_col, *p, **k):
        """Compares two Column objects"""
        self.process_column(new_col)
        self.table = k.pop('table', None)
        # we cannot use bool() on table in SA06 
        if self.table is None:
            self.table = old_col.table
        if self.table is None:
            new_col.table
        self.result_column = old_col

        # set differences
        # leave out some stuff for later comp
        for key in (set(self.diff_keys) - set(('type',))):
            val = getattr(new_col, key, None)
            if getattr(self.result_column, key, None) != val:
                k.setdefault(key, val)

        # inspect types
        if not self.are_column_types_eq(self.result_column.type, new_col.type):
            k.setdefault('type', new_col.type)

        if len(p):
            k = self._extract_parameters(p, k, self.result_column)
        return k

    def apply_diffs(self, diffs):
        """Populate dict and column object with new values"""
        self.diffs = diffs
        for key in self.diff_keys:
            if key in diffs:
                setattr(self.result_column, key, diffs[key])

        self.process_column(self.result_column)

        # create an instance of class type if not yet
        if 'type' in diffs and callable(self.result_column.type):
            self.result_column.type = self.result_column.type()

        # add column to the table
        if self.table is not None and self.alter_metadata:
            self.result_column.add_to_table(self.table)

    def are_column_types_eq(self, old_type, new_type):
        """Compares two types to be equal"""
        ret = old_type.__class__ == new_type.__class__

        # String length is a special case
        if ret and isinstance(new_type, sqlalchemy.types.String):
            ret = (getattr(old_type, 'length', None) == \
                       getattr(new_type, 'length', None))
        return ret

    def _extract_parameters(self, p, k, column):
        """Extracts data from p and modifies diffs"""
        p = list(p)
        while len(p):
            if isinstance(p[0], basestring):
                k.setdefault('name', p.pop(0))
            elif isinstance(p[0], sqlalchemy.types.AbstractType):
                k.setdefault('type', p.pop(0))
            elif callable(p[0]):
                p[0] = p[0]()
            else:
                break

        if len(p):
            new_col = column.copy_fixed()
            new_col._init_items(*p)
            k = self.compare_2_columns(column, new_col, **k)
        return k

    def process_column(self, column):
        """Processes default values for column"""
        # XXX: this is a snippet from SA processing of positional parameters
        if not SQLA_06 and column.args:
            toinit = list(column.args)
        else:
            toinit = list()

        if column.server_default is not None:
            if isinstance(column.server_default, sqlalchemy.FetchedValue):
                toinit.append(column.server_default)
            else:
                toinit.append(sqlalchemy.DefaultClause(column.server_default))
        if column.server_onupdate is not None:
            if isinstance(column.server_onupdate, FetchedValue):
                toinit.append(column.server_default)
            else:
                toinit.append(sqlalchemy.DefaultClause(column.server_onupdate,
                                            for_update=True))
        if toinit:
            column._init_items(*toinit)
            
        if not SQLA_06:
            column.args = []

    def _get_table(self):
        return getattr(self, '_table', None)

    def _set_table(self, table):
        if isinstance(table, basestring):
            if self.alter_metadata:
                if not self.meta:
                    raise ValueError("metadata must be specified for table"
                        " reflection when using alter_metadata")
                meta = self.meta
                if self.engine:
                    meta.bind = self.engine
            else:
                if not self.engine and not self.meta:
                    raise ValueError("engine or metadata must be specified"
                        " to reflect tables")
                if not self.engine:
                    self.engine = self.meta.bind
                meta = sqlalchemy.MetaData(bind=self.engine)
            self._table = sqlalchemy.Table(table, meta, autoload=True)
        elif isinstance(table, sqlalchemy.Table):
            self._table = table
            if not self.alter_metadata:
                self._table.meta = sqlalchemy.MetaData(bind=self._table.bind)

    def _get_result_column(self):
        return getattr(self, '_result_column', None)

    def _set_result_column(self, column):
        """Set Column to Table based on alter_metadata evaluation."""
        self.process_column(column)
        if not hasattr(self, 'current_name'):
            self.current_name = column.name
        if self.alter_metadata:
            self._result_column = column
        else:
            self._result_column = column.copy_fixed()

    table = property(_get_table, _set_table)
    result_column = property(_get_result_column, _set_result_column)


class ChangesetTable(object):
    """Changeset extensions to SQLAlchemy tables."""

    def create_column(self, column, *p, **kw):
        """Creates a column.

        The column parameter may be a column definition or the name of
        a column in this table.

        API to :meth:`ChangesetColumn.create`

        :param column: Column to be created
        :type column: Column instance or string
        """
        if not isinstance(column, sqlalchemy.Column):
            # It's a column name
            column = getattr(self.c, str(column))
        column.create(table=self, *p, **kw)

    def drop_column(self, column, *p, **kw):
        """Drop a column, given its name or definition.

        API to :meth:`ChangesetColumn.drop`

        :param column: Column to be droped
        :type column: Column instance or string
        """
        if not isinstance(column, sqlalchemy.Column):
            # It's a column name
            try:
                column = getattr(self.c, str(column))
            except AttributeError:
                # That column isn't part of the table. We don't need
                # its entire definition to drop the column, just its
                # name, so create a dummy column with the same name.
                column = sqlalchemy.Column(str(column), sqlalchemy.Integer())
        column.drop(table=self, *p, **kw)

    def rename(self, name, connection=None, **kwargs):
        """Rename this table.

        :param name: New name of the table.
        :type name: string
        :param alter_metadata: If True, table will be removed from metadata
        :type alter_metadata: bool
        :param connection: reuse connection istead of creating new one.
        :type connection: :class:`sqlalchemy.engine.base.Connection` instance
        """
        self.alter_metadata = kwargs.pop('alter_metadata', DEFAULT_ALTER_METADATA)
        engine = self.bind
        self.new_name = name
        visitorcallable = get_engine_visitor(engine, 'schemachanger')
        run_single_visitor(engine, visitorcallable, self, connection, **kwargs)

        # Fix metadata registration
        if self.alter_metadata:
            self.name = name
            self.deregister()
            self._set_parent(self.metadata)

    def _meta_key(self):
        return sqlalchemy.schema._get_table_key(self.name, self.schema)

    def deregister(self):
        """Remove this table from its metadata"""
        key = self._meta_key()
        meta = self.metadata
        if key in meta.tables:
            del meta.tables[key]


class ChangesetColumn(object):
    """Changeset extensions to SQLAlchemy columns."""

    def alter(self, *p, **k):
        """Alter a column's definition: ``ALTER TABLE ALTER COLUMN``.

        Column name, type, server_default, and nullable may be changed
        here.

        Direct API to :func:`alter_column`

        Example::

            col.alter(name='foobar', type=Integer(), server_default=text("a"))

        Supported parameters: name, type, primary_key, nullable,
        server_onupdate, server_default, autoincrement

        """
        if 'table' not in k:
            k['table'] = self.table
        if 'engine' not in k:
            k['engine'] = k['table'].bind
        return alter_column(self, *p, **k)

    def create(self, table=None, index_name=None, unique_name=None,
               primary_key_name=None, populate_default=True, connection=None, **kwargs):
        """Create this column in the database.

        Assumes the given table exists. ``ALTER TABLE ADD COLUMN``,
        for most databases.

        :param table: Table instance to create on.
        :param index_name: Creates :class:`ChangesetIndex` on this column.
        :param unique_name: Creates :class:\
`~migrate.changeset.constraint.UniqueConstraint` on this column.
        :param primary_key_name: Creates :class:\
`~migrate.changeset.constraint.PrimaryKeyConstraint` on this column.
        :param alter_metadata: If True, column will be added to table object.
        :param populate_default: If True, created column will be \
populated with defaults
        :param connection: reuse connection istead of creating new one.
        :type table: Table instance
        :type index_name: string
        :type unique_name: string
        :type primary_key_name: string
        :type alter_metadata: bool
        :type populate_default: bool
        :type connection: :class:`sqlalchemy.engine.base.Connection` instance

        :returns: self
        """
        self.populate_default = populate_default
        self.alter_metadata = kwargs.pop('alter_metadata', DEFAULT_ALTER_METADATA)
        self.index_name = index_name
        self.unique_name = unique_name
        self.primary_key_name = primary_key_name
        for cons in ('index_name', 'unique_name', 'primary_key_name'):
            self._check_sanity_constraints(cons)

        if self.alter_metadata:
            self.add_to_table(table)
        engine = self.table.bind
        visitorcallable = get_engine_visitor(engine, 'columngenerator')
        engine._run_visitor(visitorcallable, self, connection, **kwargs)

        # TODO: reuse existing connection
        if self.populate_default and self.default is not None:
            stmt = table.update().values({self: engine._execute_default(self.default)})
            engine.execute(stmt)

        return self

    def drop(self, table=None, connection=None, **kwargs):
        """Drop this column from the database, leaving its table intact.

        ``ALTER TABLE DROP COLUMN``, for most databases.

        :param alter_metadata: If True, column will be removed from table object.
        :type alter_metadata: bool
        :param connection: reuse connection istead of creating new one.
        :type connection: :class:`sqlalchemy.engine.base.Connection` instance
        """
        self.alter_metadata = kwargs.pop('alter_metadata', DEFAULT_ALTER_METADATA)
        if table is not None:
            self.table = table
        engine = self.table.bind
        if self.alter_metadata:
            self.remove_from_table(self.table, unset_table=False)
        visitorcallable = get_engine_visitor(engine, 'columndropper')
        engine._run_visitor(visitorcallable, self, connection, **kwargs)
        if self.alter_metadata:
            self.table = None
        return self

    def add_to_table(self, table):
        if table is not None  and self.table is None:
            self._set_parent(table)

    def remove_from_table(self, table, unset_table=True):
        # TODO: remove indexes, primary keys, constraints, etc
        if unset_table:
            self.table = None
        if table.c.contains_column(self):
            table.c.remove(self)

    # TODO: this is fixed in 0.6
    def copy_fixed(self, **kw):
        """Create a copy of this ``Column``, with all attributes."""
        return sqlalchemy.Column(self.name, self.type, self.default,
            key=self.key,
            primary_key=self.primary_key,
            nullable=self.nullable,
            quote=self.quote,
            index=self.index,
            unique=self.unique,
            onupdate=self.onupdate,
            autoincrement=self.autoincrement,
            server_default=self.server_default,
            server_onupdate=self.server_onupdate,
            *[c.copy(**kw) for c in self.constraints])

    def _check_sanity_constraints(self, name):
        """Check if constraints names are correct"""
        obj = getattr(self, name)
        if (getattr(self, name[:-5]) and not obj):
            raise InvalidConstraintError("Column.create() accepts index_name,"
            " primary_key_name and unique_name to generate constraints")
        if not isinstance(obj, basestring) and obj is not None:
            raise InvalidConstraintError(
            "%s argument for column must be constraint name" % name)


class ChangesetIndex(object):
    """Changeset extensions to SQLAlchemy Indexes."""

    __visit_name__ = 'index'

    def rename(self, name, connection=None, **kwargs):
        """Change the name of an index.

        :param name: New name of the Index.
        :type name: string
        :param alter_metadata: If True, Index object will be altered.
        :type alter_metadata: bool
        :param connection: reuse connection istead of creating new one.
        :type connection: :class:`sqlalchemy.engine.base.Connection` instance
        """
        self.alter_metadata = kwargs.pop('alter_metadata', DEFAULT_ALTER_METADATA)
        engine = self.table.bind
        self.new_name = name
        visitorcallable = get_engine_visitor(engine, 'schemachanger')
        engine._run_visitor(visitorcallable, self, connection, **kwargs)
        if self.alter_metadata:
            self.name = name


class ChangesetDefaultClause(object):
    """Implements comparison between :class:`DefaultClause` instances"""

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.arg == other.arg:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)
