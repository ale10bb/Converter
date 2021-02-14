# -*- coding: UTF-8 -*-
import os
import sys
import argparse
from time import sleep

from Converter.macros import _LOGGER
import Converter.walk
import Converter.csv
import Converter.sqlite

def main():
    # 目前本地数据库文件必须位于可执行文件的同目录下
    db_file_path = os.path.join(os.path.dirname(sys.argv[0]), 'vulns.sqlite3')
    # argparse：传入path
    parser = argparse.ArgumentParser(prog='Nessus', description='读取Nessus的CSV文件，将描述文字翻译成中文，转换结果分别保存至每个原始文件的同目录下。')
    parser.add_argument('path', nargs='+', help='file path or dir path')
    args = parser.parse_args()

    _LOGGER.info('[Nessus] Started.')
    # 本地数据库无效时，使用服务器版本强制覆盖
    if not Converter.sqlite.isvalid_Nessus(db_file_path):
        _LOGGER.warning('[Nessus] Invalid local DB. Downloading...')
        Converter.sqlite.update_Nessus(db_file_path)
    # 过滤csv并去重
    _LOGGER.debug('[Nessus] arg_paths = "{}".'.format(args.path))
    target_paths = set()
    for arg_path in args.path:
        target_paths = target_paths.union(set(Converter.walk.file(arg_path, ['.csv'])))
    _LOGGER.debug('[Nessus] target_paths = "{}".'.format(target_paths))

    # 调用Converter.csv处理
    count = 0
    for target_path in target_paths:
        try:
            rows = Converter.csv.read_Nessus(target_path, db_file_path)
            Converter.csv.write(rows, os.path.splitext(target_path)[0] + '_converted.csv')
            count += 1
        except Exception as err:
            _LOGGER.warning('[Nessus] Conversion failure due to "{}"'.format(err))

    _LOGGER.info('[Nessus] Finished with {} converted.'.format(count))

if __name__ == '__main__':
    main()
    sleep(2)

