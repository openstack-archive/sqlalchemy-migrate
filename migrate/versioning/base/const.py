__all__ = ['databases','operations']

#databases = ('sqlite','postgres','mysql','oracle','mssql','firebird')
databases = ('sqlite','postgres','mysql','oracle','mssql')

# Map operation names to function names
from sqlalchemy.util import OrderedDict
operations = OrderedDict()
operations['upgrade'] = 'upgrade'
operations['downgrade'] = 'downgrade'
