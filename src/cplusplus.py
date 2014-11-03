#coding: utf-8
# 生成C++ 目标代码头文件(.h)

import time
import uuid

import config
import cplusplus_sqlite
import pyutil

class CPlusPlus:
    def __init__(self, schema, sqlgen, savepath):
        self.sqlgen = sqlgen
        self.schema = schema
        self.namespace = schema['namespace']
        self.savepath = savepath
        self.impl = cplusplus_sqlite.CPlusPlusImpl(schema, sqlgen, self, savepath)

    def Generate(self):
        utf8_bom = '\xEF\xBB\xBF'
        pyutil.WriteFile(self.savepath + '.h', utf8_bom + self.GenerateHeaderFile())
        pyutil.WriteFile(self.savepath + '.cc',utf8_bom + self.impl.GenerateImplFile())

    def GenerateHeaderFile(self):
        content = self._Header()
        content += self._ForwardDeclare()
        content += self._DeclareConnection()

        for database in self.schema['databases']:
            content += self._DeclareDatabase(database)
            for table in database['tables']:
                content += self._DeclareTable(table, database['name'])
            if database.get('views'):
                for view in database['views']:
                    content += self._DeclareView(database, view)

        content += self._Footer()
        return content

    def _ForwardDeclare(self):
        '''所有数据库类、表类的前置声明'''
        fd = '\n'
        for database in self.schema['databases']:
            fd += 'class ' + config.kDatabasePrefix + database['name'] + ';\n'
            for table in database['tables']:
                fd += 'class ' + config.kTablePrefix + table['name'] + ';\n'
                for col in table['columns']:
                    fd += 'class ' + config.kColumnPrefix + table['name'] + '_' + col['name'] + ';\n'
            if database.get('views'):
                for view in database['views']:
                    fd += 'class ' + config.kViewPrefix + view['name'] + ';\n'

        fd += '\n' + 'typedef std::vector<std::vector<std::string> > SQLessResults;' + '\n'

        return fd;


    def _DeclareConnection(self):
        dc = '''
// 数据库连接
class SQLessConn {
public:
    SQLessConn();
    ~SQLessConn();

    typedef $HANDLE_TYPE Handle;

    // 连接到数据库
    bool connect($CONNECT_PARAMS);

    // 数据库连接是否有效
    bool isValid();

    // 数据库版本
    std::string version();

    // 返回底层数据库句柄
    Handle handle() { return handle_; }

    // 执行查询，返回全部结果集
    // 请使用LIMIT关键字限制结果行数
    bool exec(const std::string& sql_stmt, SQLessResults* result);

    // 执行查询，返回查询结果第一行的第一列的值
    bool exec(const std::string& sql_stmt, std::string* result = NULL);

    // 关闭数据库连接
    // 同时delete所有的用户数据库实例
    void close();

    // 事务处理
    void beginTransaction();
    void endTransaction();

    // 错误处理
    int lastErrorCode();
    std::string lastErrorMsg();

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
            dc += config.kIdent + 'bool has_database_' + database['name'] + '();\n'
            dc += config.kIdent + config.kDatabasePrefix + database['name'] + '* database_' + database['name'] + '();\n'  # 数据库获取函数

        dc += '\nprivate:\n'
        for database in self.schema['databases']:
            dc += config.kIdent + config.kDatabasePrefix + database['name'] + '* database_' + database['name'] + '_;\n'

        dc += '\n' + config.kIdent + 'Handle handle_;\n'

        dc += '};\n'

        return dc

    def _DeclareDatabase(self, schema):
        template = '''
// $DESCRIPTION
class $DATABASE_NAME {
public:
    $DATABASE_NAME(SQLessConn* conn);
    ~$DATABASE_NAME();

    bool exists();

    // 创建本数据库
    bool create();

    // 删除数据库
    // 将同时delete所有的数据表实例
    void drop();

    // 获取所属的数据库连接
    SQLessConn* connection() { return conn_; }

    // 直接执行SQL语句
    bool exec(const std::string& sql_stmt);

