"""
   Schema module providing common schema operations.
"""
import re
import sqlalchemy
from migrate.changeset.databases.visitor import get_engine_visitor

__all__ = [
'create_column',
'drop_column',
'alter_column',
'rename_table',
'rename_index',
]


def create_column(column, table=None, *p, **k):
    if table is not None:
        return table.create_column(column, *p, **k)
    return column.create(*p, **k)


def drop_column(column, table=None, *p, **k):
    if table is not None:
        return table.drop_column(column, *p, **k)
    return column.drop(*p, **k)


def _to_table(table, engine=None):
    if isinstance(table, sqlalchemy.Table):
        return table
    # Given: table name, maybe an engine
    meta = sqlalchemy.MetaData()
    if engine is not None:
        meta.bind = engine
    return sqlalchemy.Table(table, meta)


def _to_index(index, table=None, engine=None):
    if isinstance(index, sqlalchemy.Index):
        return index
    # Given: index name; table name required
    table = _to_table(table, engine)
    ret = sqlalchemy.Index(index)
    ret.table = table
    return ret


def rename_table(table, name, engine=None):
    """Rename a table, given the table's current name and the new
    name."""
    table = _to_table(table, engine)
    table.rename(name)


def rename_index(index, name, table=None, engine=None):
    """Rename an index.

    Takes an index name/object, a table name/object, and an
    engine. Engine and table aren't required if an index object is
    given.
    """
    index = _to_index(index, table, engine)
    index.rename(name)


def _engine_run_visitor(engine, visitorcallable, element, **kwargs):
    conn = engine.connect()
    try:
        element.accept_schema_visitor(visitorcallable(engine.dialect,
                                                      connection=conn))
    finally:
        conn.close()


def alter_column(*p, **k):
    """Alter a column.

    Parameters: column name, table name, an engine, and the properties
    of that column to change
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
    visitorcallable = get_engine_visitor(engine, 'schemachanger')
    _engine_run_visitor(engine, visitorcallable, delta)

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


def _normalize_table(column, table):
    if table is not None:
        if table is not column.table:
            # This is a bit of a hack: we end up with dupe PK columns here
            pk_names = map(lambda c: c.name, table.primary_key)
            if column.primary_key and pk_names.count(column.name):
                index = pk_names.index(column_name)
                del table.primary_key[index]
            table.append_column(column)
    return column.table


class _WrapRename(object):

    def __init__(self, item, name):
        self.item = item
        self.name = name

    def accept_schema_visitor(self, visitor):
        if isinstance(self.item, sqlalchemy.Table):
            suffix = 'table'
        elif isinstance(self.item, sqlalchemy.Column):
            suffix = 'column'
        elif isinstance(self.item, sqlalchemy.Index):
            suffix = 'index'
        funcname = 'visit_%s' % suffix
        func = getattr(visitor, funcname)
        param = self.item, self.name
        return func(param)


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
    diff_keys = ('name', 'type', 'nullable', 'default', 'server_default',
                 'primary_key', 'foreign_key')

    def _get_table_name(self):
        if isinstance(self._table, basestring):
            ret = self._table
        else:
            ret = self._table.name
        return ret
    table_name = property(_get_table_name)

    def _get_table(self):
        if isinstance(self._table, basestring):
            ret = None
        else:
            ret = self._table
        return ret
    table = property(_get_table)

    def _init_0col(self, current_name, *p, **k):
        p, k = self._init_normalize_params(p, k)
        table = k.pop('table')
        self.current_name = current_name
        self._table = table
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

    def accept_schema_visitor(self, visitor):
        return visitor.visit_column(self)


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
                column = getattr(self.c, str(column), None)
            except AttributeError:
                # That column isn't part of the table. We don't need
                # its entire definition to drop the column, just its
                # name, so create a dummy column with the same name.
                column = sqlalchemy.Column(str(column))
        column.drop(table=self)

    def _meta_key(self):
        return sqlalchemy.schema._get_table_key(self.name, self.schema)

    def deregister(self):
        """Remove this table from its metadata"""
        key = self._meta_key()
        meta = self.metadata
        if key in meta.tables:
            del meta.tables[key]

    def rename(self, name, *args, **kwargs):
        """Rename this table.

        This changes both the database name and the name of this
        Python object
        """
        engine = self.bind
        visitorcallable = get_engine_visitor(engine, 'schemachanger')
        param = _WrapRename(self, name)
        _engine_run_visitor(engine, visitorcallable, param, *args, **kwargs)

        # Fix metadata registration
        meta = self.metadata
        self.deregister()
        self.name = name
        self._set_parent(meta)

    def _get_fullname(self):
        """Fullname should always be up to date"""
        # Copied from Table constructor
        if self.schema is not None:
            ret = "%s.%s"%(self.schema, self.name)
        else:
            ret = self.name
        return ret

    fullname = property(_get_fullname, (lambda self, val: None))


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
        """
        if 'table' not in k:
            k['table'] = self.table
        if 'engine' not in k:
            k['engine'] = k['table'].bind
        return alter_column(self, *p, **k)

    def create(self, table=None, *args, **kwargs):
        """Create this column in the database.

        Assumes the given table exists. ``ALTER TABLE ADD COLUMN``,
        for most databases.
        """
        table = _normalize_table(self, table)
        engine = table.bind
        visitorcallable = get_engine_visitor(engine, 'columngenerator')
        engine._run_visitor(visitorcallable, self, *args, **kwargs)

        #add in foreign keys
        if self.foreign_keys:
            for fk in self.foreign_keys:
                visitorcallable = get_engine_visitor(engine,
                                                     'columnfkgenerator')
                engine._run_visitor(visitorcallable, self, fk=fk)
        return self

    def drop(self, table=None, *args, **kwargs):
        """Drop this column from the database, leaving its table intact.

        ``ALTER TABLE DROP COLUMN``, for most databases.
        """
        table = _normalize_table(self, table)
        engine = table.bind
        visitorcallable = get_engine_visitor(engine, 'columndropper')
        engine._run_visitor(lambda dialect, conn: visitorcallable(conn),
                            self, *args, **kwargs)
        return self


class ChangesetIndex(object):
    """Changeset extensions to SQLAlchemy Indexes."""

    def rename(self, name, *args, **kwargs):
        """Change the name of an index.

        This changes both the Python object name and the database
        name.
        """
        engine = self.table.bind
        visitorcallable = get_engine_visitor(engine, 'schemachanger')
        param = _WrapRename(self, name)
        _engine_run_visitor(engine, visitorcallable, param, *args, **kwargs)
        self.name = name


def _patch():
    """All the 'ugly' operations that patch SQLAlchemy's internals."""
    sqlalchemy.schema.Table.__bases__ += (ChangesetTable, )
    sqlalchemy.schema.Column.__bases__ += (ChangesetColumn, )
    sqlalchemy.schema.Index.__bases__ += (ChangesetIndex, )
_patch()
