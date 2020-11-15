# -*- coding: UTF-8 -*-
import sys
import os.path

# 以下全局变量，由__init__初始化
# 初始值均为None，在__init__之后应当被设置为正确的类型
_LOGGER = None

def _RESOURCE_PATH(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.dirname(sys.argv[0])
    return os.path.join(base_path, relative_path)