// SQLess数据库操作单元测试C++版
// 扫描 data/china_101_famous_places/ 目录下的所有图片，将其ID、路径、类型、大小、MD5、文件内容等存入数据库中，
// 然后再从数据库中读取出来，通过再次计算读取出的文件内容的MD5，并和文件实际的MD5比较来判断是否成功。

// g++ pictures.cc pictures.sqless.cc utils/src/ccutil.cpp utils/src/cutil.c utils/gnu-md5.c -D_DEBUG -lsqlite3

#include "pictures.sqless.h"
#include "utils/gnu-md5.h"
#include "utils/src/ccutil.h"

using namespace unittest;
using namespace utils;

// 数据库连接全局变量
static SQLessConn g_conn;

// 图片ID
static int g_id = 0;

int write_database();
int check_database();

int main(int arc, char* argv[]) {
    cutil_init();

    // 查找所有的文件并写入数据库
    if (!write_database())
        return 1;

    if (!check_database())
        return 1;

    return 0;
}

// 计算MD5值
// 如果path非空，则从文件读取
// 如果cotent非空，直接计算内存缓冲区
// 失败返回空字符串
std::string compute_md5(const std::string& path, const std::string& content) {
    std::string c;
    if (!path.empty()) {
        if(!ReadFile(path, &c))
            return "";
    } else
        c = content;

    unsigned char md5buf[17], md5[33];
    md5_buffer(c.data(), c.size(), md5buf);
    md5_string(md5buf, md5);

    return (const char*)md5;
}

// 处理找到的每个文件
int picture_file_handler(const char* path, void* arg) {
    ASSERT(g_conn.isValid());

    int64_t size = file_size(path);
    ASSERT(size > 0);

    std::string content;
    VERIFY(ReadFile(path, &content));
    ASSERT(content.size() == (size_t)size);

    std::string md5 = compute_md5("", content);
    printf("%s: %" PRId64" : %s", path, size, md5.c_str());

    SQLessTable_tb::InsertParam param;
    param.set_id(++g_id).
        set_path(path).
        set_md5(md5).
        set_data(content).
        set_type(path_find_extension(path)).
        set_size(size);

    int64_t id;
    if (!g_conn.database_db()->table_tb()->insert(param, &id)) {
        printf(" Insert failed! %s \n", g_conn.lastErrorMsg().c_str());
        return 0;
    }

    VERIFY(g_id == id);

    printf(": %" PRId64 "\n", id);

    return 1;
}

int write_database() {
    if (!g_conn.connect("pictures.db")) {
        printf("open database failed!\n");
        return 0;
    }

    // 丢弃、创建表
    SQLessTable_tb* table = g_conn.database_db()->table_tb();
    if (!table->drop()) {
        printf("table exists but drop failed\n");
        return 0;
    }

    if (!table->create()) {
        printf("create table failed!\n");
        return 0;
    }

    // 常量测试
    if (strcmp(SQLessDB_db::kName, "db") ||
        strcmp(SQLessTable_tb::kName, "tb") ||
        strcmp(SQLessColumn_tb_path::kName, "path") ||
        strcmp(SQLessColumn_tb_path::kType, "text"))
        printf("Check exported constants failed!\n");

    // 字段属性
    VERIFY(table->column_id()->is_primary_key());
    VERIFY(table->column_path()->is_not_null());

    TimeMeter t;

    // 开始事务
    g_conn.beginTransaction();

    // 查找所有图片并记录到数据库
    VERIFY(foreach_file("data/china_101_famous_places", picture_file_handler, 0, 0, NULL));

    // 结束事务
    g_conn.endTransaction();

    // 打印耗时
    printf("Cost time: %.3lf seconds.\n\n", t.ElapseSTillNow());

    // 关闭数据库连接
    g_conn.close();
    return 1;
}

int check_database() {
    if (!g_conn.connect("pictures.db")) {
        printf("open database failed!\n");
        return 0;
    }

    SQLessTable_tb* table = g_conn.database_db()->table_tb();
    if (!table->exists()) {
        printf("table not exists!\n");
        return 0;
    }

    SQLessTable_tb::SelectParam select;
    SQLessTable_tb::SelectResult r;
    if (!table->select(select.add_all(), &r)) {
        printf("select from table failed! %s \n", g_conn.lastErrorMsg().c_str());
        return 0;
    }

    int id;
    int64_t size;
    std::string path, type, md5, content;
    while (r.getRow()) {
        id = r.id();
        size = r.size();
        path = r.path();
        type = r.type();
        md5 = r.md5();
        content = r.data();

        std::string md5_file = compute_md5(path, "");
        std::string md5_db = compute_md5("", content);
        bool matched = md5_file == md5_db && md5_file == md5;

        printf("%d: %s: %" PRId64" : %s -> %s \n",
            id, path.c_str(), size, md5.c_str(),
            matched ? "Match!" : "Failed!");
    }

    g_conn.close();
    return 1;
}