    // 指定数据表是否存在以及获取相应表
$TABLE_GETTERS
$VIEW_GETTERS
public:
    static const char kName[];

private:
    // 切换到当前数据库
    bool use();

private:
    SQLessConn* conn_;

$TABLE_MEMBERS
$VIEW_MEMBERS
};
'''
        template = template.replace('$DATABASE_NAME', config.kDatabasePrefix + schema['name'])
        template = template.replace('$DESCRIPTION', schema['desc'])

        table_getters = ''
        table_members_ = ''
        for table in schema['tables']:
            table_getters += config.kIdent + 'bool has_table_' + table['name'] + '();\n'
            table_getters += config.kIdent + config.kTablePrefix + table['name'] + '* table_' + table['name'] + '();\n'
            table_members_ += config.kIdent + config.kTablePrefix + table['name'] + '* table_' + table['name'] + '_;\n'

        view_getters = ''
        view_members = ''
        if schema.get('views'):
            for view in schema['views']:
                view_getters += config.kIdent + 'bool has_view_' + view['name'] + '();\n'
                view_getters += config.kIdent + config.kViewPrefix + view['name'] + '* view_' + view['name'] + '();\n'
                view_members += config.kIdent + config.kViewPrefix + view['name'] + '* view_' + view['name'] + '_;\n'

        template = template.replace('$TABLE_GETTERS', table_getters)
        template = template.replace('$TABLE_MEMBERS', table_members_)
        template = template.replace('$VIEW_GETTERS',  view_getters)
        template = template.replace('$VIEW_MEMBERS',  view_members)

        return template

    def _DeclareTable(self, schema, database):
        template = '''
// $DESCRIPTION
class $TABLE_NAME {
public:
    $TABLE_NAME($DATABASE_NAME* db);
    ~$TABLE_NAME();

    // 当前数据表是否存在
    bool exists();

    // 创建数据表
    bool create();

    // 删除数据表
    bool drop();

    // 获取所属的数据库
    $DATABASE_NAME* database() { return db_; }

    // 查询符合条件的记录数
    // 不传参数或参数为空返回表的总行数
    // 返回-1表示出错
    int row_count(const std::string& condition = "");

    // 插入参数
$INSERT_PARAM

    // 插入操作
    // 如果表中有 INTEGER PRIMARY KEY 的列，通过 inserted_row_id 可以获取到刚插入的行的该列的值
    // 如果没有此种类型的列，sqlite将使用 _ROWID_ 代替
    bool insert(const InsertParam& param, int64_t* inserted_row_id = NULL);

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
    // 注：delete是C++的关键字不能使用
    bool remove(const std::string& condition, int* affected_rows = NULL);

    // 清空所有记录
    bool clear(int* affected_rows = NULL);

    // 获取列
$COLUMN_GETTERS

public:
    static const char kName[];

private:
    // 所属数据库
    $DATABASE_NAME* db_;

