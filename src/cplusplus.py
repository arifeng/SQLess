#coding: utf-8
# C++ 目标代码生成器

import common
import uuid

kDatabasePrefix = 'SQLessDB_'
kTablePrefix = 'SQLessTable_'
KColumnPrefix = 'SQLessCol_'
kIdent = '    '

class CPlusPlus:
    def __init__(self, schema, sqlgen, namespace):
        self.sqlgen = sqlgen
        self.schema = schema
        self.namespace = namespace

    def Generate(self):
        print self._Header()
        print self._ForwardDeclare()
        print self._DeclareConnection()

        for database in self.schema['databases']:
            print self._DeclareDatabase(database)
            for table in database['tables']:
                print self._DeclareTable(table, database['name'])

        print self._Footer()

    def _ForwardDeclare(self):
        '''所有数据库类、表类的前置声明'''
        fd = ''
        for database in self.schema['databases']:
           fd += 'class ' + kDatabasePrefix + database['name'] + ';\n'
           for table in database['tables']:
               fd += 'class ' + kTablePrefix + table['name'] + ';\n'

        return fd;


    def _DeclareConnection(self):
        dc = '''
// 数据库连接
class SQLessConn {
public:
    SQLessConn();
    ~SQLessConn();

    typedef $HANDLE_TYPE Handle;

    bool connect($CONNECT_PARAMS);

    // 数据库连接是否有效
    bool isValid();

    // 事务处理
    void beginTransition();
    void endTransition();

    // 执行数据库无关的查询，如查询服务器版本
    bool execQuery(const std::string& sql_stmt, std::string* result);

    // 关闭数据库连接
    // 同时delete所有的用户数据库实例
    void close();

    Handle handle() { return handle_; }

    // 是否存在的数据库
'''

        # 数据库底层句柄和连接参数
        handle_type = ''
        connect_params = ''
        if self.sqlgen.Name() == 'sqlite':
            handle_type = 'sqlite3*'
            connect_params = 'const std::string& path, const std::string& key = ""'
        else:
            print 'Unknown database: ' + self.sqlgen.Name()
            exit(1)

        dc = dc.replace('$HANDLE_TYPE', handle_type)
        dc = dc.replace('$CONNECT_PARAMS', connect_params)

        for database in self.schema['databases']:
            dc += kIdent + 'bool has_database_' + database['name'] + '();\n'
            dc += kIdent + kDatabasePrefix + database['name'] + '* database_' + database['name'] + '();\n'  # 数据库获取函数

        dc += '\nprivate:\n'
        for database in self.schema['databases']:
            dc += kIdent + kDatabasePrefix + database['name'] + '* database_' + database['name'] + '_;\n'

        dc += '};\n'

        return dc

    def _DeclareDatabase(self, schema):
        template = '''
class $DATABASE_NAME {
public:
    $DATABASE_NAME(SqlPlusConn* conn);
    ~$DATABASE_NAME();

    bool exists();

    // 删除数据库
    // 将同时delete所有的数据表实例
    void drop();

    // 获取所属的数据库连接
    SqlPlusConn* connection() { return conn_; }

    // 直接执行SQL语句
    bool execQuery(const std::string& sql_stmt);

    // 指定数据表是否存在以及获取相应表
$TABLE_GETTERS

public:
    static const char kName[];
    static const char kDescription[];

private:
    // 创建本数据库
    bool create();

    // 切换到当前数据库
    bool use();

private:
    SqlPlusConn* conn_;

$TABLE_MEMBERS
};
'''
        template = template.replace('$DATABASE_NAME', kDatabasePrefix + schema['name'])

        table_getters = ''
        for table in schema['tables']:
            table_getters += kIdent + 'has_table_' + table['name'] + '();\n'
            table_getters += kIdent + kTablePrefix + table['name'] + '* table_' + table['name'] + '();\n'
        template = template.replace('$TABLE_GETTERS', table_getters)

        table_members_ = ''
        for database in schema['tables']:
            table_members_ += kIdent + kTablePrefix + table['name'] + '* table_' + table['name'] + '_;\n'
        template = template.replace('$TABLE_MEMBERS', table_members_)

        return template

    def _DeclareTable(self, schema, database):
        template = '''
class $TABLE_NAME {
public:
    $TABLE_NAME($DATABASE_NAME* db);
    ~$TABLE_NAME();

    // 当前数据表是否存在
    bool exists();

    // 删除数据表
    bool drop();

    // 获取所属的数据库
    $DATABASE_NAME* database() { return db_; }

    // 包含的记录数
    int row_count();

    // 插入参数
$INSERT_PARAM

    // 插入操作
    bool insert(const InsertParam& param);

    // 查询参数
$SELECT_PARAM

    // 查询结果
$SELECT_RESULT

    // 查询操作
    bool select(const SelectParam& param, SelectResult* result);

    // 更新参数
$UPDATE_PARAM

    // 更新操作
    bool update(const UpdateParam& param, int* affected_rows = NULL);

    // 删除操作
    bool remove(const std::string& condition, int* affected_rows = NULL);

    // 清空所有记录
    bool clear(int* affected_rows = NULL);

public:
    static const char kName[];
    static const char kDescription[];

private:
    // 创建数据表
    bool create();

private:
    // 所属数据库
    $DATABASE_NAME* db_;
};
'''
        template = template.replace('$TABLE_NAME', kTablePrefix + schema['name'])
        template = template.replace('$DATABASE_NAME', kDatabasePrefix + database)

        template = template.replace('$INSERT_PARAM', self._DeclareInsertParam(schema))
        template = template.replace('$SELECT_PARAM', self._DeclareSelectParam(schema))
        template = template.replace('$SELECT_RESULT', self._DeclareSelectResult(schema))
        template = template.replace('$UPDATE_PARAM', self._DeclareUpdateParam(schema))

        return template

    def _DeclareInsertParam(self, schema):
        return 'NOT_IMPLEMENTED'

    def _DeclareSelectParam(self, schema):
        return 'NOT_IMPLEMENTED'

    def _DeclareSelectResult(self, schema):
        return 'NOT_IMPLEMENTED'

    def _DeclareUpdateParam(self, schema):
        return 'NOT_IMPLEMENTED'

    def _Header(self):
        h = '''// Generated by SQLess v$VERSION
// project homepage http://www.sqless.org

#ifndef SQLESS_$UUID_H
#define SQLESS_$UUID_H

#include <string>
#include <vector>
        '''
        h = h.replace('$VERSION', common.Version())
        h = h.replace('$UUID', str(uuid.uuid1()))

        # 数据库所需要的头文件
        h += '\n'
        if self.sqlgen.Name() is 'sqlite':
            h += '#include <sqlite3.h>'
        else:
            print 'unknown database ' + str(self.sqlgen.Name())
            exit(1)
        h += '\n';

        # 命名空间
        if self.namespace:
            h += '\nnamespace ' + self.namespace + ' {\n'

        return h


    def _Footer(self):
        f= '\n\n'

        if self.namespace:
            f += '} // namespace ' + self.namespace + '\n\n'

        f += '#endif\n'

        return f

