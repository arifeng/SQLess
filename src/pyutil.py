#coding: utf-8

import os
import sys
import hashlib
import logging
import shutil
import zipfile


def GetModulePath():
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


def ReadableSize(num):
    """可读性强的文件大小"""
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def ReadableFileSize(path):
    try:
        size = os.path.getsize(path)
        return ReadableSize(size)
    except OSError:
        return ' '

def ReadFile(path, charset='UTF-8', binary=False):
    '''读取文件内容，返回字符串'''
    try:
        if binary:
            f = open(path, 'rb')
        else:
            f = open(path, 'r', encoding=charset)
        content = f.read()
        f.close()
        return content
    except IOError:
        return ''

def GetFileMd5(filename):
    if not os.path.isfile(filename):
        return ""
    myhash = hashlib.md5()
    f = open(filename,'rb')
    while True:
        b = f.read(4096*4)
        if not b :
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest().upper()

def UnderScoreToCamcelCase(var):
    ''' 将foo_bar类型风格的名称更改为FooBar'''
    camel = ''
    for part in var.split('_'):
        camel += part.capitalize()

    return camel

def WriteFile(path, content, binary=False):
    '''将字符串作为文件内容写入文件'''
    if binary:
        f = open(path, 'wb')
    else:
        f = open(path, 'w')
    f.write(content)
    f.close()

def copytree(src, dst, symlinks=False, ignore=None):
    '''将src目录递归地拷贝到dst目录下'''
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def InitLog():
    '''初始化日志'''
    # logging level: DEBUG<INFO<WARNING<ERROR<CRITICAL(FATAL)

    logfile = 'packing.log'
    if os.path.exists(logfile):
      os.remove(logfile)

    #dirname = os.path.dirname(logfile)
    # if not os.path.exists(dirname):
    #    os.mkdir(dirname)

    logger = logging.getLogger(logfile)
    logger.setLevel(logging.DEBUG)

    info_hd = logging.FileHandler(logfile)
    info_hd.setLevel(logging.INFO)

    debug_hd = logging.StreamHandler()
    debug_hd.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    debug_hd.setFormatter(formatter)
    info_hd.setFormatter(formatter)

    logger.addHandler(info_hd)
    logger.addHandler(debug_hd)

    return logger

def UnderScoreToCamcelCase(var):
    ''' 将foo_bar类型风格的名称更改为FooBar'''
    camel = ''
    for part in var.split('_'):
        camel += part.capitalize()

    return camel

def ZipFolder(dirname, zipfilename):
    filelist = []
    if os.path.isfile(dirname):
        filelist.append(dirname)
    else:
        for root, dirs, files in os.walk(dirname):
            for name in files:
                filelist.append(os.path.join(root, name))

    zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED)
    for tar in filelist:
        arcname = tar[len(dirname):]
        # print arcname
        zf.write(tar, arcname)
    zf.close()


def UnzipFile(zipfilename, unziptodir):
    if not os.path.exists(unziptodir):
        os.mkdir(unziptodir)
    zfobj = zipfile.ZipFile(zipfilename)
    for name in zfobj.namelist():
        name = name.replace('\\', '/')

        if name.endswith('/'):
            dir_name = os.path.join(unziptodir, name)
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)
        else:
            ext_filename = os.path.join(unziptodir, name)
            ext_dir = os.path.dirname(ext_filename)
            if not os.path.exists(ext_dir):
                os.mkdir(ext_dir)
            outfile = open(ext_filename, 'wb')
            outfile.write(zfobj.read(name))
            outfile.close()

#os.chdir(GetModulePath())
#logger = InitLog()
