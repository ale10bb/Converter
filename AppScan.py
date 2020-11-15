# -*- coding: UTF-8 -*-
import os
import argparse
from walkdir import filtered_walk, file_paths
from time import sleep

from Converter.macros import _LOGGER
import Converter.walk
import Converter.xml

def main():
    # argparse：只需传入path，无其他开关
    parser = argparse.ArgumentParser(prog='AppScan', description='读取AppScan的XML文件(version 2.42)，转换成测评能手标准格式，转换结果分别保存至每个原始文件的同目录下。')
    parser.add_argument('path', nargs='+', help='file path or dir path')
    args = parser.parse_args()
    _LOGGER.info('[AppScan] Started.')

    # 过滤xml并去重
    _LOGGER.debug('[AppScan] arg_paths = "{}".'.format(args.path))
    target_paths = set()
    for arg_path in args.path:
        target_paths = target_paths.union(set(Converter.walk.file(arg_path, ['.xml'])))
    _LOGGER.debug('[AppScan] target_paths = "{}".'.format(target_paths))

    # 调用Converter.xml处理
    count = 0
    for target_path in target_paths:
        try:
            new_root = Converter.xml.read_AppScan(target_path)
            Converter.xml.write(new_root, os.path.splitext(target_path)[0] + '_converted.xml')
            count += 1
        except Exception as err:
            _LOGGER.warning('[AppScan] Conversion failure due to "{}"'.format(err))

    _LOGGER.info('[AppScan] Finished with {} converted.'.format(count))

if __name__ == '__main__':
    main()
    sleep(2)