    //列成员
$COLUMN_MEMBERS
};
'''
        # FIXME：废弃的
        column_members = ''
        column_getters = ''
        for col in schema['columns']:
            col_class = config.kColumnPrefix + schema['name'] + '_' + col['name']   # SQLessColumn_table_column
            column_getters += config.kIdent + col_class + '* column_' + col['name'] + '();\n'
            column_members += config.kIdent + col_class + '* column_' + col['name'] + '_;\n'

        template = template.replace('$COLUMN_MEMBERS', column_members)
        template = template.replace('$COLUMN_GETTERS', column_getters)

        template = template.replace('$DESCRIPTION', schema['desc'])
        template = template.replace('$TABLE_NAME', config.kTablePrefix + schema['name'])
        template = template.replace('$DATABASE_NAME', config.kDatabasePrefix + database)

        template = template.replace('$INSERT_PARAM', self._DeclareInsertParam(schema, config.kTablePrefix + schema['name']))
        template = template.replace('$SELECT_PARAM', self._DeclareSelectParam(schema, config.kTablePrefix + schema['name']))
        template = template.replace('$SELECT_RESULT', self._DeclareSelectResult(schema, config.kTablePrefix + schema['name']))
        template = template.replace('$UPDATE_PARAM', self._DeclareUpdateParam(schema, config.kTablePrefix + schema['name']))

        for col in schema['columns']:
            template += self._DeclareColumn(schema['name'], col)

        return template

    def _SQLTypeToCPPType(self, col_type, is_param):
        '''将SQL的数据类型转为相应C++数据类型'''
        if self.sqlgen.Name() != 'sqlite':
            print 'Unknown database :' + self.sqlgen.Name()
            exit(1)

        sql_type = self.sqlgen.MapDataType(col_type)
        cpp_type = ''
        if sql_type == 'INTEGER':
            cpp_type = 'int'
        elif sql_type == 'BIGINT':
            cpp_type = 'int64_t'
        elif sql_type == 'REAL':
            cpp_type = 'double'
        elif sql_type == 'TEXT' or sql_type == 'BLOB':
            cpp_type = 'const std::string&' if is_param else 'std::string'
        else:
            print 'unknown SQL type: ' + sql_type
            exit(1)

        return cpp_type

    def _DeclareInsertParam(self, schema, table):
        template = '''
    class InsertParam {
    public:
        InsertParam();
        ~InsertParam();

$COLUMN_SETTERS
    private:
        friend class $TABLE_NAME;
$COLUMN_MEMBERS
    };
        '''

        template = template.replace('$TABLE_NAME', table)

        column_setters = ''
        column_members = ''
        for col in schema['columns']:
            # void set_col1(int i);
            column_setters += config.kIdent2 + 'InsertParam& set_' + col['name'] + '(' + self._SQLTypeToCPPType(col['type'], True) + ');\n'
            # std::string col3_;
            column_members += config.kIdent2 + self._SQLTypeToCPPType(col['type'], False) + ' ' + col['name'] + '_;\n'
            # bool has_col3_;
            column_members += config.kIdent2 + 'bool has_' + col['name'] + '_;\n'

        template = template.replace('$COLUMN_SETTERS', column_setters)
        template = template.replace('$COLUMN_MEMBERS', column_members)

        return template


    def _DeclareSelectParam(self, schema, table):
        template = """
    class SelectParam {
      public:
          SelectParam();
          ~SelectParam();

          SelectParam&  add_all();

$COLUMN_ADDERS

$COLUMN_ORDERBYS

        void set_condition(const std::string& cond) { condition_ = cond; }
        void set_limit(int count) { limit_ = count; }
        void set_offset(int offset) { offset_ = offset; }

      private:
        friend class $TABLE_NAME;

$COLUMN_STATUS

        std::string condition_;
        std::string order_by_;
        bool desc_;
        int limit_;
        int offset_;
    };
        """

        template = template.replace('$TABLE_NAME', table)

        column_adders = ''
        column_orderbys = ''
        column_status = ''
        for col in schema['columns']:
            # void add_col1() { col1_ = true; }
            column_adders += config.kIdent2 + 'SelectParam& add_' + col['name'] + '() { ' + col['name'] + '_ = true; return *this; }\n'
            # void order_by_col1(bool desc = false);
            column_orderbys += config.kIdent2 + 'SelectParam& order_by_' + col['name'] + '(bool desc = false);\n'
            # bool col1_;
            column_status += config.kIdent2 + 'bool ' + col['name'] + '_;\n'

        template = template.replace('$COLUMN_ADDERS', column_adders)
        template = template.replace('$COLUMN_ORDERBYS', column_orderbys)
        template = template.replace('$COLUMN_STATUS', column_status)

        return template

    def _DeclareSelectResult(self, schema, table):
        template = """
  class SelectResult {
    public:
        SelectResult();
        ~SelectResult();

$COLUMN_GETTERS

        bool getRow();  // 获取下一条结果
    private:
        friend class $TABLE_NAME;
        sqlite3_stmt* stmt_;
        SelectParam param_;

$COLUMN_VALUES
    };
        """

        template = template.replace('$TABLE_NAME', table)

        column_getters = ''
        column_values = ''
        for col in schema['columns']:
            cpp_type = self._SQLTypeToCPPType(col['type'], False)
            cpp_type_ref = self._SQLTypeToCPPType(col['type'], True)
            # int col1() { return col1_; }
            column_getters += config.kIdent2 + cpp_type_ref + ' ' + col['name'] + '() const { return ' + col['name'] + '_; }\n'
            # int col1_;
            column_values += config.kIdent2 + cpp_type + ' ' + col['name'] + '_;\n'

        template = template.replace('$COLUMN_GETTERS', column_getters)
        template = template.replace('$COLUMN_VALUES', column_values)

        return template

    def _DeclareUpdateParam(self, schema, table):
        template = """
    class UpdateParam {
    public:
        UpdateParam();
        ~UpdateParam();

$COLUMN_SETTERS

        void set_condition(const std::string& cond) { condition_ = cond; }

    private:
        friend class $TABLE_NAME;

        std::string condition_;

$COLUMN_MEMBERS
    };
        """

        template = template.replace('$TABLE_NAME', table)

        column_setters = ''
        column_members = ''
        for col in schema['columns']:
            # void set_col1(int i);
            column_setters += config.kIdent2 + 'UpdateParam& set_' + col['name'] + '(' + self._SQLTypeToCPPType(col['type'], True) + ');\n'
            # std::string col3_;
            column_members += config.kIdent2 + self._SQLTypeToCPPType(col['type'], False) + ' ' + col['name'] + '_;\n'
            # bool has_col3_;
            column_members += config.kIdent2 + 'bool has_' + col['name'] + '_;\n'

        template = template.replace('$COLUMN_SETTERS', column_setters)
        template = template.replace('$COLUMN_MEMBERS', column_members)

        return template


    def MockViewAsTableSchema(self, database, view):
        ''' 将View的定义转换为相应虚拟Table的格式 '''
        mock = {}
        mock['name'] = view['name']
        mock['desc'] = view['desc']

        def GetTableColumn(tname, cname):
            ''' 根据视图定义中列的属性查找相应表中的列定义 '''
            for table in database['tables']:
                if table['name'] == tname:
                    for column in table['columns']:
                        if column['name'] == cname:
                            return column

        mock_columns = []
        for col in view['columns']:
            mock_column = {}
            # 如果指定了列的名称，则使用指定的名称，如同 AS 关键字
            if col.get('name'):
                mock_column['name'] = col['name']
            else:
                mock_column['name'] = col['table'] + '_' + col['column']
            # 视图的列源自的表和表的列必须存在，否则以下语句执行将出错
            orig_col = GetTableColumn(col['table'], col['column'])
            mock_column['type'] = orig_col['type']
            # 优先使用视图中的描述信息
            if col.get('desc'):
                mock_column['desc'] = col['desc']
            else:
                mock_column['desc'] = orig_col['desc']

            mock_columns.append(mock_column)

        mock['columns'] = mock_columns
        return mock


    def _DeclareView(self, db_schema, schema):
        template = '''
