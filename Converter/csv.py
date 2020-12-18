# -*- coding: UTF-8 -*-
import csv
import sqlite3
import requests

from Converter.macros import _LOGGER

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
        for row in rows:
            try:
                # 对于没有Plugin ID列，或Plugin ID不为数字的异常情况，直接跳过该行
                plugin_id = int(row['Plugin ID'])
                # 对于get_zhcn_pack的任意失败情况，直接跳过翻译并使用原始数据
                zhcn_pack = get_zhcn_pack(plugin_id, db_file_path)
                row['Name'] = zhcn_pack['script_name']
                row['Synopsis'] = zhcn_pack['synopsis']
                row['Description'] = zhcn_pack['description']
                row['Solution'] = zhcn_pack['solution']
            except Exception as err:
                _LOGGER.warning('[Converter/csv/read_Nessus] Skipping {} due to "{}".'.format(plugin_id, err))
            ret.append(row)
    return ret

def get_zhcn_pack(plugin_id:int, db_file_path:str) -> dict:
    ''' 尝试读取读取{plugin_id}的中文信息，缓存未命中时向服务器请求结果。

    Args:
        plugin_id(int): 插件ID
        db_file_path(str): 本地数据库文件的路径

    Returns:
        dict: {'pluginid': xxx, 'script_name': xxx, 'synopsis': xxx, 'description': xxx, 'solution': xxx}

    Raises:
        ValueError: 如果服务器请求失败
    '''
    ret = {'pluginid': plugin_id}
    
    conn = sqlite3.connect(db_file_path, isolation_level=None)
    # 首先从本地sqlite缓存读取
    row = conn.execute("SELECT * FROM zhcn WHERE `pluginid` = ?", (plugin_id,)).fetchone()
    if row:
        _LOGGER.debug('[Converter/csv/get_zhcn_pack] Local hit: {}.'.format(plugin_id))
        ret['script_name'] = row[1]
        ret['synopsis'] = row[2]
        ret['description'] = row[3]
        ret['solution'] = row[4]
    else:
        # 本地缓存未命中时，向NTS请求缓存
        remote_search = requests.get('https://nt.chenqlz.top/api/search?id={}'.format(plugin_id)).json()
        if remote_search['result'] == 0:
            # NTS缓存命中时，将结果存放至本地缓存
            _LOGGER.debug('[Converter/csv/get_zhcn_pack] Remote hit: {}.'.format(plugin_id))
            ret = remote_search['data']
            conn.execute("INSERT INTO zhcn VALUES (?, ?, ?, ?, ?)", (plugin_id, ret['script_name'], ret['synopsis'], ret['description'], ret['solution']))
            conn.execute("UPDATE config SET value = value + 1 WHERE `key` = 'count'")
        elif remote_search['result'] == 2:
            # NTS缓存未命中时，向NTS发起翻译请求
            _LOGGER.debug('[Converter/csv/get_zhcn_pack] Cache miss: {}.'.format(plugin_id))
            _LOGGER.info('[Converter/csv/get_zhcn_pack] Waiting for server translation: {}.'.format(plugin_id))
            remote_update = requests.get('https://nt.chenqlz.top/api/update?id={}'.format(plugin_id)).json()
            if remote_update['result'] == 0:
                # NTS翻译成功时，请求翻译后的数据，并存放至本地缓存
                remote_search = requests.get('https://nt.chenqlz.top/api/search?id={}'.format(plugin_id)).json()
                ret = remote_search['data']
                conn.execute("INSERT INTO zhcn VALUES (?, ?, ?, ?, ?)", (plugin_id, ret['script_name'], ret['synopsis'], ret['description'], ret['solution']))
                conn.execute("UPDATE config SET value = value + 1 WHERE `key` = 'count'")
            else:
                raise ValueError('[NTS] Server fault.')

    return ret