#!/usr/bin/env python
# -*- coding: utf-8 -*-

from migrate.versioning.script import base


class SqlScript(base.BaseScript):
    """A file containing plain SQL statements."""

    # TODO: why is step parameter even here?
    def run(self, engine, step=None):
        """Runs SQL script through raw dbapi execute call"""
        text = self.source()
        # Don't rely on SA's autocommit here
        # (SA uses .startswith to check if a commit is needed. What if script
        # starts with a comment?)
        conn = engine.connect()
        try:
            trans = conn.begin()
            try:
                # HACK: SQLite doesn't allow multiple statements through
                # its execute() method, but it provides executescript() instead
                dbapi = conn.engine.raw_connection()
                if getattr(dbapi, 'executescript', None):
                    dbapi.executescript(text)
                else:
                    conn.execute(text)
                trans.commit()
            except:
                trans.rollback()
                raise
        finally:
            conn.close()
