# -*- coding: UTF-8 -*-
import datetime
import sqlite3
import requests

from Converter.macros import _LOGGER

def Nessus_db(db_file_path:str):
    ''' 尝试更新本地数据库{db_file_path}。

    Args:
        db_file_path(str): 本地数据库文件的路径
    '''
    try:
        # 从 local DB 中读取数据库版本
        local_info_pack = {}
        conn = sqlite3.connect(db_file_path, isolation_level=None)
        row = conn.execute("SELECT value FROM config WHERE `key` = 'count'").fetchone()
        local_info_pack['count'] = int(row[0])
        row = conn.execute("SELECT value FROM config WHERE `key` = 'built'").fetchone()
        local_info_pack['built'] = int(row[0])
        conn.close()
        # 请求NTS的数据库版本并比对
        remote_info_pack = requests.get('https://nt.chenqlz.top/api/info').json()['data']
        if local_info_pack['built'] >= remote_info_pack['built']:
            _LOGGER.info('[Nessus] Up to date.')
            return
        _LOGGER.info('[Nessus] Downloading remote DB: {} ({} vulns).'.format(datetime.datetime.fromtimestamp(remote_info_pack['built']).strftime('%Y-%m-%d'), remote_info_pack['count']))
        with open(db_file_path, 'wb') as db_file:
            db_file.write(requests.get('https://nt.chenqlz.top/static/vulns.sqlite3').content)
        _LOGGER.info('[Nessus] Update complete.')
    except Exception as err:
        _LOGGER.error('[Nessus] Update failure due to "{}"'.format(err))