## What is SQLess

SQLess is an code generator that enables coding with relational database in an object-oriented way. Just define an database schema (a JSON format file), the generator will generate all the code you need.

For the generated code, every connection, database, table and even column is represented by a distinct object, and you can use this object to do CRUD operations and more.

SQLess is not a database wrapper like [sqlapi](http://www.sqlapi.com/), which still needs you to write SQL statement and do parameter binding.etc.

SQLess is also not an Object-Relational Mapping (ORM) system like [ODB](http://www.codesynthesis.com/products/odb/), which tightly binds to the language used and have obscure usage.

If you have ever used [Protobuf](https://code.google.com/p/protobuf/), you will find them quiet similer. In fact, SQLess is inspired from Protobuf.

## Compare

### Ordinary method drawbacks

* Difficult and time consuming. Writing database conversion code for any non-trivial application requires extensive knowledge of the specific database system and its APIs.
* Easy to make mistake. It is easy to misspell column names or pass incompatible values in SQL queries. It is also easy to construct a SQL statement that has syntax error, even worse if using printf series function. Forgetting escaping special charactar is another common thing.
* The above errors can only be detected at runtime, resulting in a long debug circle.
* Database vendor lock-in. The conversion code is written for a specific database which makes it hard to switch to another database vendor.
* Complicates the application. The database conversion code often ends up interspersed throughout the application making it hard to debug, change, and maintain.

### What if using SQLess?

* Ease of use. The interface for a language is the same and you don't need to known the used database deeply. The interface is also very simple.
* Concise code. With SQLess generated codes hiding the details of the underlying database, the application logic is written using the natural object vocabulary instead of tables, columns and SQL. The resulting code is simpler and thus easier to read and understand.
* High-efficiency. If your editor support auto-completiton, you can write code unbeliable faster!
* Database portability. Because the database conversion code is automatically generated, it is easy to switch from one database vendor to another.
* Safety. You use C++ identifiers instead of strings to refer to object members and the generated code makes sure database and C++ types are compatible. All this helps catch programming errors at compile-time rather than at runtime.

## Support

Because the database schema is defined in a language unrelated style, SQLess can support any object-oriented language in theory. The backend database is also not restricted. But due to my restricted time and energy...

Currently only C++ language and [SQLite](http://www.sqlite.org/) database is supported, but MySQL database support is coming soon.

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

| name | type | optional | description |
|------|------|----------|-------------|
| namespace | string | optional | put the generated code in a namespace (C++ only)  |
| databases | list | mandatory | describes all used databases, each element is a map that describes the database. |

Supported keys in database map:

| name | type | optional | description |
|------|------|----------|-------------|
|name | string | mandatory | the name of the database |
|desc | string | mandatory | the description of the database |
|tables | list | mandatory | the tables inside the database, each element is a map that describes the view. |
|views | list | mandatory | the views inside the database, each element is a map that describes the view. |

Supported keys in table map:

| name | type | optional | description |
|------|------|----------|-------------|
| name | string | mandatory | the name of the table |
| desc | string | mandatory | the description of the table |
| type | string | optional  | the type of the table. e.g. fts3 for sqlite, InnoDB or MyISAM for MySQL. |
| columns | list| mandatory | the columns of the table, each element is a map that describes that column. |

Supported keys in table-column map:

| name | type | optional | description |
|------|------|----------|-------------|
| name | string | mandatory | the name of the column |
| desc | string | mandatory | the description of the column |
| type | string | mandatory | one of "INT", "BIGINT", "REAL", "TEXT" or "BLOB", case insensitive. |
| default | * | optional | default value of this column. Used in the create table statement. |
| index | bool | optional | create index on this column, default to false. |
| primary_key | bool | optional | treat this column as primary key, default to false. |
| auto_increment | bool | optional | whether the column value is auto increment, default to false. |
| not_null | bool | optional | whether the column value must be specified when insert, default to false. |

Supported keys in view map:

| name | type | optional | description |
|------|------|----------|-------------|
| name | string | mandatory | the name of the view |
| desc | string | mandatory | the description of the view |
| columns | list | mandatory | the columns of the view, each element is a map that describes that column. |

Supported keys in view-column map:

| name | type | optional | description |
|------|------|----------|-------------|
| table | string | mandatory | the original table name where this column come from, the table must exists in the same database scope. |
| column | string | mandatory | the original column name in the origin table, the column must exists. |
| name | string | optional | the alias name for the origin table column, default to TABLE_COLUMN is not specified. |

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