// $DESCRIPTION
class SQLessView_$VIEW {
public:
    SQLessView_$VIEW(SQLessDB_$DATABASE* db);
    ~SQLessView_$VIEW();

    // 视图是否存在
    bool exists();

    // 创建视图
    bool create(const std::string &condition);

    // 删除视图
    bool drop();

    // 获取所属的数据库
    SQLessDB_$DATABASE* database() { return db_; }

    // 查询符合条件的记录数
    // 不传参数或参数为空返回表的总行数
    // 返回-1表示出错
    int row_count(const std::string& condition = "");

    // 查询参数
$SELECT_PARAM


    // 查询结果
$SELECT_RESULT

    bool select(const SelectParam& param, SelectResult* result);

public:
    static const char kName[];

private:
    SQLessDB_$DATABASE* db_;
};
'''
        # 根据视图的定义模拟表的操作，重用table的 SelectParam 和 SelectResult
        mock_schema = self.MockViewAsTableSchema(db_schema, schema)
        view_name = config.kViewPrefix + schema['name']

        template = template.replace('$VIEW', schema['name'])
        template = template.replace('$DESCRIPTION', schema['desc'])
        template = template.replace('$DATABASE', db_schema['name'])
        template = template.replace('$SELECT_PARAM', self._DeclareSelectParam(mock_schema, view_name))
        template = template.replace('$SELECT_RESULT', self._DeclareSelectResult(mock_schema, view_name))

        print self.sqlgen.CreateViewSQL(schema)

        return template


    def _DeclareColumn(self, table, schema):
        template = '''
