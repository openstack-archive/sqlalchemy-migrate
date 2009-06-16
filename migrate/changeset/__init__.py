"""
   This module extends SQLAlchemy and provides additional DDL [#]_
   support.

   .. [#] SQL Data Definition Language
"""
import sqlalchemy

from migrate.changeset.schema import *
from migrate.changeset.constraint import *

sqlalchemy.schema.Table.__bases__ += (ChangesetTable, )
sqlalchemy.schema.Column.__bases__ += (ChangesetColumn, )
sqlalchemy.schema.Index.__bases__ += (ChangesetIndex, )
