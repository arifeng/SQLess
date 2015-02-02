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
            sql += self._ColumnSQL(col) + ', '

            if col.get('index') or col.get('indexed'):
                index_cols.append(col['name'])

        sql = sql.rstrip(', ') + '); '

        # 为指定的列创建索引
        for index_col in index_cols:
            sql += self._CreateIndexSQL(schema['name'], index_col)

        print (sql)
        return sql

    def _ColumnSQL(self, schema):
        # col_demo INTEGER AUTO_INCREMENT UNIQUE NOT_NULL DEFAULT 0
        ctype = self.MapDataType(schema['type'])
        sql = schema['name'] + ' ' + ctype

        # 主键
        if schema.get('primary_key'):
            sql += ' PRIMARY_KEY'

        #  自增
        if schema.get('auto_increment'):
            if ctype != 'INTEGER' and ctype != 'BIGINT':
                print ('auto increment column type must be integer or bigint !')
                exti(1)
            sql += ' AUTO_INCREMENT'

        # 唯一约束
        if schema.get('unique'):
            sql += ' UNIQUE'

        # 非空约束
        if schema.get('not_null'):
            sql += ' NOT NULL'

        # 列的默认值
        default_value = schema.get('default')
        if type(default_value) == type(0):
          if ctype != 'INTEGER' and ctype != 'BIGINT':
            print ('Not an integer/bitint type but has a integer default value')
            exit(1)
          sql += ' DEFAULT ' + str(default_value)
        elif type(default_value) == type(''):
          if ctype != 'TEXT':
            print ('Not an text type but has a text default value')
            exit(1)
          sql += ' DEFAULT \'' + default_value + '\''
        elif default_value:
          print ('unknown default value: ' + str(default_value))
          exit(1)

        return sql


    def _CreateVirtualTable(self, schema):
        ''' 创建虚表，虚表不支持创建索引，也不支持 IF NOT EXISTS 从句 '''
        # https://www.sqlite.org/vtab.html
        sql = 'CREATE VIRTUAL TABLE ' + schema['name'] + \
              ' USING ' + schema['type'] + ' ('

        for col in schema['columns']:
            sql += col['name'] + ', '

        sql = sql.rstrip(', ') + '); '

        print (sql)
        return sql

    def _CreateIndexSQL(self, table, column):
        ''' 创建索引 '''
        # CREATE INDEX table_column_index ON table(column);
        return 'CREATE INDEX ' + table + '_' + column + '_index ON ' + table + '(' + column + '); '

    def HasTableSQL(self, table):
        ''' 数据库中是否存在指定名称的表 '''
        return 'SELECT name FROM (SELECT * FROM sqlite_master UNION ALL SELECT * FROM sqlite_temp_master) WHERE type = "table" AND name = "' + table + '";'

    def DropTableSQL(self, table):
        ''' 删除数据表 '''
        return 'DROP TABLE IF EXISTS "' + table + '";'

    def HasColumnSQL(self, table, column):
        ''' 列是否存在 '''
        return 'SELECT ' + column + ' FROM ' + table + ' LIMIT 0;'

    def AddColumnSQL(self, table, schema):
        ''' 添加新的一列 '''
        return 'ALTER TABLE ' +  table + ' ADD ' + self._ColumnSQL(schema) + ';'

    def HasViewSQL(self, view):
        ''' 视图是否存在 '''
        return 'SELECT name FROM (SELECT * FROM sqlite_master UNION ALL SELECT * FROM sqlite_temp_master)  WHERE type = "view" AND name = "' + view + '";'

    def DropViewSQL(self, view):
        ''' 删除视图 '''
        return 'DROP VIEW ' + view

    def CreateViewSQL(self, schema):
        ''' 创建视图，未附加任何条件限制，并以逗号结尾 '''
        _temp = 'TEMP ' if schema.get('temp') or schema.get('temporary') else ''
        sql = 'CREATE ' + _temp + 'VIEW ' + schema['name'] + ' AS SELECT '

        tables = []
        for col in schema['columns']:
            table = col['table']

            _as = ''
            if col.get('name'):
                _as = col['name']
            else:
                _as = col['table'] + '_' + col['column']

            sql += table + '.' + col['column'] + ' AS ' + _as + ', '
            if not table in tables:
                tables.append(table)

        sql = sql.rstrip(', ') + ' FROM ';

        for table in tables:
            sql += table + ', ';

        sql = sql.rstrip(', ') + ';';
        return sql


    def BeginTransitionSQL(self):
        ''' 开始事务 '''
        return 'BEGIN;'

    def EndTransitionSQL(self):
        ''' 提交事务 '''
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
            print ('unknown column type: ' + t)
            exit(1)

        return col_type
