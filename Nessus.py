# -*- coding: UTF-8 -*-
import os
import sys
import argparse
import datetime
from time import sleep
import csv
import requests

from Converter.macros import _LOGGER
import Converter.walk
import Converter.csv
import Converter.update

class _UpdateAction(argparse.Action):

    def __init__(self,
                 option_strings,
                 default,
                 dest=None,
                 nargs=0,
                 help=None):
        super(_UpdateAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=nargs,
            help=help)
        self.db_file_path = default

    def __call__(self, parser, namespace, values, option_string=None):
        db_file_path = self.db_file_path
        Converter.update.Nessus_db(db_file_path)
        parser.exit()

def main():
    # 目前本地数据库文件必须位于可执行文件的同目录下
    db_file_path = os.path.join(os.path.dirname(sys.argv[0]), 'vulns.sqlite3')
    # argparse：传入path
    parser = argparse.ArgumentParser(prog='Nessus', description='读取Nessus的CSV文件，将描述文字翻译成中文，转换结果分别保存至每个原始文件的同目录下。')
    parser.add_argument('path', nargs='+', help='file path or dir path')
    # 传入update，控制升级数据库
    parser.add_argument(
        '-u',
        '--update', 
        action=_UpdateAction,
        default=db_file_path,
        help='update local DB and exit'
    )
    args = parser.parse_args()

    _LOGGER.info('[Nessus] Started.')
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
            with open(os.path.splitext(target_path)[0] + '_converted.csv', 'w', encoding='utf-8-sig') as dst_file:
                writer = csv.DictWriter(dst_file, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
                writer.writeheader()
                writer.writerows(rows)
            count += 1
        except Exception as err:
            _LOGGER.warning('[Nessus] Conversion failure due to "{}"'.format(err))

    _LOGGER.info('[Nessus] Finished with {} converted.'.format(count))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.argv.append('--update')
    main()
    sleep(2)

