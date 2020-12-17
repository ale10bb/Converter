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

def main():
    # argparse：只需传入path，无其他开关
    parser = argparse.ArgumentParser(prog='Nessus', description='读取Nessus的CSV文件，将描述文字翻译成中文，转换结果分别保存至每个原始文件的同目录下。')
    parser.add_argument('path', nargs='+', help='file path or dir path')
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
            rows = Converter.csv.read_Nessus(target_path)
            with open(os.path.splitext(target_path)[0] + '_converted.csv', 'w', encoding='utf-8-sig') as dst_file:
                writer = csv.DictWriter(dst_file, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
                writer.writeheader()
                writer.writerows(rows)
            count += 1
        except Exception as err:
            _LOGGER.warning('[Nessus] Conversion failure due to "{}"'.format(err))

    _LOGGER.info('[Nessus] Finished with {} converted.'.format(count))

def update():
    _LOGGER.info('[Nessus] Updating started.')
    try:
        info_pack = requests.get('https://nt.chenqlz.top/api/info').json()
        _LOGGER.info('[Nessus] Downloading version: {} ({} vulns).'.format(datetime.datetime.fromtimestamp(int(info_pack['data']['built'])).strftime('%Y-%m-%d'), info_pack['data']['count']))
        db_path = os.path.join(os.path.dirname(sys.argv[0]), 'vulns.sqlite3')
        with open(db_path, 'wb') as db_file:
            db_file.write(requests.get('https://nt.chenqlz.top/static/vulns.sqlite3').content)
        _LOGGER.info('[Nessus] Updating finished.')
    except:
        _LOGGER.error('[Nessus] Updating failed.')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        update()
    else:
        main()
    sleep(2)

