# -*- coding: UTF-8 -*-
import datetime
import sqlite3
import requests

from .macros import _LOGGER

def update_Nessus(db_file_path:str) -> int:
    ''' 尝试更新本地数据库{db_file_path}。

    Args:
        db_file_path(str): 本地数据库文件的路径
    '''
    try:
        # 从 local DB 中读取数据库版本
        local_info_pack = {}
        conn = sqlite3.connect(db_file_path, isolation_level=None)
        # 对于非法数据库或不存在文件的情况，将信息设置为0
        try:
            row = conn.execute("SELECT value FROM config WHERE `key` = 'count'").fetchone()
            local_info_pack['count'] = int(row[0])
        except:
            local_info_pack['count'] = 0
        try:
            row = conn.execute("SELECT value FROM config WHERE `key` = 'built'").fetchone()
            local_info_pack['built'] = int(row[0])
        except:
            local_info_pack['built'] = 0 
        conn.close()
        # 请求NTS的数据库版本并比对
        remote_info_pack = requests.get('https://nt.chenqlz.top/api/info').json()['data']
        if local_info_pack['built'] >= remote_info_pack['built']:
            _LOGGER.info('[Nessus] Up to date.')
            return
        _LOGGER.info(
            '[Nessus] Downloading remote DB: {} ({} smore vulns).'.format(
                datetime.datetime.fromtimestamp(remote_info_pack['built']).strftime('%Y-%m-%d'), 
                remote_info_pack['count'] - local_info_pack['count']
            )
        )
        with open(db_file_path, 'wb') as db_file:
            db_file.write(requests.get('https://nt.chenqlz.top/static/vulns.sqlite3').content)
        _LOGGER.info('[Nessus] Update complete.')
        return 0
    except Exception as err:
        _LOGGER.error('[Nessus] Update failure due to "{}"'.format(err))
        return 1

def isvalid_Nessus(db_file_path:str) -> bool:
    ''' 检查本地数据库{db_file_path}的有效性。

    Args:
        db_file_path(str): 本地数据库文件的路径
    '''
    conn = sqlite3.connect(db_file_path)
    try:
        conn.execute("SELECT pluginid, reviewed, script_name, synopsis, description, solution FROM zhcn LIMIT 1")
        row = conn.execute("SELECT value FROM config where `key` = 'count'")
        if not row:
            raise ValueError
        row = conn.execute("SELECT value FROM config where `key` = 'bulit'")
        if not row:
            raise ValueError
        return True
    except:
        return False
    finally:
        conn.close()

def get_Nessus_zhcn_pack(plugin_id:int, db_file_path:str) -> dict:
    ''' 尝试读取读取{plugin_id}的中文信息，缓存未命中时向服务器请求结果。

    Args:
        plugin_id(int): 插件ID
        db_file_path(str): 本地数据库文件的路径

    Returns:
        dict: {'pluginid': xxx, 'reviewed': xxx, 'script_name': xxx, 'synopsis': xxx, 'description': xxx, 'solution': xxx}

    Raises:
        ValueError: 如果服务器请求失败
    '''
    ret = {'pluginid': plugin_id}
    
    conn = sqlite3.connect(db_file_path, isolation_level=None)
    # 首先从本地sqlite缓存读取
    row = conn.execute("SELECT * FROM zhcn WHERE `pluginid` = ?", (plugin_id,)).fetchone()
    if row:
        ret['reviewed'] = row[1]
        ret['script_name'] = row[2]
        ret['synopsis'] = row[3]
        ret['description'] = row[4]
        ret['solution'] = row[5]
    else:
        # 本地缓存未命中时，向NTS请求缓存
        _LOGGER.debug('[Converter/csv/get_zhcn_pack] Local miss. Quering NTS: {}.'.format(plugin_id))
        remote_search = requests.get('https://nt.chenqlz.top/api/search?id={}'.format(plugin_id)).json()
        if remote_search['result'] == 0:
            # NTS缓存命中时，将结果存放至本地缓存
            ret = remote_search['data']
            conn.execute("INSERT INTO zhcn VALUES (?, ?, ?, ?, ?, ?)", (plugin_id, ret['reviewed'], ret['script_name'], ret['synopsis'], ret['description'], ret['solution']))
            conn.execute("UPDATE config SET value = value + 1 WHERE `key` = 'count'")
        elif remote_search['result'] == 2:
            # NTS缓存未命中时，向NTS发起翻译请求
            _LOGGER.info('[Converter/csv/get_zhcn_pack] Remote miss. Waiting for server translation: {}.'.format(plugin_id))
            remote_update = requests.get('https://nt.chenqlz.top/api/update?id={}'.format(plugin_id)).json()
            if remote_update['result'] == 0:
                # NTS翻译成功时，请求翻译后的数据，并存放至本地缓存
                remote_search = requests.get('https://nt.chenqlz.top/api/search?id={}'.format(plugin_id)).json()
                ret = remote_search['data']
                conn.execute("INSERT INTO zhcn VALUES (?, ?, ?, ?, ?, ?)", (plugin_id, ret['reviewed'], ret['script_name'], ret['synopsis'], ret['description'], ret['solution']))
                conn.execute("UPDATE config SET value = value + 1 WHERE `key` = 'count'")
            else:
                raise ValueError('[NTS] Server fault.')

    return ret