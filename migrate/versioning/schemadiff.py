"""
   Schema differencing support.
"""
import logging

import sqlalchemy
from migrate.changeset import SQLA_06


log = logging.getLogger(__name__)

def getDiffOfModelAgainstDatabase(metadata, engine, excludeTables=None):
    """
    Return differences of model against database.

    :return: object which will evaluate to :keyword:`True` if there \
      are differences else :keyword:`False`.
    """
    return SchemaDiff(metadata,
                      sqlalchemy.MetaData(engine, reflect=True),
                      labelA='model',
                      labelB='database',
                      excludeTables=excludeTables)


def getDiffOfModelAgainstModel(metadataA, metadataB, excludeTables=None):
    """
    Return differences of model against another model.

    :return: object which will evaluate to :keyword:`True` if there \
      are differences else :keyword:`False`.
    """
    return SchemaDiff(metadataA, metadataB, excludeTables)


class TableDiff(object):
    """
    Container for differences in one :class:`~sqlalchemy.schema.Table
    between two :class:`~sqlalchemy.schema.MetaData` instances, ``A``
    and ``B``.

    .. attribute:: columns_missing_from_A

      A sequence of column names that were found in B but weren't in
      A.
      
    .. attribute:: columns_missing_from_B

      A sequence of column names that were found in A but weren't in
      B.
      
    .. attribute:: columns_different

      An empty dictionary, for future use...
    """
    __slots__ = (
        'columns_missing_from_A',
        'columns_missing_from_B',
        'columns_different',
        )

    def __len__(self):
        return (
            len(self.columns_missing_from_A)+
            len(self.columns_missing_from_B)+
            len(self.columns_different)
            )
    
class SchemaDiff(object):
    """
    Compute the difference between two :class:`~sqlalchemy.schema.MetaData`
    objects.

    The string representation of a :class:`SchemaDiff` will summarise
    the changes found between the two
    :class:`~sqlalchemy.schema.MetaData` objects.

    The length of a :class:`SchemaDiff` will give the number of
    changes found, enabling it to be used much like a boolean in
    expressions.
        
    :param metadataA:
      First :class:`~sqlalchemy.schema.MetaData` to compare.
      
    :param metadataB:
      Second :class:`~sqlalchemy.schema.MetaData` to compare.
      
    :param labelA:
      The label to use in messages about the first
      :class:`~sqlalchemy.schema.MetaData`. 
    
    :param labelB: 
      The label to use in messages about the second
      :class:`~sqlalchemy.schema.MetaData`. 
    
    :param excludeTables:
      A sequence of table names to exclude.
    """

    def __init__(self,
                 metadataA, metadataB,
                 labelA='metadataA',
                 labelB='metadataB',
                 excludeTables=None):

        self.metadataA, self.metadataB = metadataA, metadataB
        self.labelA, self.labelB = labelA, labelB
        excludeTables = set(excludeTables or [])

        A_table_names = set(metadataA.tables.keys())
        B_table_names = set(metadataB.tables.keys())

        self.tables_missing_from_A = sorted(
            B_table_names - A_table_names - excludeTables
            )
        self.tables_missing_from_B = sorted(
            A_table_names - B_table_names - excludeTables
            )
        
        self.tables_different = {}
        for table_name in A_table_names.intersection(B_table_names):

            td = TableDiff()
            
            A_table = metadataA.tables[table_name]
            B_table = metadataB.tables[table_name]
            
            A_column_names = set(A_table.columns.keys())
            B_column_names = set(B_table.columns.keys())

            td.columns_missing_from_A = sorted(
                B_column_names - A_column_names
                )
            
            td.columns_missing_from_B = sorted(
                A_column_names - B_column_names
                )
            
            td.columns_different = {}

            # XXX - should check columns differences
            #for col_name in A_column_names.intersection(B_column_names):
            #
            #    A_col = A_table.columns.get(col_name)
            #    B_col = B_table.columns.get(col_name)
            
            # XXX - index and constraint differences should
            #       be checked for here

            if td:
                self.tables_different[table_name]=td

    def __str__(self):
        ''' Summarize differences. '''
        out = []
        
        for names,label in (
            (self.tables_missing_from_A,self.labelA),
            (self.tables_missing_from_B,self.labelB),
            ):
            if names:
                out.append(
                    '  tables missing from %s: %s' % (
                        label,', '.join(sorted(names))
                        )
                    )
                
        for name,td in sorted(self.tables_different.items()):
            out.append(
               '  table with differences: %s' % name
               )
            for names,label in (
                (td.columns_missing_from_A,self.labelA),
                (td.columns_missing_from_B,self.labelB),
                ):
                if names:
                    out.append(
                        '    %s missing these columns: %s' % (
                            label,', '.join(sorted(names))
                            )
                        )
                
        if out:
            out.insert(0, 'Schema diffs:')
            return '\n'.join(out)
        else:
            return 'No schema diffs'

    def __len__(self):
        """
        Used in bool evaluation, return of 0 means no diffs.
        """
        return (
            len(self.tables_missing_from_A) +
            len(self.tables_missing_from_B) +
            len(self.tables_different)
            )
