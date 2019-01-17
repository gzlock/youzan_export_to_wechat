import os
import sqlite3
import sys
import threading

from peewee import SqliteDatabase
from playhouse.signals import *

from model.config import Config
from services.AESCoder import AESCoder

# 打开内存数据库
__db__ = SqliteDatabase(':memory:')

# 将数据库 传递 给 数据模型
Config.Init(__db__)

Data_Path = os.path.expanduser('~')

# Windows
if sys.platform == 'win32':
    Data_Path = os.path.expandvars('%LOCALAPPDATA%') + '\\wechat_product_editor\\'
# macOS
elif sys.platform == 'darwin':
    Data_Path += '/Library/Containers/com.lumu.wechat_product_editor/'
# Linux
else:
    Data_Path = '/var/lib/wechat_product_editor/'

isExists = os.path.exists(Data_Path)
if not isExists:
    os.mkdir(Data_Path)

SQL_Path = Data_Path + 'encrypt_store'

AESCoder('CmKEzRQKD3UxmRGD')

if os.path.exists(SQL_Path) and os.path.isfile(SQL_Path):
    # print('初始化内存数据库')
    try:
        f = open(SQL_Path, 'rb')
        text = AESCoder.decrypt(f.read())
        f.close()
        # print('解密内容', text)
        db = __db__.connection()
        db.cursor().executescript(text)
        db.commit()
        db.row_factory = sqlite3.Row
    except Exception as e:
        # print('初始化内存数据库错误, 创建数据库表', e)
        __db__.create_tables([Config])
else:
    # print('创建数据库表')
    __db__.create_tables([Config])

# 延时保存
timer: threading.Timer = None


# 保存数据库为二进制文件
def save_db_to_binary_file(text: str):
    print('保存内存数据库到文件', text)
    data = AESCoder.encrypt(text)
    f = open(SQL_Path, 'wb')
    f.write(data)
    f.close()


# 数据库信号
def post_save_handler(sender, instance, created):
    global timer
    if timer:
        timer.cancel()
    text = ''
    for line in __db__.connection().iterdump():
        text += '%s\n' % line
    timer = threading.Timer(1, save_db_to_binary_file, [text])
    timer.start()


# 连接数据库信号
post_save.connect(post_save_handler, sender=Config)


class LocalStore:

    @staticmethod
    def Set(key: str, value):
        print('set', key, value)
        Config.Set(key=key, value=value)

    @staticmethod
    def Get(key: str, default=None):
        return Config.Get(key=key, default=default)

    @staticmethod
    def Delete(key: str):
        Config.delete().where(Config.key == key).execute()