// $DESCRIPTION
class SQLessColumn_$TABLE_$COLUMN {
public:
    SQLessColumn_$TABLE_$COLUMN(SQLessTable_$TABLE* table);
    ~SQLessColumn_$TABLE_$COLUMN();

    // 获取所属的表
    SQLessTable_$TABLE* table() { return table_; }

    // 该列是否存在，如果存在 real_type 代表当前数据库里的列类型
    // 注：通过kType获取到的是当前json描述文件里的类型，列的类型可能发生了变化
    bool exists();

    // 创建本列
    bool create();

    // 数据库已经为主键建了索引，并且主键是唯一的
    // 对于整数类型的主键，该列的值还会自动增长
    bool is_primary_key() { return $IS_PRIMARY_KEY; }

    // 该列是否建了索引
    bool is_indexed() { return $IS_INDEXED; }

    // 该列中的值是否唯一化
    bool is_unique() { return $IS_UNIQUE; }

    // 是否自动增加
    bool is_auto_increment() { return $IS_AUTO_INCREMENT; }

    // 是否保证非空
    bool is_not_null() { return $IS_NOT_NULL; }

public:
    // 列名
    static const char kName[];

    // 列的类型(在schema.json文件中指定的)
    static const char kType[];
$DEFAULT_VALUE
private:
    SQLessTable_$TABLE* table_;
};
'''
        is_primary_key = schema.get('primary_key')

        default_value = ''
        if 'default' in schema:
            default_value = '\n' + config.kIdent + 'static const '
            stype = self.sqlgen.MapDataType(schema['type'])
            if stype == 'INTEGER' or stype == 'BIGINT':
                default_value += self._SQLTypeToCPPType(schema['type'], False) + ' kDefault = ' + str(schema['default']) + ';\n'
            elif stype == 'TEXT':
                default_value += 'char kDefault[];\n'   # 在cc文件中定义
            else:
                print 'Default value not supported for column ' + schema['name'] + ' with type ' + schema['type']
                exit(1)

        template = template.replace('$COLUMN', schema['name'])
        template = template.replace('$DESCRIPTION', schema['desc'])
        template = template.replace('$TABLE', table)

        template = template.replace('$IS_PRIMARY_KEY', 'true' if is_primary_key else 'false')
        template = template.replace('$IS_INDEXED', 'true' if is_primary_key or schema.get('index') or schema.get('indexed') else 'false')
        template = template.replace('$IS_UNIQUE', 'true' if is_primary_key or schema.get('unique') else 'false')
        template = template.replace('$IS_AUTO_INCREMENT', 'true' if is_primary_key or schema.get('unique') else 'false')
        template = template.replace('$IS_NOT_NULL', 'true' if is_primary_key or schema.get('not_null') else 'false')
        template = template.replace('$DEFAULT_VALUE', default_value)

        return template


    def _Header(self):
        h = '''// Generated by SQLess v$VERSION at $DATETIME
// project homepage http://www.SQLess.org

#ifndef SQLess_$UUID_H
#define SQLess_$UUID_H

#include <cstdint>
#include <string>
#include <vector>
        '''

        h = h.replace('$VERSION', config.version)
        h = h.replace("$DATETIME", time.strftime('%Y-%m-%d %X', time.localtime()))
        h = h.replace('$UUID', str(uuid.uuid1()).replace('-', '_'))

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
