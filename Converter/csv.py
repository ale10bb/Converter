# -*- coding: UTF-8 -*-
import csv

from .macros import _LOGGER
from . import sqlite

def read_Nessus(src_file_path:str, db_file_path:str) -> list:
    ''' 尝试以Nessus模式读取{src_file_path}，并返回翻译后的CSV行列表。

    Args:
        src_file_path(str): 读取文件的路径
        db_file_path(str): 本地数据库文件的路径

    Returns:
        list: CSV行列表
    '''
    _LOGGER.info('[Converter/csv/read_Nessus] Reading "{}".'.format(src_file_path))
    ret = []
    # 微软默认使用UTF-8-BOM的格式读写CSV
    with open(src_file_path, encoding='utf-8-sig') as src_file:
        rows = csv.DictReader(src_file, quoting=csv.QUOTE_ALL)
        count = 1
        for row in rows:
            try:
                # 对于没有Plugin ID列，或Plugin ID不为数字的异常情况，直接跳过该行
                plugin_id = int(row['Plugin ID'])
                # 对于get_zhcn_pack的任意失败情况，直接跳过翻译并使用原始数据
                zhcn_pack = sqlite.get_Nessus_zhcn_pack(plugin_id, db_file_path)
                row['Name'] = zhcn_pack['script_name']
                row['Synopsis'] = zhcn_pack['synopsis']
                row['Description'] = zhcn_pack['description']
                row['Solution'] = zhcn_pack['solution']
            except Exception as err:
                _LOGGER.warning('[Converter/csv/read_Nessus] Skipping line {} due to "{}".'.format(count, err))
            finally:
                count += 1
            ret.append(row)
    _LOGGER.info('[Converter/csv/read_Nessus] lines = {}.'.format(count))
    return ret
