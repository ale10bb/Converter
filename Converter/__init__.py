# -*- coding: UTF-8 -*-
import logging
import os.path
import sys

from . import macros

macros._LOGGER = logging.getLogger()
macros._LOGGER.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# 使用FileHandler输出到文件
fh = logging.FileHandler(os.path.join(os.path.dirname(sys.argv[0]), 'Converter.log'), encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
# 使用StreamHandler输出到屏幕
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
# 添加两个Handler
macros._LOGGER.addHandler(ch)
macros._LOGGER.addHandler(fh)