#!/usr/bin/python
#coding: utf-8

import json
import os
import sys

import config
import cplusplus
import sqlite
import pyutil

def Usage():
    usage = """SQLess v$VERSION
An object-oriented database operating code generator

--outdir='' : Where to store the generated code file[s]
--cpp : Generate CPlusPlus code [Default]
--sqlite : Using sqlite as backend database

-h, --help : Show this help message and exit
-v, --version: Show version info and exit
"""
    print(usage.replace('$VERSION', config.version))


def ParseOptions():
    opt = {
        'database': 'sqlite',
        'target' : 'cpp'
    }

    for p in sys.argv[1:]:
        if p.startswith('--outdir'):
            print(p)
            opt['outdir'] = p[9:]
        elif p == '--cpp':
            opt['target'] = 'cpp'
        elif p == '--sqlite':
            opt['database'] = 'sqlite'
        elif p == '-h' or p == '--help':
            Usage()
            exit(0)
        elif p == '-v' or p == '--version':
            print('SQLess v' + config.version)
            exit(0)
        elif not p.startswith('-'):
            opt['schema_file'] = p
        else:
            Usage()
            exit(1)

    return opt


if __name__ == '__main__':
    opt = ParseOptions()

    if not opt.get('schema_file'):
        print ('No schema file specified!')
        exit(1)

    schema = json.loads(pyutil.ReadFile(opt['schema_file']))
    if not schema.get('databases'):
        print ('schema file does not has a "databases" key!')
        exit(1)

    if not opt.get('outdir'):
        opt['outdir'] = os.path.dirname(opt['schema_file'])

    outname = os.path.basename(opt['schema_file']).split('.')[0]
    outfile = os.path.join(opt['outdir'], outname) + config.kTargetFileSuffix

    if opt.get('database') == 'sqlite':
        database_engine = sqlite.Sqlite()
    else:
        print ('Unsupport database: ' + opt['database'])
        exit(1)

    if opt.get('target') == 'cpp':
        engine = cplusplus.CPlusPlus(schema, database_engine, outfile)
    else:
        print ('Unknown target language: ' + opt['target'])
        exit(1)

    engine.Generate()
