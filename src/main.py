#!/usr/bin/python
#coding: utf-8

import simplejson as json

import cplusplus
import sqlite
import pyutil


if __name__ == '__main__':
    # TODO：解析命令行参数来获取数据库IDL文件、目标语言、数据库引擎、命名空间等
    schema = json.loads(pyutil.ReadFile('../db_schema.json'))
    cpp = cplusplus.CPlusPlus(schema, sqlite.Sqlite(), 'ns')
    print cpp.Generate()
