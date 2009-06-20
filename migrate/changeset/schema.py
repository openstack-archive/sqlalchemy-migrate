"""
   Schema module providing common schema operations.
"""
import sqlalchemy

from migrate.changeset.databases.visitor import (get_engine_visitor,
                                                 run_single_visitor)
from migrate.changeset.exceptions import *


__all__ = [
    'create_column',
    'drop_column',
    'alter_column',
    'rename_table',
    'rename_index',
    'ChangesetTable',
    'ChangesetColumn',
    'ChangesetIndex',
]


def create_column(column, table=None, *p, **k):
    """Create a column, given the table
    
    API to :meth:`column.create`
    """
    if table is not None:
        return table.create_column(column, *p, **k)
    return column.create(*p, **k)


def drop_column(column, table=None, *p, **k):
    """Drop a column, given the table
    
    API to :meth:`column.drop`
    """
    if table is not None:
        return table.drop_column(column, *p, **k)
    return column.drop(*p, **k)


def rename_table(table, name, engine=None):
    """Rename a table.

    If Table instance is given, engine is not used.

    API to :meth:`table.rename`

    :param table: Table to be renamed
    :param name: new name
    :param engine: Engine instance
    :type table: string or Table instance
    :type name: string
    :type engine: obj
    """
    table = _to_table(table, engine)
    table.rename(name)


def rename_index(index, name, table=None, engine=None):
    """Rename an index.

    If Index and Table object instances are given,
    table and engine are not used.

    API to :meth:`index.rename`

    :param index: Index to be renamed
    :param name: new name
    :param table: Table to which Index is reffered
    :param engine: Engine instance
    :type index: string or Index instance
    :type name: string
    :type table: string or Table instance
    :type engine: obj
    """
    index = _to_index(index, table, engine)
    index.rename(name)


def alter_column(*p, **k):
    """Alter a column.

    Parameters: column name, table name, an engine, and the properties
    of that column to change

    API to :meth:`column.alter`
    """
    if len(p) and isinstance(p[0], sqlalchemy.Column):
        col = p[0]
    else:
        col = None

    if 'table' not in k:
        k['table'] = col.table
    if 'engine' not in k:
        k['engine'] = k['table'].bind

    engine = k['engine']
    delta = _ColumnDelta(*p, **k)

    delta.result_column.delta = delta
    delta.result_column.table = delta.table

    visitorcallable = get_engine_visitor(engine, 'schemachanger')
    engine._run_visitor(visitorcallable, delta.result_column)

    # Update column
    if col is not None:
        # Special case: change column key on rename, if key not
        # explicit
        #
        # Used by SA : table.c.[key]
        #
        # This fails if the key was explit AND equal to the column
        # name.  (It changes the key name when it shouldn't.)
        #
        # Not much we can do about it.
        if 'name' in delta.keys():
            if (col.name == col.key):
                newname = delta['name']
                del col.table.c[col.key]
                setattr(col, 'key', newname)
                col.table.c[col.key] = col
        # Change all other attrs
        for key, val in delta.iteritems():
            setattr(col, key, val)


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


class _ColumnDelta(dict):
    """Extracts the differences between two columns/column-parameters"""

    def __init__(self, *p, **k):
        """Extract ALTER-able differences from two columns.

        May receive parameters arranged in several different ways:
         * old_column_object,new_column_object,*parameters Identifies
            attributes that differ between the two columns.
            Parameters specified outside of either column are always
            executed and override column differences.
         * column_object,[current_name,]*parameters Parameters
            specified are changed; table name is extracted from column
            object.  Name is changed to column_object.name from
            current_name, if current_name is specified. If not
            specified, name is unchanged.
         * current_name,table,*parameters 'table' may be either an
            object or a name
        """
        # Things are initialized differently depending on how many column
        # parameters are given. Figure out how many and call the appropriate
        # method.

        if len(p) >= 1 and isinstance(p[0], sqlalchemy.Column):
            # At least one column specified
            if len(p) >= 2 and isinstance(p[1], sqlalchemy.Column):
                # Two columns specified
                func = self._init_2col
            else:
                # Exactly one column specified
                func = self._init_1col
        else:
            # Zero columns specified
            func = self._init_0col
        diffs = func(*p, **k)
        self._set_diffs(diffs)

    # Column attributes that can be altered
    diff_keys = ('name',
                 'type',
                 'nullable',
                 'default',
                 'server_default',
                 'primary_key',
                 'foreign_key')

    @property
    def table(self):
        if isinstance(self._table, sqlalchemy.Table):
            return self._table

    def _init_0col(self, current_name, *p, **k):
        p, k = self._init_normalize_params(p, k)
        table = k.pop('table')
        self.current_name = current_name
        self._table = table
        self.result_column = table.c.get(current_name, None)
        return k

    def _init_1col(self, col, *p, **k):
        p, k = self._init_normalize_params(p, k)
        self._table = k.pop('table', None) or col.table
        self.result_column = col.copy()
        if 'current_name' in k:
            # Renamed
            self.current_name = k.pop('current_name')
            k.setdefault('name', col.name)
        else:
            self.current_name = col.name
        return k

    def _init_2col(self, start_col, end_col, *p, **k):
        p, k = self._init_normalize_params(p, k)
        self.result_column = start_col.copy()
        self._table = k.pop('table', None) or start_col.table \
            or end_col.table
        self.current_name = start_col.name
        for key in ('name', 'nullable', 'default', 'server_default',
                    'primary_key', 'foreign_key'):
            val = getattr(end_col, key, None)
            if getattr(start_col, key, None) != val:
                k.setdefault(key, val)
        if not self.column_types_eq(start_col.type, end_col.type):
            k.setdefault('type', end_col.type)
        return k

    def _init_normalize_params(self, p, k):
        p = list(p)
        if len(p):
            k.setdefault('name', p.pop(0))
        if len(p):
            k.setdefault('type', p.pop(0))
        # TODO: sequences? FKs?
        return p, k

    def _set_diffs(self, diffs):
        for key in self.diff_keys:
            if key in diffs:
                self[key] = diffs[key]
                if getattr(self, 'result_column', None) is not None:
                    setattr(self.result_column, key, diffs[key])

    def column_types_eq(self, this, that):
        ret = isinstance(this, that.__class__)
        ret = ret or isinstance(that, this.__class__)
        # String length is a special case
        if ret and isinstance(that, sqlalchemy.types.String):
            ret = (getattr(this, 'length', None) == \
                       getattr(that, 'length', None))
        return ret


