#coding: utf-8
# 生成C++ 目标代码实现文件(.cpp)

import os
import time

import config
import cplusplus
import pyutil

class CPlusPlusImpl:
    def __init__(self, schema, sqlgen, declare, savename):
        self.sqlgen = sqlgen
        self.schema = schema
        self.savename = savename
        self.namespace = schema['namespace']
        self.declare = declare

    def GenerateImplFile(self):
        content = self._Header()
        content += self._ImplConnect()

        for database in self.schema['databases']:
            content += self._ImplDatabase(database)
            for table in database['tables']:
                content += self._ImplTable(table, database['name'])
            if database.get('views'):
                for view in database['views']:
                    content += self._ImplView(database, view)

        content += self._Footer()
        return content

    def _ImplConnect(self):
        template = '''
SQLessConn::SQLessConn():
    handle_(NULL),
$INIT_DATABASES {
}

SQLessConn::~SQLessConn() {
$DELETE_DATABASES
    close();
}

bool SQLessConn::connect(const std::string& path, const std::string& key /* = "" */) {
    if (sqlite3_open(path.c_str(), &handle_) != SQLITE_OK)
        return false;

#ifdef SQLITE_HAS_CODEC
    if (!key.empty())
        sqlite3_key(handle_, key.c_str(), key.length());
#endif

    return true;
}

bool SQLessConn::isValid() {
    return handle_ != NULL;
}

void SQLessConn::close() {
    if (handle_) {
        sqlite3_close(handle_);
        handle_ = NULL;
    }
}

void SQLessConn::beginTransaction() {
    sqlite3_exec(handle_, "$BEGIN_TRANS_SQL", NULL, NULL, NULL);
}

void SQLessConn::endTransaction() {
    sqlite3_exec(handle_, "$END_TRANS_SQL", NULL, NULL, NULL);
}

int SQLessConn::lastErrorCode() {
    return sqlite3_errcode(handle_);
}

std::string SQLessConn::lastErrorMsg() {
    return sqlite3_errmsg(handle_);
}

'''

        getter_template = '''
SQLessDB_$DATABASE *SQLessConn::database_$DATABASE() {
    if (!database_$DATABASE_)
        database_$DATABASE_ = new SQLessDB_$DATABASE(this);

    return database_$DATABASE_;
}
'''

        init_databases = ''
        delete_databases = ''
        has_databases = ''
        get_databases = ''
        for database in self.schema['databases']:
            name = database['name']
            #database_TaskList_(NULL)
            init_databases += config.kIdent + 'database_' + name + '_(NULL),\n'
            #if (database_db1_)
            #    delete database_db1_;
            delete_databases += config.kIdent + 'if (database_' + name + '_)\n' + \
                                config.kIdent2 + 'delete database_' + name + '_;\n'
            #bool SQLessConn::has_database_db1() {
            #   return true;
            #}
            has_databases += '\nbool SQLessConn::has_database_' + name + '() {\n' + \
                             config.kIdent + 'return true;\n}\n'

            get_databases += getter_template.replace('$DATABASE', name)

        template = template.replace('$INIT_DATABASES', init_databases.rstrip(',\n'))
        template = template.replace('$DELETE_DATABASES', delete_databases)
        template = template.replace('$BEGIN_TRANS_SQL', self.sqlgen.BeginTransitionSQL())
        template = template.replace('$END_TRANS_SQL', self.sqlgen.EndTransitionSQL())
        template += has_databases
        template += get_databases

        return template

    def _ImplDatabase(self, database):
        template = '''
// $DESCRIPTION
const char SQLessDB_$DB::kName[] = "$DB";


SQLessDB_$DB::SQLessDB_$DB(SQLessConn* conn)
    :conn_(conn),
$INIT_TABLES
$INIT_VIEWS {

    if (!exists())
        create();
}

SQLessDB_$DB::~SQLessDB_$DB() {
$DELETE_TABLES
$DELETE_VIEWS
}

bool SQLessDB_$DB::exists() {
    return true;
}

void SQLessDB_$DB::drop() {

}

bool SQLessDB_$DB::execQuery(const std::string& sql_stmt) {
    use();
    return sqlite3_exec(conn_->handle(), sql_stmt.c_str(), NULL, NULL, NULL) == SQLITE_OK;
}

bool SQLessDB_$DB::create() {
    return true;
}

bool SQLessDB_$DB::use() {
    return true;
}
'''
        template = template.replace('$DB', database['name'])
        template = template.replace('$DESCRIPTION', database['desc'])

        init_tables = ''
        delete_tables = ''
        table_has_and_getters = ''
        for table in database['tables']:
            #table_list_(NULL)
            init_tables += config.kIdent + 'table_' + table['name'] + '_(NULL),\n'
            #if (table_tb1_)
            #    delete table_tb1_;
            delete_tables += config.kIdent + 'if (table_' + table['name'] + '_)\n' + \
                             config.kIdent2 + 'delete table_' + table['name'] + '_;\n'
            table_has_and_getters += self._ImplHasTableView(database['name'], table['name'], False)

        init_views = ''
        delete_views = ''
        view_has_and_getters = ''
        if database.get('views'):
            for view in database['views']:
                init_views += config.kIdent + 'view_' + view['name'] + '_(NULL),\n'
                delete_views += config.kIdent + 'if (view_' + view['name'] + '_)\n' + \
                                config.kIdent2 + 'delete view_' + view['name'] + '_;\n'
                view_has_and_getters += self._ImplHasTableView(database['name'], view['name'], True)

        template = template.replace('$INIT_TABLES', init_tables)
        template = template.replace('$DELETE_TABLES', delete_tables)
        template = template.replace('$INIT_VIEWS', init_views.rstrip(',\n'))
        template = template.replace('$DELETE_VIEWS', delete_views)
        template += table_has_and_getters
        template += view_has_and_getters

        return template

    def _ImplHasTableView(self, database, name, is_view):
        _type = 'view' if is_view else 'table'
        _prefix = config.kViewPrefix if is_view else config.kTablePrefix
        _has_sql = self.sqlgen.HasViewSQL(name) if is_view else self.sqlgen.HasTableSQL(name)

        template = '''
bool SQLessDB_$DB::has_$TYPE_$NAME() {
    std::string sql = "$HAS_SQL";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(conn_->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return false;

    bool exists = false;
    if (sqlite3_step(stmt) == SQLITE_ROW)
        exists = true;

    sqlite3_finalize(stmt);
    return exists;
}

$PREFIX_$NAME* SQLessDB_$DB::$TYPE_$NAME() {
    if (!$TYPE_$NAME_)
        $TYPE_$NAME_ = new $PREFIX_$NAME(this);

    return $TYPE_$NAME_;
}
'''
        template = template.replace('$NAME', name)
        template = template.replace('$PREFIX_', _prefix)
        template = template.replace('$TYPE', _type)
        template = template.replace('$DB', database)
        template = template.replace('$HAS_SQL', _has_sql.replace('"', '\\"'))

        return template

    def _ImplTable(self, schema, database):
        template = '''
// $DESCRIPTION
const char SQLessTable_$TABLE::kName[] = "$TABLE";

SQLessTable_$TABLE::SQLessTable_$TABLE(SQLessDB_$DATABASE* db)
    :db_(db),
$INIT_COLUMNS {
    if (!exists())
        create();
}

SQLessTable_$TABLE::~SQLessTable_$TABLE() {
}

bool SQLessTable_$TABLE::exists() {
    return db_->has_table_$TABLE();
}

bool SQLessTable_$TABLE::create() {
    return db_->execQuery("$CREATE_TABLE_SQL");
}

bool SQLessTable_$TABLE::drop() {
    return db_->execQuery("$DROP_TABLE_SQL");
}

int SQLessTable_$TABLE::row_count(const std::string& condition) {
    std::string sql = "SELECT COUNT(*) FROM $TABLE";

    if (!condition.empty())
        sql += " WHERE " + condition;

    sql += ";";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(db_->connection()->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return -1;

    int count = -1;
    if (sqlite3_step(stmt) == SQLITE_ROW)
        count = sqlite3_column_int(stmt, 0);

    sqlite3_finalize(stmt);
    return count;
}
'''

        getter_template = '''
SQLessColumn_$TABLE_$COLUMN* SQLessTable_$TABLE::column_$COLUMN() {
    if (!column_$COLUMN_)
        column_$COLUMN_ = new SQLessColumn_$TABLE_$COLUMN(this);

    return column_$COLUMN_;
}'''

        init_columns = ''
        get_columns = ''
        for col in schema['columns']:
            init_columns += config.kIdent + 'column_' + col['name'] + '_(NULL),\n'
            get_columns += getter_template.replace('$TABLE', schema['name']).replace('$COLUMN', col['name'])

        template = template.replace('$INIT_COLUMNS', init_columns.rstrip(',\n'))

        template = template.replace('$TABLE', schema['name'])
        template = template.replace('$DESCRIPTION', schema['desc'])
        template = template.replace('$DATABASE', database)

        template = template.replace('$CREATE_TABLE_SQL', self.sqlgen.CreateTableSQL(schema, if_not_exists=True).replace('"', '\\"'))
        template = template.replace('$DROP_TABLE_SQL', self.sqlgen.DropTableSQL(schema['name']).replace('"', '\\"'))

        # Insert
        template += self._ImplInsertParam(schema)
        template += self._ImplTableInsert(schema)

        # Select
        template += self._ImplSelectParamAndResult(schema, False)
        template += self._ImplTableViewSelect(schema, False)
        template += self._ImplSelectResultGetRow(schema, False)

        # Update
        template += self._ImplUpdateParam(schema)
        template += self._ImplTableUpdate(schema)

        # Delete
        template += self._ImplTableRemoveAndClear(schema)

        # Column Getters
        template += get_columns

        for col in schema['columns']:
            template += self._ImplColumn(schema['name'], col)

        return template

    def _SQLTypeToCppDefaultValue(self, col_type):
        '''返回SQL的数据类型对应C++数据类型的默认初始化值'''
        if self.sqlgen.Name() != 'sqlite':
            print 'Unknown database :' + self.sqlgen.Name()
            exit(1)

        sql_type = self.sqlgen.MapDataType(col_type)
        if sql_type == 'INTEGER' or sql_type == 'BIGINT' or sql_type == 'REAL':
            return '0'

        return ''

    def _ImplInsertParam(self, schema):
        # 构造函数
        cdtor = '\nSQLessTable_' + schema['name'] + '::InsertParam::InsertParam():\n'
        col_setters = ''
        for col in schema['columns']:
            # 初始化整形/浮点型和布尔型成员的默认值
            defval = self._SQLTypeToCppDefaultValue(col['type'])
            if len(defval) > 0:
                cdtor += config.kIdent + col['name'] + '_(' + defval + '),\n'
            cdtor += config.kIdent + 'has_' + col['name'] + '_(false),\n'

            # 设置选中的列
            #InsertParam& SQLessTable_tb1::InsertParam::set_col1(int i) {
            #   col1_ = i;
            #   has_col1_ = true;
            #   return *this;
            #}
            col_setters += '\nSQLessTable_' + schema['name'] + '::InsertParam& ' + 'SQLessTable_' + schema['name'] + '::InsertParam::set_' + col['name'] + \
                           '(' + self.declare._SQLTypeToCPPType(col['type'], True) + ' i) {\n' + \
                           config.kIdent + col['name'] + '_ = i;\n' + \
                           config.kIdent + 'has_' + col['name'] + '_ = true;\n' + \
                           config.kIdent + 'return *this;\n}\n'

        cdtor = cdtor.rstrip(',\n') + ' {\n}\n'

        #析构函数
        cdtor += '\nSQLessTable_' + schema['name'] + '::InsertParam::~InsertParam() {\n}\n'

        cdtor += col_setters
        return cdtor

    def _BindValueForInsertAndUpdate(self, stype, field):
        rv = ''
        if stype == 'INTEGER':
            rv = 'sqlite3_bind_int(stmt, sqlite3_bind_parameter_index(stmt, "@' + field + '"), param.' + field + '_);'
        elif stype =='BIGINT':
            rv = 'sqlite3_bind_int64(stmt, sqlite3_bind_parameter_index(stmt, "@' + field + '"), param.' + field + '_);'
        elif stype == 'REAL':
            rv = 'sqlite3_bind_double(stmt, sqlite3_bind_parameter_index(stmt, "@' + field + '"), param.' + field + '_);'
        elif stype == 'TEXT' or stype == 'BLOB':
            rv = 'sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@' + field + '"), param.' + field + '_.c_str(), param.' + field + '_.length(), SQLITE_STATIC);'
        else:
            print 'Unknown SQL type: ' + stype
            exit(1)

        return rv


    def _ImplTableInsert(self, schema):
        template = '''
bool SQLessTable_$TABLE::insert(const InsertParam& param, int64_t* inserted_row_id) {
    std::string sql = "INSERT INTO $TABLE (";
    std::string fields;
$SELECT_FIELDS

    if (fields.empty())
        return false;

    sql += TrimRight(fields, " ,");
    sql += ") VALUES (";

    fields.clear();
$VALUE_FIELDS

    sql += TrimRight(fields, " ,");
    sql += ");";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(db_->connection()->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return false;

$BIND_FIELDS

    bool succ = sqlite3_step(stmt) == SQLITE_DONE;
    sqlite3_finalize(stmt);

    if (succ && inserted_row_id)
        *inserted_row_id = sqlite3_last_insert_rowid(db_->connection()->handle());

    return succ;
}
'''
        select_fields = ''
        value_fields = ''
        bind_fields = ''
        for col in schema['columns']:
            #if (param.has_col1_)
            #   fields += "col1, ";
            select_fields += config.kIdent + 'if (param.has_' + col['name'] + '_)\n' + \
                             config.kIdent2 + 'fields += "' + col['name'] + ', ";\n'

            #if (param.has_col1_)
            #    fields.append("@col1, ");
            value_fields += config.kIdent + 'if (param.has_' + col['name'] + '_)\n' + \
                            config.kIdent2 + 'fields += "@' + col['name'] + ', ";\n'

            #if (param.has_col2_)
            #    sqlite3_bind_double(stmt, sqlite3_bind_parameter_index(stmt, "@col2"), param.col2_);
            #if (param.has_col3_)
            #    sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@col3"), param.col3_.c_str(), param.col3_.length(), SQLITE_STATIC);
            bind_fields += config.kIdent + 'if (param.has_' + col['name'] + '_)\n'
            bind_fields += config.kIdent2 + self._BindValueForInsertAndUpdate(self.sqlgen.MapDataType(col['type']), col['name']) + '\n'

        template = template.replace('$TABLE', schema['name'])
        template = template.replace('$SELECT_FIELDS', select_fields)
        template = template.replace('$VALUE_FIELDS', value_fields)
        template = template.replace('$BIND_FIELDS', bind_fields)

        return template

    def _ImplSelectParamAndResult(self, schema, is_view):
        prefix = config.kViewPrefix if is_view else config.kTablePrefix
        table_view_name = prefix + schema['name']
        ret = ''

        # SelectParam 构造函数
        select_ctor = """
$TABLE_VIEW_NAME::SelectParam::SelectParam():
    desc_(false),
    limit_(0),
    offset_(0),
"""

        for col in schema['columns']:
            select_ctor += config.kIdent + col['name'] + '_(false),\n'

        select_ctor = select_ctor.rstrip(',\n') + ' {\n}\n'
        select_ctor = select_ctor.replace('$TABLE_VIEW_NAME', table_view_name)
        ret += select_ctor

        # SelectParam 析构函数
        ret += '\n' + table_view_name + '::SelectParam::~SelectParam() {\n}\n'

        # 选择所有列
        select_all_template = '''
$TABLE_VIEW_NAME::SelectParam& $TABLE_VIEW_NAME::SelectParam::add_all() {
$ADD_COLUMNS
    return *this;
}
'''
        order_by_template = '''
$TABLE_VIEW_NAME::SelectParam& $TABLE_VIEW_NAME::SelectParam::order_by_$COLUMN(bool desc) {
    order_by_ = "$COLUMN";
    desc_ = desc;
    return *this;
}'''

        add_columns = ''
        order_by_columns = ''
        for col in schema['columns']:
            add_columns += config.kIdent + col['name'] + '_ = true;\n'
            order_by_columns += order_by_template.replace('$TABLE_VIEW_NAME', table_view_name).replace('$COLUMN', col['name']) + '\n'

        ret += select_all_template.replace('$TABLE_VIEW_NAME', table_view_name).replace('$ADD_COLUMNS', add_columns)
        ret += order_by_columns

        # SelectResult 构造函数
        ret += '\n' + table_view_name + '::SelectResult::SelectResult():\n'
        for col in schema['columns']:
            # 初始化整形/浮点型和布尔型成员的默认值
            defval = self._SQLTypeToCppDefaultValue(col['type'])
            if len(defval) > 0:
                ret += config.kIdent + col['name'] + '_(' + defval + '),\n'
        ret += config.kIdent + 'stmt_(NULL) {\n}\n'

        # SelectResult 析构函数
        ret += '\n' + table_view_name + '::SelectResult::~SelectResult() {\n' + \
                config.kIdent + 'if (stmt_)\n' + \
                config.kIdent2 + 'sqlite3_finalize(stmt_);\n}\n'

        return ret

    def _ImplTableViewSelect(self, schema, is_view):
        prefix = config.kViewPrefix if is_view else config.kTablePrefix
        table_view_name = prefix + schema['name']

        template = '''
bool $TABLE_VIEW_NAME::select(const SelectParam& param, SelectResult* result) {
    std::string sql = "SELECT ";
    std::string fields;
$SELECT_FIELDS

    if (fields.empty())
        return false;

    sql += TrimRight(fields, " ,");
    sql += " FROM $NAME";

    if (!param.condition_.empty()) {
        sql += " WHERE ";
        sql += param.condition_;
    }
    if (param.limit_ > 0) {
        sql += " LIMIT ";
        sql += NumberToString(param.limit_);
    }
    if (param.offset_ > 0) {
        sql += " OFFSET ";
        sql += NumberToString(param.offset_);
    }

    sql += ";";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(db_->connection()->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return false;

    result->param_ = param;
    result->stmt_ = stmt;

    return true;
}
'''
        select_fields = ''
        for col in schema['columns']:
            #if (param.has_col1_)
            #   fields += "col1, ";
            select_fields += config.kIdent + 'if (param.' + col['name'] + '_)\n' + \
                             config.kIdent2 + 'fields += "' + col['name'] + ', ";\n'

        template = template.replace('$NAME', schema['name'])
        template = template.replace('$TABLE_VIEW_NAME', table_view_name)
        template = template.replace('$SELECT_FIELDS', select_fields)

        return template


    def _ImplSelectResultGetRow(self, schema, is_view):
        prefix = config.kViewPrefix if is_view else config.kTablePrefix
        table_view_name = prefix + schema['name']

        template = '''
bool $TABLE_VIEW_NAME::SelectResult::getRow() {
    if (!stmt_)
        return false;

    if (sqlite3_step(stmt_) != SQLITE_ROW) {
        sqlite3_finalize(stmt_);
        stmt_ = NULL;
        return false;
    }

    int _columns = sqlite3_column_count(stmt_);

$REMEMBER_COLUMNS

    for (int i = 0; i < _columns; i++) {
        $ASSIGN_COLUMNS
    }

    return true;
}
'''
        def AssignColumnValue(stype, colname):
            rv = ''
            if stype == 'INTEGER':
                rv = colname + '_ = sqlite3_column_int(stmt_, i);'
            elif stype == 'BIGINT':
                rv = colname + '_ = sqlite3_column_int64(stmt_, i);'
            elif stype == 'REAL':
                rv = colname + '_ = sqlite3_column_double(stmt_, i);'
            elif stype == 'TEXT' or stype == 'BLOB':
                rv = colname + '_.assign((const char*)sqlite3_column_text(stmt_, i), sqlite3_column_bytes(stmt_, i));'
            else:
                print 'Unkown SQL type: ' + stype
                exit(1)

            return rv

        remember_columns = ''
        assign_columns = ''
        _first = True
        for col in schema['columns']:
            # bool col1 = param_.col1_;
            remember_columns += config.kIdent + 'bool ' + col['name'] + ' = param_.' + col['name'] + '_;\n'
            assign_columns += ('if' if _first else 'else if') + ' (' + col['name'] + ') {\n' + \
                              config.kIdent3 + AssignColumnValue(self.sqlgen.MapDataType(col['type']), col['name']) + '\n' + \
                              config.kIdent3 + col['name'] + ' = false;\n' +  config.kIdent2 + '} '
            _first = False

        template = template.replace('$TABLE_VIEW_NAME', table_view_name)
        template = template.replace('$REMEMBER_COLUMNS', remember_columns)
        template = template.replace('$ASSIGN_COLUMNS', assign_columns)

        return template

    def _ImplUpdateParam(self, schema):
        up = self._ImplInsertParam(schema)
        up = up.replace('InsertParam', 'UpdateParam')
        return up

    def _ImplTableUpdate(self, schema):
        template = '''
bool SQLessTable_$TABLE::update(const UpdateParam& param, int* affected_rows /* = NULL */) {
    std::string sql = "UPDATE $TABLE SET ";
    std::string fields;
$SELECT_COLUMNS

    if (fields.empty())
        return false;

    sql += TrimRight(fields, ", ");

    if (!param.condition_.empty())
        sql.append(" WHERE ").append(param.condition_);

    sql.append(";");

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(db_->connection()->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return false;

$BIND_COLUMNS

    bool succ = sqlite3_step(stmt) == SQLITE_DONE;

    sqlite3_finalize(stmt);

    if (succ && affected_rows)
        *affected_rows = sqlite3_changes(db_->connection()->handle());

    return succ;
}
'''
        select_columns = ''
        bind_columns = ''
        for col in schema['columns']:
            #if (param.has_col1_)
            #    fields.append("col1=@col1, ");
            select_columns += config.kIdent + 'if (param.has_' + col['name'] + '_)\n' + \
                            config.kIdent2 + 'fields += "' + col['name'] + '=@' + col['name'] + ', ";\n'

            # 和insert操作相同的代码
            #if (param.has_col2_)
            #    sqlite3_bind_double(stmt, sqlite3_bind_parameter_index(stmt, "@col2"), param.col2_);
            #if (param.has_col3_)
            #    sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@col3"), param.col3_.c_str(), param.col3_.length(), SQLITE_STATIC);
            bind_columns += config.kIdent + 'if (param.has_' + col['name'] + '_)\n'
            bind_columns += config.kIdent2 + self._BindValueForInsertAndUpdate(self.sqlgen.MapDataType(col['type']), col['name']) + '\n'

        template = template.replace('$TABLE', schema['name'])
        template = template.replace('$SELECT_COLUMNS', select_columns)
        template = template.replace('$BIND_COLUMNS', bind_columns)

        return template


    def _ImplTableRemoveAndClear(self, schema):
        template = '''
bool SQLessTable_$TABLE::remove(const std::string& condition, int* affected_rows /* = NULL */) {
    std::string sql = "DELETE FROM $TABLE ";

    if (!condition.empty()) {
        sql += " WHERE ";
        sql += condition;
    }

    sql += ";";

    bool succ = db_->execQuery(sql);
    if (succ && affected_rows)
        *affected_rows = sqlite3_changes(db_->connection()->handle());

    return succ;
}

bool SQLessTable_$TABLE::clear(int* affected_rows /* = NULL */) {
    return remove("", affected_rows);
}
'''
        template = template.replace('$TABLE', schema['name'])
        return template


    def _ImplView(self, db_schema, schema):
        template = '''
// $DESCRIPTION
const char SQLessView_$VIEW::kName[] = "$VIEW";

SQLessView_$VIEW::SQLessView_$VIEW(SQLessDB_$DATABASE* db)
    :db_(db) {
}

SQLessView_$VIEW::~SQLessView_$VIEW() {
}

bool SQLessView_$VIEW::exists() {
    return db_->has_view_$VIEW();
}

bool SQLessView_$VIEW::create(const std::string& condition) {
    std::string sql = "$CREATE_VIEW_SQL";

    if (!condition.empty()) {
        TrimRight(sql, ";");
        sql += " WHERE " + condition + ";";
    }

    return db_->execQuery(sql);
}

bool SQLessView_$VIEW::drop() {
    return db_->execQuery("$DROP_VIEW_SQL");
}

int SQLessView_$VIEW::row_count(const std::string& condition) {
    std::string sql = "SELECT COUNT(*) FROM $VIEW";

    if (!condition.empty())
        sql += " WHERE " + condition;

    sql += ";";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(db_->connection()->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return -1;

    int count = -1;
    if (sqlite3_step(stmt) == SQLITE_ROW)
        count = sqlite3_column_int(stmt, 0);

    sqlite3_finalize(stmt);
    return count;
}
'''
        template = template.replace('$VIEW', schema['name'])
        template = template.replace('$DESCRIPTION', schema['desc'])
        template = template.replace('$DATABASE', db_schema['name'])
        template = template.replace('$CREATE_VIEW_SQL', self.sqlgen.CreateViewSQL(schema))
        template = template.replace('$DROP_VIEW_SQL', self.sqlgen.DropViewSQL(schema['name']))

        mock_schema = self.declare.MockViewAsTableSchema(db_schema, schema)

        template += self._ImplSelectParamAndResult(mock_schema, True)
        template += self._ImplTableViewSelect(mock_schema, True)
        template += self._ImplSelectResultGetRow(mock_schema, True)

        return template


    def _ImplColumn(self, table, schema):
        template = '''
// $DESCRIPTION
const char SQLessColumn_$TABLE_$COLUMN::kName[] = "$COLUMN";
const char SQLessColumn_$TABLE_$COLUMN::kType[] = "$TYPE";
$DEFAULT_VALUE

SQLessColumn_$TABLE_$COLUMN::SQLessColumn_$TABLE_$COLUMN(SQLessTable_$TABLE* table):
    table_(table) {
    if (!exists())
        create();
}

SQLessColumn_$TABLE_$COLUMN::~SQLessColumn_$TABLE_$COLUMN() {
}

bool SQLessColumn_$TABLE_$COLUMN::exists() {
    return table_->database()->execQuery("$HAS_COLUMN_SQL");
}

bool SQLessColumn_$TABLE_$COLUMN::create() {
    return table_->database()->execQuery("$ADD_COLUMN_SQL");
}
'''
        default_value = ''
        if 'default' in schema and self.sqlgen.MapDataType(schema['type']) == 'TEXT':
            default_value = 'const char ' + config.kColumnPrefix + table + '_' + schema['name'] + '::kDefault[] = "' + schema['default'] + '";\n'

        template = template.replace('$DESCRIPTION', schema['desc'])
        template = template.replace('$COLUMN', schema['name'])
        template = template.replace('$TYPE', schema['type'])
        template = template.replace('$TABLE', table)
        template = template.replace('$DEFAULT_VALUE', default_value)

        template = template.replace('$HAS_COLUMN_SQL', self.sqlgen.HasColumnSQL(table, schema['name']))
        template = template.replace('$ADD_COLUMN_SQL', self.sqlgen.AddColumnSQL(table, schema))

        return template


    def _Header(self):
        template = """
// Generated by SQLess v$VERSION at $DATETIME

#include "$SAVENAME.h"

#include <sstream>

namespace {

std::string &TrimRight(std::string &s, const std::string &m) {
    size_t pe = s.length() - 1;
    while (pe < s.length() && m.find(s.at(pe)) != m.npos)
        pe--;

    if (pe >= s.length())
        return s.erase(0, s.length());

    return s.erase(pe + 1, s.length() - 1 - pe);
}

std::string NumberToString(int64_t n) {
    return static_cast<std::ostringstream*>( &(std::ostringstream() << n) )->str();
}

}
"""
        template = template.replace('$VERSION', config.version)
        template = template.replace('$DATETIME', time.strftime('%Y-%m-%d %X', time.localtime()))
        template = template.replace('$SAVENAME', os.path.basename(self.savename))

        # 命名空间
        if self.namespace:
            template += '\nnamespace ' + self.namespace + ' {\n'

        return template


    def _Footer(self):
        f= '\n'

        if self.namespace:
            f += '} // namespace ' + self.namespace + '\n'

        return f
