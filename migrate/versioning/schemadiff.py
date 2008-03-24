
import sqlalchemy


def getDiffOfModelAgainstDatabase(model, conn, excludeTables=None):
    ''' Return differences of model against database.
        Returned object will evaluate to True if there are differences else False.
    '''
    return SchemaDiff(model, conn, excludeTables)
    

class SchemaDiff(object):
    ''' Differences of model against database. '''
    
    def __init__(self, model, conn, excludeTables=None):
        ''' Parameter model is your Python model's metadata and conn is an active database connection. '''
        self.model = model
        self.conn = conn
        if not excludeTables: excludeTables = []  # [] can't be default value in Python parameter
        self.excludeTables = excludeTables
        self.reflected_model = sqlalchemy.MetaData(conn, reflect=True)
        self.tablesMissingInDatabase, self.tablesMissingInModel, self.tablesWithDiff = [], [], []
        self.colDiffs = {}
        self.compareModelToDatabase()
        
    def compareModelToDatabase(self):
        ''' Do actual comparison. '''
       
        # Setup common variables.
        cc = self.conn.contextual_connect()
        schemagenerator = self.conn.dialect.schemagenerator(self.conn.dialect, cc)
        
        # For each in model, find missing in database.
        for modelName, modelTable in self.model.tables.items():
            if modelName in self.excludeTables:
                continue
            reflectedTable = self.reflected_model.tables.get(modelName, None)
            if reflectedTable:
                # Table exists.
                pass
            else:
                self.tablesMissingInDatabase.append(modelTable)
        
        # For each in database, find missing in model.
        for reflectedName, reflectedTable in self.reflected_model.tables.items():
            if reflectedName in self.excludeTables:
                continue
            modelTable = self.model.tables.get(reflectedName, None)
            if modelTable:
                # Table exists.
                
                # Find missing columns in database.
                for modelCol in modelTable.columns:
                    databaseCol = reflectedTable.columns.get(modelCol.name, None)
                    if databaseCol:
                        pass
                    else:
                        self.storeColumnMissingInDatabase(modelTable, modelCol)
                
                # Find missing columns in model.
                for databaseCol in reflectedTable.columns:
                    modelCol = modelTable.columns.get(databaseCol.name, None)
                    if modelCol:
                        # Compare attributes of column.
                        modelDecl = schemagenerator.get_column_specification(modelCol)
                        databaseDecl = schemagenerator.get_column_specification(databaseCol)
                        if modelDecl != databaseDecl:
                            # Unfortunately, sometimes the database decl won't quite match the model, even though they're the same.
                            mc, dc = modelCol.type.__class__, databaseCol.type.__class__
                            if (issubclass(mc, dc) or issubclass(dc, mc)) and modelCol.nullable == databaseCol.nullable:
                                # Types and nullable are the same.
                                pass
                            else:
                                self.storeColumnDiff(modelTable, modelCol, databaseCol, modelDecl, databaseDecl)
                    else:
                        self.storeColumnMissingInModel(modelTable, databaseCol)
            else:
                self.tablesMissingInModel.append(reflectedTable)
        
    def __str__(self):
        ''' Summarize differences. '''
        
        def colDiffDetails():
            colout = []
            for table in self.tablesWithDiff:
                tableName = table.name
                missingInDatabase, missingInModel, diffDecl = self.colDiffs[tableName]
                if missingInDatabase:
                    colout.append('    %s missing columns in database: %s' % (tableName, ', '.join([col.name for col in missingInDatabase])))
                if missingInModel:
                    colout.append('    %s missing columns in model: %s' % (tableName, ', '.join([col.name for col in missingInModel])))
                if diffDecl:
                    colout.append('    %s with different declaration of columns in database: %s' % (tableName, str(diffDecl)))
            return colout
            
        out = []
        if self.tablesMissingInDatabase:
            out.append('  tables missing in database: %s' % ', '.join([table.name for table in self.tablesMissingInDatabase]))
        if self.tablesMissingInModel:
            out.append('  tables missing in model: %s' % ', '.join([table.name for table in self.tablesMissingInModel]))
        if self.tablesWithDiff:
            out.append('  tables with differences: %s' % ', '.join([table.name for table in self.tablesWithDiff]))
            
        if out:
            out.insert(0, 'Schema diffs:')
            out.extend(colDiffDetails())
            return '\n'.join(out)
        else:
            return 'No schema diffs'
    
    #__repr__ = __str__
    
    def __len__(self):
        ''' Used in bool evaluation, return of 0 means no diffs. '''
        return len(self.tablesMissingInDatabase) + len(self.tablesMissingInModel) + len(self.tablesWithDiff)
    
    def storeColumnMissingInDatabase(self, table, col):
        if table not in self.tablesWithDiff:
            self.tablesWithDiff.append(table)
        missingInDatabase, missingInModel, diffDecl = self.colDiffs.setdefault(table.name, ([], [], []))
        missingInDatabase.append(col)
   
    def storeColumnMissingInModel(self, table, col):
        if table not in self.tablesWithDiff:
            self.tablesWithDiff.append(table)
        missingInDatabase, missingInModel, diffDecl = self.colDiffs.setdefault(table.name, ([], [], []))
        missingInModel.append(col)
   
    def storeColumnDiff(self, table, modelCol, databaseCol, modelDecl, databaseDecl):
        if table not in self.tablesWithDiff:
            self.tablesWithDiff.append(table)
        missingInDatabase, missingInModel, diffDecl = self.colDiffs.setdefault(table.name, ([], [], []))
        diffDecl.append( (modelCol, databaseCol, modelDecl, databaseDecl) )
   