class ChangesetTable(object):
    """Changeset extensions to SQLAlchemy tables."""

    def create_column(self, column):
        """Creates a column.

        The column parameter may be a column definition or the name of
        a column in this table.
        """
        if not isinstance(column, sqlalchemy.Column):
            # It's a column name
            column = getattr(self.c, str(column))
        column.create(table=self)

    def drop_column(self, column):
        """Drop a column, given its name or definition."""
        if not isinstance(column, sqlalchemy.Column):
            # It's a column name
            try:
                column = getattr(self.c, str(column))
            except AttributeError:
                # That column isn't part of the table. We don't need
                # its entire definition to drop the column, just its
                # name, so create a dummy column with the same name.
                column = sqlalchemy.Column(str(column))
        column.drop(table=self)

    def rename(self, name, *args, **kwargs):
        """Rename this table.

        This changes both the database name and the name of this
        Python object
        """
        engine = self.bind
        self.new_name = name
        visitorcallable = get_engine_visitor(engine, 'schemachanger')
        run_single_visitor(engine, visitorcallable, self, *args, **kwargs)

        # Fix metadata registration
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
    """Changeset extensions to SQLAlchemy columns"""

    def alter(self, *p, **k):
        """Alter a column's definition: ``ALTER TABLE ALTER COLUMN``.

        May supply a new column object, or a list of properties to
        change.

        For example; the following are equivalent:
            col.alter(Column('myint', Integer, nullable=False))
            col.alter('myint', Integer, nullable=False)
            col.alter(name='myint', type=Integer, nullable=False)

        Column name, type, default, and nullable may be changed
        here. Note that for column defaults, only PassiveDefaults are
        managed by the database - changing others doesn't make sense.

        :param table: Table to be altered
        :param engine: Engine to be used
        """
        if 'table' not in k:
            k['table'] = self.table
        if 'engine' not in k:
            k['engine'] = k['table'].bind
        return alter_column(self, *p, **k)

    def create(self, table=None, index_name=None, unique_name=None,
               primary_key_name=None, *args, **kwargs):
        """Create this column in the database.

        Assumes the given table exists. ``ALTER TABLE ADD COLUMN``,
        for most databases.
        """
        self.index_name = index_name
        self.unique_name = unique_name
        self.primary_key_name = primary_key_name
        for cons in ('index_name', 'unique_name', 'primary_key_name'):
            self._check_sanity_constraints(cons)
        
        self.add_to_table(table)
        engine = self.table.bind
        visitorcallable = get_engine_visitor(engine, 'columngenerator')
        engine._run_visitor(visitorcallable, self, *args, **kwargs)
        return self

    def drop(self, table=None, *args, **kwargs):
        """Drop this column from the database, leaving its table intact.

        ``ALTER TABLE DROP COLUMN``, for most databases.
        """
        if table is not None:
            self.table = table
        self.remove_from_table(self.table)
        engine = self.table.bind
        visitorcallable = get_engine_visitor(engine, 'columndropper')
        engine._run_visitor(visitorcallable, self, *args, **kwargs)
        return self

    def add_to_table(self, table):
        if table and not self.table:
            self._set_parent(table)

    def remove_from_table(self, table):
        # TODO: remove indexes, primary keys, constraints, etc
        if table.c.contains_column(self):
            table.c.remove(self)
            
    def _check_sanity_constraints(self, name):
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

    def rename(self, name, *args, **kwargs):
        """Change the name of an index.

        This changes both the Python object name and the database
        name.
        """
        engine = self.table.bind
        self.new_name = name
        visitorcallable = get_engine_visitor(engine, 'schemachanger')
        engine._run_visitor(visitorcallable, self, *args, **kwargs)
        self.name = name
