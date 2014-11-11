## What is SQLess

SQLess is an code generator that enables coding with relational database in an object-oriented way. Just define an database schema (a JSON format file), the generator will generate all the code you need.

For the generated code, every connection, database, table and even column is represented by a distinct object, and you can use this object to do CRUD operations and more.

Currently only C++ language and [SQLite](http://www.sqlite.org/) database is supported, but MySQL database support will come soon.

## Features & Advantages

SQLess is not a database wrapper like [sqlapi](http://www.sqlapi.com/), which still needs you to write SQL statment and do parameter binding.etc. SQLess is also not an Object-Relational Mapping (ORM) system like [ODB](http://www.codesynthesis.com/products/odb/), which tightly binds to the language used and have obscure usage. If you have ever used [Protobuf](https://code.google.com/p/protobuf/), you will find them quiet similer. In fact, SQLess is inspired from Protobuf.

// TODO: translate to en
一般方式
困难并且耗时。需深入要了解所使用的数据库，需要写大量冗余的数据库操作代码（如参数绑定）。
容易出错。构造SQL容易发生语法错误，使用printf类似的函数更容易出问题；容易写错表名、列名；SQL语句中列的值与列的类型不匹配；忘记转义字符串中的特殊字符等等，这些问题只有在运行时才能表现出来。
不能方便地切换数据库。因为所写的代码都是数据库相关的。
大量的数据库操作代码会增加程序的复杂性，使代码调试困难，难以维护。

使用SQLess
无需深入了解所用数据库的API，支持多种数据库，并可方便切换。
使代码更加简洁。通过隐藏数据库操作的细节，使用少量简单的代码就可以完成原本需要大量复杂代码才能完成的数据库操作。
编写更加高效。只需使用最简单的语法。因为表、列等已成为标识符，配合编辑器自动补全功能可使编写效率成倍提高，并减少拼写错误。
更加健壮，尽可能将运行时的SQL执行错误提前到编译时。
结果是代码的可读性和可维护性更好。

相对于其他数据库封装或ORM：
支持多种面向对象的语言，不针对特定语言
生成的代码可立即编译和链接，不依赖其他文件，不需要链接库文件。
无需阅读冗长的说明文档，不需要学习因此引入的新“语言”。

## How to use

* Step1: Write a database schema like [Pictures.json](https://github.com/arifeng/SQLess/blob/master/tests/pictures.json)
* Step2: Generating code: src/sqless.py SCHEMA_FILE_PATH. The generated filename is something like schema.sqless.h, schema.sqless.cc
* Step3: Use the generating file in your project directly, no other dependence required.

> SQLess is written with python 2.7.x, python 3.x is not tested.

## Schema file format

Firstly, take a look at [Pictures.json](https://github.com/arifeng/SQLess/blob/master/tests/pictures.json), that is more explicable than the details below.

The generated C++ code using sqlite is something like [Pictures.sqless.h](https://github.com/arifeng/SQLess/blob/master/tests/pictures.sqless.h) and [Pictures.sqless.cc](https://github.com/arifeng/SQLess/blob/master/tests/pictures.sqless.cc)

### Details:

Supported keys in outest map:

* namespace: [string, optional] put the generated code in a namespace (C++ only)
* databases: [list, mandatory] describes all used databases, each element is a map that describes the database.

Supported keys in database map:

* name: [string, mandatory] the name of the database
* desc: [string, mandatory] the description of the database
* tables: [list, mandatory] the tables inside the database, each element is a map that describes the view.
* views: [list, mandatory] the views inside the database, each element is a map that describes the view.

Supported keys in table map:

* name: [string, mandatory] the name of the table
* desc: [string, mandatory] the description of the table
* type: [string, optional] the type of the table. e.g. fts3 for sqlite, InnoDB or MyISAM for MySQL.
* columns: [list, mandatory] the columns of the table, each element is a map that describes that column.

Supported keys in table-column map:

* name: [string, mandatory] the name of the column
* desc: [string, mandatory] the description of the column
* type: [string, mandatory] one of "INT", "BIGINT", "REAL", "TEXT" or "BLOB", case insensitive.
* index: [bool, optional] create index on this column, default to false.
* primary_key: [bool, optional] treat this column as primary key, default to false.
* auto_increment: [bool, optional] whether the column value is auto increment, default to false.
* not_null: [bool, optional] whether the column value must be specified when insert, default to false.

Supported keys in view map:

* name: [string, mandatory] the name of the view
* desc: [string, mandatory] the description of the view
* columns: [list, mandatory] the columns of the view, each element is a map that describes that column.

Supported keys in view-column map:

* table: [string, mandatory] the original table name where this column come from, the table must exists in the same database scope.
* column: [string, mandatory] the original column name in the origin table, the column must exists.
* name: [string, optional] the alias name for the origin table column, default to TABLE_COLUMN is not specified.

### Coding exmaple using C++

Open an database connection:

    SQLessConn conn;
    if (!conn.connect("pictures.db")) {
        //handle failure
    }

Insert into a table:

    SQLessTable_tb::InsertParam param;
    param.set_id(id).
        set_path(path).
        set_md5(md5).
        set_data(content).
        set_type(path).
        set_size(size);

    int64_t id;
    if (!conn.database_db()->table_tb()->insert(param, &id)) {
        //handle failure
    }

Select from a table:

    SQLessTable_tb::SelectParam select;
    SQLessTable_tb::SelectResult r;

    if (!conn.database_db()->table_tb()->select(select.add_all(), &r)) {
        //handle failure
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

        //...
    }

Delete from table:

    int affected_rows;
    conn.database_db()->table_tb()->remove("where id=1", &affected_rows);

