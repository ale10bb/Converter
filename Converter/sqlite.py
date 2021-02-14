# -*- coding: UTF-8 -*-
import shutil
import sqlite3
import requests

from .macros import _LOGGER, _RESOURCE_PATH

def update_Nessus(db_file_path:str) -> int:
    ''' 尝试更新本地数据库{db_file_path}。

    Args:
        db_file_path(str): 本地数据库文件的路径
    '''
    try:
        with open(db_file_path, 'wb') as db_file:
            db_file.write(requests.get('https://static.chenqlz.top/converter/vulns.sqlite3').content)
        _LOGGER.info('[Nessus] Update complete.')
        return 0
    except:
        shutil.copyfile(_RESOURCE_PATH(os.path.join('res', 'empty.sqlite3')), db_file_path)
        _LOGGER.warning('[Nessus] Update failure. Use empty DB.')
        return 1 

def isvalid_Nessus(db_file_path:str) -> bool:
    ''' 检查本地数据库{db_file_path}的有效性。

    Args:
        db_file_path(str): 本地数据库文件的路径
    '''
    
    try:
        cnx = sqlite3.connect(db_file_path)
        cnx.execute("SELECT pluginid, reviewed, script_name, synopsis, description, solution FROM zhcn LIMIT 1")
        cnx.close()
        return True
    except:
        return False

def get_Nessus_zhcn_pack(plugin_id:int, db_file_path:str) -> dict:
    ''' 尝试读取读取{plugin_id}的中文信息，缓存未命中时向服务器请求结果。

    Args:
        plugin_id(int): 插件ID
        db_file_path(str): 本地数据库文件的路径

    Returns:
        dict: {'pluginid': xxx, 'script_name': xxx, 'synopsis': xxx, 'description': xxx, 'solution': xxx}

    Raises:
        ValueError: 如果服务器请求失败
    '''

    keys = ['pluginid', 'script_name', 'synopsis', 'description', 'solution']
    cnx = sqlite3.connect(db_file_path, isolation_level=None)
    # 首先从本地sqlite缓存读取
    row = cnx.execute("SELECT pluginid, script_name, synopsis, description, solution FROM zhcn WHERE `pluginid` = ?", (plugin_id,)).fetchone()
    if row:
        return dict(zip(keys, row))
        
    # 本地缓存未命中时，向NTS请求缓存，缓存未命中时发起翻译请求
    _LOGGER.debug('[Converter/csv/get_zhcn_pack] Local miss. Quering NTS: {}.'.format(plugin_id))
    remote_search = requests.get('https://nt.chenqlz.top/api/search?id={}'.format(plugin_id)).json()
    if remote_search['result'] == 0:
        remote_zhcn_pack = remote_search['data']
    elif remote_search['result'] == 2:
        _LOGGER.info('[Converter/csv/get_zhcn_pack] Remote miss. Waiting for server translation: {}.'.format(plugin_id))
        remote_update = requests.get('https://nt.chenqlz.top/api/update?id={}'.format(plugin_id)).json()
        if remote_update['result'] == 0:
            remote_zhcn_pack = remote_update['data']
        else:
            raise ValueError(remote_update['err'])
    # 查询结果插入本地数据库
    cnx.execute(
        "INSERT INTO zhcn VALUES (?, ?, ?, ?, ?, ?)", (
            remote_zhcn_pack['pluginid'], 
            remote_zhcn_pack['reviewed'], 
            remote_zhcn_pack['script_name'], 
            remote_zhcn_pack['synopsis'], 
            remote_zhcn_pack['description'], 
            remote_zhcn_pack['solution']
        )
    )
    remote_zhcn_pack.pop('reviewed', None)
    return remote_zhcn_pack