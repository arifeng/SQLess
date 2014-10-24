#coding: utf-8
# SQLite数据库支持

class Sqlite:
    def __init__(self):
        pass

    def Name(self):
        return 'sqlite'

    def CreateDatabaseSQL(self, schema):
        return 'CREATE DATABASE ' + schema['name']

    def CreateTableSQL(self, schema, if_not_exists=False):
        if schema.get('type'):
            return self._CreateVirtualTable(schema)

        _if_not_exists = 'IF NOT EXISTS ' if if_not_exists else ''
        sql = 'CREATE TABLE ' + _if_not_exists + schema['name'] + ' ('
        index_cols = []

        for col in schema['columns']:
            ctype = self.MapDataType(col['type'])

            if col.get('index') or col.get('indexed'):
                index_cols.append(col['name'])

            sql += col['name'] + ' ' + ctype

            if col.get('primary_key'):
                sql += ' PRIMARY_KEY'
            if col.get('auto_increment'):
                sql += ' AUTO_INCREMENT'

            default_value = col.get('default')
            if type(default_value) == type(0):
              sql += ' DEFAULT ' + str(default_value)
            elif type(default_value) == type(''):
              sql += ' DEFAULT \'' + default_value + '\''
            elif default_value:
              print 'unknown default value: ' + str(default_value)
              exit(1)

            sql += ', '

        sql = sql.rstrip(', ') + '); '

        # 为指定的列创建索引
        for index_col in index_cols:
            sql += self._CreateIndexSQL(schema['name'], index_col)

        print sql
        return sql

    def _CreateVirtualTable(self, schema):
        '''创建虚表，虚表不支持创建索引，也不支持 IF NOT EXISTS 从句'''
        # https://www.sqlite.org/vtab.html
        sql = 'CREATE VIRTUAL TABLE ' + schema['name'] + \
              ' USING ' + schema['type'] + ' ('

        for col in schema['columns']:
            sql += col['name'] + ', '

        sql = sql.rstrip(', ') + '); '

        print sql
        return sql

    def _CreateIndexSQL(self, table, column):
        '''创建索引'''
        # CREATE INDEX table_column_index ON table(column);
        return 'CREATE INDEX ' + table + '_' + column + '_index ON ' + table + '(' + column + '); '

    def HasTableSQL(self, table):
        ''' 数据库中是否存在指定名称的表 '''
        return 'SELECT name FROM sqlite_master WHERE type = "table" AND name = "' + table + '";'


    def DropTableSQL(self, table):
        ''' 删除数据表 '''
        return 'DROP TABLE IF EXISTS "' + table + '";'


    def BeginTransitionSQL(self):
        return 'BEGIN;'

    def EndTransitionSQL(self):
        return 'COMMIT;'

    def MapDataType(self, t):
        integer_alias = ['integer', 'INTEGER', 'int', 'INT']
        bigint_alias = ['bigint', 'BIGINT', 'largeint', 'LARGEINT']
        real_alias = ['real', 'REAL', 'float', 'FLOAT', 'double', 'DOUBLE']
        text_alias = ['text', 'TEXT', 'char', 'varchar', 'text']
        blob_alias = ['blob', 'BLOB', 'BINARY']

        if t in integer_alias:
            col_type = 'INTEGER'
        elif t in bigint_alias:
            col_type = 'BIGINT'
        elif t in real_alias:
            col_type = 'REAL'
        elif t in text_alias:
            col_type = 'TEXT'
        elif t in blob_alias:
            col_type = 'BLOB'
        else:
            print 'unknown column type: ' + t
            exit(1)

        return col_type
