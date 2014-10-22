#coding: utf-8
# 生成C++ 目标代码实现文件(.cpp)

import config

class CPlusPlusImpl:
    def __init__(self, schema, sqlgen, savename):
        self.sqlgen = sqlgen
        self.schema = schema
        self.savename = savename
        self.namespace = schema['namespace']

    def GenerateImplFile(self):
        content = self._Header()
        content += self._ImplConnect()

        for database in self.schema['databases']:
            content += self._ImplDatabase(database)
            for table in database['tables']:
                content += self._ImplTable(table, database['name'])

        content += self._Footer()
        return content

    def _ImplConnect(self):
        template = '''
SqlessConn::SqlessConn() {
}

SqlessConn::~SqlessConn() {
$DELETE_DATABASES
    close();
}

bool SqlessConn::connect(const std::string& path, const std::string& key /* = "" */) {
    if (sqlite3_open(path.c_str(), &handle_) != SQLITE_OK)
        return false;

    return true;
}

bool SqlessConn::isValid() {
    return handle_ != NULL;
}

void SqlessConn::beginTransition() {
    sqlite3_exec(handle_, "$BEGIN_TRANS_SQL", NULL, NULL, NULL);
}

void SqlessConn::endTransition() {
    sqlite3_exec(handle_, "$END_TRANS_SQL", NULL, NULL, NULL);
}

void SqlessConn::close() {
    sqlite3_close(handle_);
}
'''

        getter_template = '''
SqlessDB_$DATABASE *SqlessConn::database_$DATABASE() {
    if (!database_$DATABASE_)
        database_$DATABASE_ = new SqlessDB_$DATABASE(this);

    return database_$DATABASE_;
}
'''

        delete_databases = ''
        has_databases = ''
        get_databases = ''
        for database in self.schema['databases']:
            name = database['name']
            #if (database_db1_)
            #    delete database_db1_;
            delete_databases += config.kIdent + 'if (database_' + name + '_)\n' + \
                                config.kIdent2 + 'delete database_' + name + '_;\n'
            #bool SqlessConn::has_database_db1() {
            #   return true;
            #}
            has_databases += '\nbool SqlessConn::has_database_' + name + '() {\n' + \
                             config.kIdent + 'return true;\n}\n'

            get_databases += getter_template.replace('$DATABASE', name)

        template = template.replace('$DELETE_DATABASES', delete_databases)
        template = template.replace('$BEGIN_TRANS_SQL', self.sqlgen.BeginTransitionSQL())
        template = template.replace('$END_TRANS_SQL', self.sqlgen.EndTransitionSQL())
        template += has_databases
        template += get_databases

        return template

    def _ImplDatabase(self, database):
        template = '''
const char SqlessDB_$DB::kName[] = "$DB";
const char SqlessDB_$DB::kDescription[] = "$DESC";

SqlessDB_$DB::SqlessDB_$DB(SqlessConn* conn)
    :conn_(conn) {

    if (!exists())
        create();
}

SqlessDB_$DB::~SqlessDB_$DB() {
$DELETE_TABLES
}

bool SqlessDB_$DB::exists() {
    return true;
}

void SqlessDB_$DB::drop() {

}

bool SqlessDB_$DB::execQuery(const std::string& sql_stmt) {
    use();
    return sqlite3_exec(conn_->handle(), sql_stmt.c_str(), NULL, NULL, NULL) == SQLITE_OK;
}

bool SqlessDB_$DB::create() {
    return true;
}

bool SqlessDB_$DB::use() {
    return true;
}
'''
        template = template.replace('$DB', database['name'])
        template = template.replace('$DESC', database['desc'])

        delete_tables = ''
        table_has_and_getters = ''
        for table in database['tables']:
            #if (table_tb1_)
            #    delete table_tb1_;
            delete_tables += config.kIdent + 'if (table_' + table['name'] + '_)\n' + \
                             config.kIdent2 + 'delete table_' + table['name'] + '_;\n'
            table_has_and_getters += self._ImplHasTable(database['name'], table['name'])

        template = template.replace('$DELETE_TABLES', delete_tables)
        template += table_has_and_getters

        return template

    def _ImplHasTable(self, database, table):
        template = '''
bool SqlessDB_$DB::has_table_$TABLE() {
    std::string sql = "$HAS_TABLE_SQL";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(conn_->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK) {
        const char* s = sqlite3_errmsg(conn_->handle());
        return false;
    }

    bool exists = false;
    if (sqlite3_step(stmt) == SQLITE_ROW)
        exists = true;

    sqlite3_finalize(stmt);
    return exists;
}

SqlessTable_$TABLE* SqlessDB_$DB::table_$TABLE() {
    if (!table_$TABLE_)
        table_$TABLE_ = new SqlessTable_$TABLE(this);

    return table_$TABLE_;
}
'''
        template = template.replace('$DB', database)
        template = template.replace('$TABLE', table)
        template = template.replace('$HAS_TABLE_SQL', self.sqlgen.HasTableSQL(table).replace('"', '\\"'))

        return template

    def _ImplTable(self, schema, database):
        template = '''
const char SqlessTable_$TABLE::kName[] = "$TABLE";
const char SqlessTable_$TABLE::kDescription[] = "$DESC";

SqlessTable_$TABLE::SqlessTable_$TABLE(SqlessDB_$DATABASE* db)
    :db_(db) {
    if (!exists())
        create();
}

SqlessTable_$TABLE::~SqlessTable_$TABLE() {
}

bool SqlessTable_$TABLE::exists() {
    return db_->has_table_$TABLE();
}

bool SqlessTable_$TABLE::create() {
    return db_->execQuery("$CREATE_TABLE_SQL");
}

bool SqlessTable_$TABLE::drop() {
    return db_->execQuery("$DROP_TABLE_SQL");
}

int SqlessTable_$TABLE::row_count() {
    //TODO: 计算表行数
    return 0;
}
'''
        template = template.replace('$TABLE', schema['name'])
        template = template.replace('$DESC', schema['desc'])
        template = template.replace('$DATABASE', database)
        template = template.replace('$CREATE_TABLE_SQL', self.sqlgen.CreateTableSQL(schema).replace('"', '\\"'))
        template = template.replace('$DROP_TABLE_SQL', self.sqlgen.DropTableSQL(schema['name']).replace('"', '\\"'))

        return template


    def _Header(self):
        template = """
// Generated by SQLess v$VERSION

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

}
"""
        template = template.replace('$VERSION', config.version)
        template = template.replace('$SAVENAME', self.savename + config.kTargetFileSuffix)

        # 命名空间
        if self.namespace:
            template += '\nnamespace ' + self.namespace + ' {\n'

        return template


    def _Footer(self):
        f= '\n'

        if self.namespace:
            f += '} // namespace ' + self.namespace + '\n'

        return f
