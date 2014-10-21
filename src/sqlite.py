#coding: utf-8
# SQLite数据库支持

class Sqlite:
    def __init__(self):
        pass

    def Name(self):
        return 'sqlite'

    def CreateDatabaseSQL(self, schema):
        return 'CREATE DATABASE ' + schema['name']

    def CreateTableSQL(self, schema):
        sql = 'CREATE TABLE ' + schema['name'] + ' (\n';
        for col in schema['columns']:
            ctype = self._MapDataType(col['type'])

            sql += col['name'] + ' ' + ctype

            if col.get('primary_key'):
                sql += ' PRIMARY_KEY'
            if col.get('auto_increment'):
                sql += ' AUTOINCREMENT'

            default_value = col.get('default')
            if type(default_value) == type(0):
              sql += ' DEFAULT ' + str(default_value)
            elif type(default_value) == type(''):
              sql += ' DEFAULT \'' + default_value + '\''
            elif default_value:
              print 'unknown default value: ' + str(default_value)
              exit(1)

            sql += ',\n'

        sql += ');'

        return sql

    def _MapDataType(self, t):
        integer_alias = ['integer', 'INTEGER', 'int', 'INT']
        real_alias = ['real', 'REAL', 'float', 'FLOAT', 'double', 'DOUBLE']
        text_alias = ['text', 'TEXT', 'char', 'varchar', 'text']
        blob_alias = ['blob', 'BLOB', 'BINARY']

        if t in integer_alias:
            col_type = 'INTEGER'
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
