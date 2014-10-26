﻿
// Generated by SQLess v0.3.1 at 2014-10-26 14:41:47

#include "pictures.sqless.h"

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

namespace unittest {

SQLessConn::SQLessConn():
    handle_(NULL),
    database_db_(NULL) {
}

SQLessConn::~SQLessConn() {
    if (database_db_)
        delete database_db_;

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

void SQLessConn::beginTransition() {
    sqlite3_exec(handle_, "BEGIN;", NULL, NULL, NULL);
}

void SQLessConn::endTransition() {
    sqlite3_exec(handle_, "COMMIT;", NULL, NULL, NULL);
}

int SQLessConn::lastErrorCode() {
    return sqlite3_errcode(handle_);
}

std::string SQLessConn::lastErrorMsg() {
    return sqlite3_errmsg(handle_);
}


bool SQLessConn::has_database_db() {
    return true;
}

SQLessDB_db *SQLessConn::database_db() {
    if (!database_db_)
        database_db_ = new SQLessDB_db(this);

    return database_db_;
}

// The database where all pictures info are stored.
const char SQLessDB_db::kName[] = "db";


SQLessDB_db::SQLessDB_db(SQLessConn* conn)
    :conn_(conn),
    table_tb_(NULL) {

    if (!exists())
        create();
}

SQLessDB_db::~SQLessDB_db() {
    if (table_tb_)
        delete table_tb_;

}

bool SQLessDB_db::exists() {
    return true;
}

void SQLessDB_db::drop() {

}

bool SQLessDB_db::execQuery(const std::string& sql_stmt) {
    use();
    return sqlite3_exec(conn_->handle(), sql_stmt.c_str(), NULL, NULL, NULL) == SQLITE_OK;
}

bool SQLessDB_db::create() {
    return true;
}

bool SQLessDB_db::use() {
    return true;
}

bool SQLessDB_db::has_table_tb() {
    std::string sql = "SELECT name FROM sqlite_master WHERE type = \"table\" AND name = \"tb\";";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(conn_->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return false;

    bool exists = false;
    if (sqlite3_step(stmt) == SQLITE_ROW)
        exists = true;

    sqlite3_finalize(stmt);
    return exists;
}

SQLessTable_tb* SQLessDB_db::table_tb() {
    if (!table_tb_)
        table_tb_ = new SQLessTable_tb(this);

    return table_tb_;
}

// The table where all pictures info are stored.
const char SQLessTable_tb::kName[] = "tb";

SQLessTable_tb::SQLessTable_tb(SQLessDB_db* db)
    :db_(db),
    column_id_(NULL),
    column_path_(NULL),
    column_type_(NULL),
    column_size_(NULL),
    column_md5_(NULL),
    column_data_(NULL) {
    if (!exists())
        create();
}

SQLessTable_tb::~SQLessTable_tb() {
}

bool SQLessTable_tb::exists() {
    return db_->has_table_tb();
}

bool SQLessTable_tb::create() {
    return db_->execQuery("CREATE TABLE IF NOT EXISTS tb (id INTEGER PRIMARY_KEY AUTO_INCREMENT NOT NULL, path TEXT NOT NULL, type TEXT DEFAULT 'unknown', size BIGINT DEFAULT 0, md5 TEXT, data BLOB); ");
}

bool SQLessTable_tb::drop() {
    return db_->execQuery("DROP TABLE IF EXISTS \"tb\";");
}

int SQLessTable_tb::row_count(const std::string& condition) {
    std::string sql = "SELECT COUNT(*) FROM tb";

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

SQLessTable_tb::InsertParam::InsertParam():
    id_(0),
    has_id_(false),
    has_path_(false),
    has_type_(false),
    size_(0),
    has_size_(false),
    has_md5_(false),
    has_data_(false) {
}

SQLessTable_tb::InsertParam::~InsertParam() {
}

SQLessTable_tb::InsertParam& SQLessTable_tb::InsertParam::set_id(int i) {
    id_ = i;
    has_id_ = true;
    return *this;
}

SQLessTable_tb::InsertParam& SQLessTable_tb::InsertParam::set_path(const std::string& i) {
    path_ = i;
    has_path_ = true;
    return *this;
}

SQLessTable_tb::InsertParam& SQLessTable_tb::InsertParam::set_type(const std::string& i) {
    type_ = i;
    has_type_ = true;
    return *this;
}

SQLessTable_tb::InsertParam& SQLessTable_tb::InsertParam::set_size(int64_t i) {
    size_ = i;
    has_size_ = true;
    return *this;
}

SQLessTable_tb::InsertParam& SQLessTable_tb::InsertParam::set_md5(const std::string& i) {
    md5_ = i;
    has_md5_ = true;
    return *this;
}

SQLessTable_tb::InsertParam& SQLessTable_tb::InsertParam::set_data(const std::string& i) {
    data_ = i;
    has_data_ = true;
    return *this;
}

bool SQLessTable_tb::insert(const InsertParam& param, int64_t* inserted_row_id) {
    std::string sql = "INSERT INTO tb (";
    std::string fields;
    if (param.has_id_)
        fields += "id, ";
    if (param.has_path_)
        fields += "path, ";
    if (param.has_type_)
        fields += "type, ";
    if (param.has_size_)
        fields += "size, ";
    if (param.has_md5_)
        fields += "md5, ";
    if (param.has_data_)
        fields += "data, ";


    if (fields.empty())
        return false;

    sql += TrimRight(fields, " ,");
    sql += ") VALUES (";

    fields.clear();
    if (param.has_id_)
        fields += "@id, ";
    if (param.has_path_)
        fields += "@path, ";
    if (param.has_type_)
        fields += "@type, ";
    if (param.has_size_)
        fields += "@size, ";
    if (param.has_md5_)
        fields += "@md5, ";
    if (param.has_data_)
        fields += "@data, ";


    sql += TrimRight(fields, " ,");
    sql += ");";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(db_->connection()->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return false;

    if (param.has_id_)
        sqlite3_bind_int(stmt, sqlite3_bind_parameter_index(stmt, "@id"), param.id_);
    if (param.has_path_)
        sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@path"), param.path_.c_str(), param.path_.length(), SQLITE_STATIC);
    if (param.has_type_)
        sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@type"), param.type_.c_str(), param.type_.length(), SQLITE_STATIC);
    if (param.has_size_)
        sqlite3_bind_int64(stmt, sqlite3_bind_parameter_index(stmt, "@size"), param.size_);
    if (param.has_md5_)
        sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@md5"), param.md5_.c_str(), param.md5_.length(), SQLITE_STATIC);
    if (param.has_data_)
        sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@data"), param.data_.c_str(), param.data_.length(), SQLITE_STATIC);


    bool succ = sqlite3_step(stmt) == SQLITE_DONE;
    sqlite3_finalize(stmt);

    if (succ && inserted_row_id)
        *inserted_row_id = sqlite3_last_insert_rowid(db_->connection()->handle());

    return succ;
}

SQLessTable_tb::SelectParam::SelectParam():
    id_(false),
    path_(false),
    type_(false),
    size_(false),
    md5_(false),
    data_(false),
    desc_(false) {
}

SQLessTable_tb::SelectParam::~SelectParam() {
}

SQLessTable_tb::SelectParam& SQLessTable_tb::SelectParam::add_all() {
    id_ = true;
    path_ = true;
    type_ = true;
    size_ = true;
    md5_ = true;
    data_ = true;

    return *this;
}

SQLessTable_tb::SelectParam& SQLessTable_tb::SelectParam::order_by_id(bool desc) {
    order_by_ = "id";
    desc_ = desc;
    return *this;
}

SQLessTable_tb::SelectParam& SQLessTable_tb::SelectParam::order_by_path(bool desc) {
    order_by_ = "path";
    desc_ = desc;
    return *this;
}

SQLessTable_tb::SelectParam& SQLessTable_tb::SelectParam::order_by_type(bool desc) {
    order_by_ = "type";
    desc_ = desc;
    return *this;
}

SQLessTable_tb::SelectParam& SQLessTable_tb::SelectParam::order_by_size(bool desc) {
    order_by_ = "size";
    desc_ = desc;
    return *this;
}

SQLessTable_tb::SelectParam& SQLessTable_tb::SelectParam::order_by_md5(bool desc) {
    order_by_ = "md5";
    desc_ = desc;
    return *this;
}

SQLessTable_tb::SelectParam& SQLessTable_tb::SelectParam::order_by_data(bool desc) {
    order_by_ = "data";
    desc_ = desc;
    return *this;
}

SQLessTable_tb::SelectResult::SelectResult():
    id_(0),
    size_(0),
    stmt_(NULL) {
}

SQLessTable_tb::SelectResult::~SelectResult() {
}

bool SQLessTable_tb::select(const SelectParam& param, SelectResult* result) {
    std::string sql = "SELECT ";
    std::string fields;
    if (param.id_)
        fields += "id, ";
    if (param.path_)
        fields += "path, ";
    if (param.type_)
        fields += "type, ";
    if (param.size_)
        fields += "size, ";
    if (param.md5_)
        fields += "md5, ";
    if (param.data_)
        fields += "data, ";


    if (fields.empty())
        return false;

    sql += TrimRight(fields, " ,");
    sql += " FROM tb";

    if (!param.condition_.empty()) {
        sql += " WHERE ";
        sql += param.condition_;
    }

    sql += ";";

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(db_->connection()->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return false;

    result->param_ = param;
    result->stmt_ = stmt;

    return true;
}

bool SQLessTable_tb::SelectResult::getRow() {
    if (!stmt_)
        return false;

    if (sqlite3_step(stmt_) != SQLITE_ROW) {
        sqlite3_finalize(stmt_);
        stmt_ = NULL;
        return false;
    }

    int _columns = sqlite3_column_count(stmt_);

    bool id = param_.id_;
    bool path = param_.path_;
    bool type = param_.type_;
    bool size = param_.size_;
    bool md5 = param_.md5_;
    bool data = param_.data_;


    for (int i = 0; i < _columns; i++) {
        if (id) {
            id_ = sqlite3_column_int(stmt_, i);
            id = false;
        } else if (path) {
            path_.assign((const char*)sqlite3_column_text(stmt_, i), sqlite3_column_bytes(stmt_, i));
            path = false;
        } else if (type) {
            type_.assign((const char*)sqlite3_column_text(stmt_, i), sqlite3_column_bytes(stmt_, i));
            type = false;
        } else if (size) {
            size_ = sqlite3_column_int64(stmt_, i);
            size = false;
        } else if (md5) {
            md5_.assign((const char*)sqlite3_column_text(stmt_, i), sqlite3_column_bytes(stmt_, i));
            md5 = false;
        } else if (data) {
            data_.assign((const char*)sqlite3_column_text(stmt_, i), sqlite3_column_bytes(stmt_, i));
            data = false;
        } 
    }

    return true;
}

SQLessTable_tb::UpdateParam::UpdateParam():
    id_(0),
    has_id_(false),
    has_path_(false),
    has_type_(false),
    size_(0),
    has_size_(false),
    has_md5_(false),
    has_data_(false) {
}

SQLessTable_tb::UpdateParam::~UpdateParam() {
}

SQLessTable_tb::UpdateParam& SQLessTable_tb::UpdateParam::set_id(int i) {
    id_ = i;
    has_id_ = true;
    return *this;
}

SQLessTable_tb::UpdateParam& SQLessTable_tb::UpdateParam::set_path(const std::string& i) {
    path_ = i;
    has_path_ = true;
    return *this;
}

SQLessTable_tb::UpdateParam& SQLessTable_tb::UpdateParam::set_type(const std::string& i) {
    type_ = i;
    has_type_ = true;
    return *this;
}

SQLessTable_tb::UpdateParam& SQLessTable_tb::UpdateParam::set_size(int64_t i) {
    size_ = i;
    has_size_ = true;
    return *this;
}

SQLessTable_tb::UpdateParam& SQLessTable_tb::UpdateParam::set_md5(const std::string& i) {
    md5_ = i;
    has_md5_ = true;
    return *this;
}

SQLessTable_tb::UpdateParam& SQLessTable_tb::UpdateParam::set_data(const std::string& i) {
    data_ = i;
    has_data_ = true;
    return *this;
}

bool SQLessTable_tb::update(const UpdateParam& param, int* affected_rows /* = NULL */) {
    std::string sql = "UPDATE tb SET ";
    std::string fields;
    if (param.has_id_)
        fields += "id=@id, ";
    if (param.has_path_)
        fields += "path=@path, ";
    if (param.has_type_)
        fields += "type=@type, ";
    if (param.has_size_)
        fields += "size=@size, ";
    if (param.has_md5_)
        fields += "md5=@md5, ";
    if (param.has_data_)
        fields += "data=@data, ";


    if (fields.empty())
        return false;

    sql += TrimRight(fields, ", ");

    if (!param.condition_.empty())
        sql.append(" WHERE ").append(param.condition_);

    sql.append(";");

    sqlite3_stmt* stmt = NULL;
    if (sqlite3_prepare_v2(db_->connection()->handle(), sql.c_str(), -1, &stmt, 0) != SQLITE_OK)
        return false;

    if (param.has_id_)
        sqlite3_bind_int(stmt, sqlite3_bind_parameter_index(stmt, "@id"), param.id_);
    if (param.has_path_)
        sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@path"), param.path_.c_str(), param.path_.length(), SQLITE_STATIC);
    if (param.has_type_)
        sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@type"), param.type_.c_str(), param.type_.length(), SQLITE_STATIC);
    if (param.has_size_)
        sqlite3_bind_int64(stmt, sqlite3_bind_parameter_index(stmt, "@size"), param.size_);
    if (param.has_md5_)
        sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@md5"), param.md5_.c_str(), param.md5_.length(), SQLITE_STATIC);
    if (param.has_data_)
        sqlite3_bind_text(stmt, sqlite3_bind_parameter_index(stmt, "@data"), param.data_.c_str(), param.data_.length(), SQLITE_STATIC);


    bool succ = sqlite3_step(stmt) == SQLITE_DONE;

    sqlite3_finalize(stmt);

    if (succ && affected_rows)
        *affected_rows = sqlite3_changes(db_->connection()->handle());

    return succ;
}

bool SQLessTable_tb::remove(const std::string& condition, int* affected_rows /* = NULL */) {
    std::string sql = "DELETE FROM tb ";

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

bool SQLessTable_tb::clear(int* affected_rows /* = NULL */) {
    return remove("", affected_rows);
}

SQLessColumn_tb_id* SQLessTable_tb::column_id() {
    if (!column_id_)
        column_id_ = new SQLessColumn_tb_id(this);

    return column_id_;
}
SQLessColumn_tb_path* SQLessTable_tb::column_path() {
    if (!column_path_)
        column_path_ = new SQLessColumn_tb_path(this);

    return column_path_;
}
SQLessColumn_tb_type* SQLessTable_tb::column_type() {
    if (!column_type_)
        column_type_ = new SQLessColumn_tb_type(this);

    return column_type_;
}
SQLessColumn_tb_size* SQLessTable_tb::column_size() {
    if (!column_size_)
        column_size_ = new SQLessColumn_tb_size(this);

    return column_size_;
}
SQLessColumn_tb_md5* SQLessTable_tb::column_md5() {
    if (!column_md5_)
        column_md5_ = new SQLessColumn_tb_md5(this);

    return column_md5_;
}
SQLessColumn_tb_data* SQLessTable_tb::column_data() {
    if (!column_data_)
        column_data_ = new SQLessColumn_tb_data(this);

    return column_data_;
}
// The Unique ID of the picture
const char SQLessColumn_tb_id::kName[] = "id";
const char SQLessColumn_tb_id::kType[] = "int";


SQLessColumn_tb_id::SQLessColumn_tb_id(SQLessTable_tb* table):
    table_(table) {
    if (!exists())
        create();
}

SQLessColumn_tb_id::~SQLessColumn_tb_id() {
}

bool SQLessColumn_tb_id::exists() {
    return table_->database()->execQuery("SELECT id FROM tb LIMIT 0;");
}

bool SQLessColumn_tb_id::create() {
    return table_->database()->execQuery("ALTER TABLE tb ADD id INTEGER PRIMARY_KEY AUTO_INCREMENT NOT NULL;");
}

// the path of the picture
const char SQLessColumn_tb_path::kName[] = "path";
const char SQLessColumn_tb_path::kType[] = "text";


SQLessColumn_tb_path::SQLessColumn_tb_path(SQLessTable_tb* table):
    table_(table) {
    if (!exists())
        create();
}

SQLessColumn_tb_path::~SQLessColumn_tb_path() {
}

bool SQLessColumn_tb_path::exists() {
    return table_->database()->execQuery("SELECT path FROM tb LIMIT 0;");
}

bool SQLessColumn_tb_path::create() {
    return table_->database()->execQuery("ALTER TABLE tb ADD path TEXT NOT NULL;");
}

// The image type, e.g. jpg, png, gif...
const char SQLessColumn_tb_type::kName[] = "type";
const char SQLessColumn_tb_type::kType[] = "text";
const char SQLessColumn_tb_type::kDefault[] = "unknown";


SQLessColumn_tb_type::SQLessColumn_tb_type(SQLessTable_tb* table):
    table_(table) {
    if (!exists())
        create();
}

SQLessColumn_tb_type::~SQLessColumn_tb_type() {
}

bool SQLessColumn_tb_type::exists() {
    return table_->database()->execQuery("SELECT type FROM tb LIMIT 0;");
}

bool SQLessColumn_tb_type::create() {
    return table_->database()->execQuery("ALTER TABLE tb ADD type TEXT DEFAULT 'unknown';");
}

// The size of the picture file
const char SQLessColumn_tb_size::kName[] = "size";
const char SQLessColumn_tb_size::kType[] = "bigint";


SQLessColumn_tb_size::SQLessColumn_tb_size(SQLessTable_tb* table):
    table_(table) {
    if (!exists())
        create();
}

SQLessColumn_tb_size::~SQLessColumn_tb_size() {
}

bool SQLessColumn_tb_size::exists() {
    return table_->database()->execQuery("SELECT size FROM tb LIMIT 0;");
}

bool SQLessColumn_tb_size::create() {
    return table_->database()->execQuery("ALTER TABLE tb ADD size BIGINT DEFAULT 0;");
}

// The MD5 checksum of the picture
const char SQLessColumn_tb_md5::kName[] = "md5";
const char SQLessColumn_tb_md5::kType[] = "text";


SQLessColumn_tb_md5::SQLessColumn_tb_md5(SQLessTable_tb* table):
    table_(table) {
    if (!exists())
        create();
}

SQLessColumn_tb_md5::~SQLessColumn_tb_md5() {
}

bool SQLessColumn_tb_md5::exists() {
    return table_->database()->execQuery("SELECT md5 FROM tb LIMIT 0;");
}

bool SQLessColumn_tb_md5::create() {
    return table_->database()->execQuery("ALTER TABLE tb ADD md5 TEXT;");
}

// The image file data
const char SQLessColumn_tb_data::kName[] = "data";
const char SQLessColumn_tb_data::kType[] = "blob";


SQLessColumn_tb_data::SQLessColumn_tb_data(SQLessTable_tb* table):
    table_(table) {
    if (!exists())
        create();
}

SQLessColumn_tb_data::~SQLessColumn_tb_data() {
}

bool SQLessColumn_tb_data::exists() {
    return table_->database()->execQuery("SELECT data FROM tb LIMIT 0;");
}

bool SQLessColumn_tb_data::create() {
    return table_->database()->execQuery("ALTER TABLE tb ADD data BLOB;");
}

} // namespace unittest
