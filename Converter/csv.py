# -*- coding: UTF-8 -*-
import os
import csv
import sys
import sqlite3
import requests

from Converter.macros import _LOGGER

def read_Nessus(src_file_path:str) -> list:
    ''' 尝试以Nessus模式读取{src_file_path}，并返回翻译后的CSV行列表。

    Args:
        src_file_path(str): 读取文件的路径

    Returns:
        list: CSV行列表
    '''
    _LOGGER.info('[Converter/csv/read_Nessus] Reading "{}".'.format(src_file_path))
    ret = []
    with open(src_file_path, encoding='utf-8-sig') as src_file:
        rows = csv.DictReader(src_file, quoting=csv.QUOTE_ALL)
        for row in rows:
            # 对于没有Plugin ID列，或Plugin ID不为数字的异常情况，直接跳过该行
            try:
                plugin_id = int(row['Plugin ID'])
            except:
                continue
            try:
                zhcn_pack = get_zhcn_pack(int(row['Plugin ID']))
            # 对于get_zhcn_pack的任意失败情况，直接跳过翻译并使用原始数据
            except Exception as err:
                _LOGGER.warning('[Converter/csv/read_Nessus] Skipping {} due to "{}".'.format(plugin_id, err))
                if row.__contains__('Name'):
                    zhcn_pack['script_name'] = row['Name']
                else:
                    zhcn_pack['script_name'] = ''
                if row.__contains__('Synopsis'):
                    zhcn_pack['synopsis'] = row['Synopsis']
                else:
                    zhcn_pack['synopsis'] = ''
                if row.__contains__('Description'):
                    zhcn_pack['description'] = row['Description']
                else:
                    zhcn_pack['description'] = ''
                if row.__contains__('Solution'):
                    zhcn_pack['solution'] = row['Solution']
                else:
                    zhcn_pack['solution'] = ''
                
            row['Name'] = zhcn_pack['script_name']
            row['Synopsis'] = zhcn_pack['synopsis']
            row['Description'] = zhcn_pack['description']
            row['Solution'] = zhcn_pack['solution']
            ret.append(row)
    return ret

def get_zhcn_pack(plugin_id:int) -> dict:
    ''' 尝试读取读取{plugin_id}的中文信息，缓存未命中时向服务器请求结果。

    Args:
        plugin_id(int): 插件ID

    Returns:
        dict: {'script_name': xxx, 'synopsis': xxx, 'description': xxx, 'solution': xxx}

    Raises:
        ValueError: 如果服务器请求失败
    '''
    ret = {'script_name': '', 'synopsis': '', 'description': '', 'solution': ''}

    # 本地文件必须位于可执行文件的同目录下
    conn = sqlite3.connect(os.path.join(os.path.dirname(sys.argv[0]), 'vulns.sqlite3'), isolation_level=None)
    # 首先从本地sqlite缓存读取
    row = conn.execute("SELECT * FROM zhcn WHERE `pluginid` = ?", (plugin_id,)).fetchone()
    if row:
        _LOGGER.debug('[Converter/csv/get_zhcn_pack] Local hit: {}.'.format(plugin_id))
        ret['script_name'] = row[1]
        ret['synopsis'] = row[2]
        ret['description'] = row[3]
        ret['solution'] = row[4]
    else:
        # 本地缓存未命中时，向服务器请求缓存
        remote_search = requests.get('https://nt.chenqlz.top/api/search?id={}'.format(plugin_id)).json()
        if remote_search['result'] == 0:
            _LOGGER.debug('[Converter/csv/get_zhcn_pack] Remote hit: {}.'.format(plugin_id))
            ret['script_name'] = remote_search['data']['script_name']
            ret['synopsis'] = remote_search['data']['synopsis']
            ret['description'] = remote_search['data']['description']
            ret['solution'] = remote_search['data']['solution']
            # 服务器缓存命中时，将结果存放至本地缓存
            _LOGGER.info('[Converter/csv/get_zhcn_pack] Adding to local cache: {}.'.format(plugin_id))
            conn.execute("INSERT INTO zhcn VALUES (?, ?, ?, ?, ?)", (plugin_id, ret['script_name'], ret['synopsis'], ret['description'], ret['solution']))
            count = int(conn.execute("SELECT value FROM config WHERE `key` = 'count'").fetchone()[0])
            conn.execute("UPDATE config SET value = ? where `key` = 'count'", (str(count+1),))
        elif remote_search['result'] == 2:
            # 服务器缓存未命中时，向服务器发起翻译请求
            _LOGGER.debug('[Converter/csv/get_zhcn_pack] Cache miss: {}.'.format(plugin_id))
            _LOGGER.info('[Converter/csv/get_zhcn_pack] Waiting for server translation: {}.'.format(plugin_id))
            remote_update = requests.get('https://nt.chenqlz.top/api/update?id={}'.format(plugin_id)).json()
            if remote_update['result'] == 0:
                # 服务器翻译成功时，请求翻译后的数据
                remote_search = requests.get('https://nt.chenqlz.top/api/search?id={}'.format(plugin_id)).json()
                ret['script_name'] = remote_search['data']['script_name']
                ret['synopsis'] = remote_search['data']['synopsis']
                ret['description'] = remote_search['data']['description']
                ret['solution'] = remote_search['data']['solution']
                # 将结果存放至本地缓存
                _LOGGER.info('[Converter/csv/get_zhcn_pack] Adding to local cache: {}.'.format(plugin_id))
                conn.execute("INSERT INTO zhcn VALUES (?, ?, ?, ?, ?)", (plugin_id, ret['script_name'], ret['synopsis'], ret['description'], ret['solution']))
                count = int(conn.execute("SELECT value FROM config WHERE `key` = 'count'").fetchone()[0])
                conn.execute("UPDATE config SET value = ? where `key` = 'count'", (str(count+1),))
            else:
                raise ValueError('Remote server fault.')

    return ret