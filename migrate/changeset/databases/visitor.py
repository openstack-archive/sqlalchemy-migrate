"""
   Module for visitor class mapping.
"""
import sqlalchemy as sa

from migrate.changeset import ansisql
from migrate.changeset.databases import sqlite, postgres, mysql, oracle


# Map SA dialects to the corresponding Migrate extensions
DIALECTS = {
    sa.engine.default.DefaultDialect: ansisql.ANSIDialect,
    sa.databases.sqlite.SQLiteDialect: sqlite.SQLiteDialect,
    sa.databases.postgres.PGDialect: postgres.PGDialect,
    sa.databases.mysql.MySQLDialect: mysql.MySQLDialect,
    sa.databases.oracle.OracleDialect: oracle.OracleDialect,
}


def get_engine_visitor(engine, name):
    """
    Get the visitor implementation for the given database engine.

    :param engine: SQLAlchemy Engine
    :param name: Name of the visitor
    :type name: string
    :type engine: Engine
    :returns: visitor
    """
    # TODO: link to supported visitors
    return get_dialect_visitor(engine.dialect, name)


def get_dialect_visitor(sa_dialect, name):
    """
    Get the visitor implementation for the given dialect.

    Finds the visitor implementation based on the dialect class and
    returns and instance initialized with the given name.

    Binds dialect specific preparer to visitor.
    """

    # map sa dialect to migrate dialect and return visitor
    sa_dialect_cls = sa_dialect.__class__
    migrate_dialect_cls = DIALECTS[sa_dialect_cls]
    visitor = getattr(migrate_dialect_cls, name)

    # bind preparer
    visitor.preparer = sa_dialect.preparer(sa_dialect)

    return visitor

def run_single_visitor(engine, visitorcallable, element, **kwargs):
    """Runs only one method on the visitor"""
    conn = engine.contextual_connect(close_with_result=False)
    try:
        visitor = visitorcallable(engine.dialect, conn)
        getattr(visitor, 'visit_' + element.__visit_name__)(element, **kwargs)
    finally:
        conn.close()
