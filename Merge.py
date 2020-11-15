# -*- coding: utf-8 -*-
import os
import sys
import shutil
import argparse
from walkdir import filtered_walk, file_paths
from time import sleep

from Converter.macros import _LOGGER, _RESOURCE_PATH
import Converter.walk
import Converter.document

def main():
    # argparse：传入path
    parser = argparse.ArgumentParser(prog='Merge', description='读取所有输入的Word文件，转换后合并PDF。')
    # 传入preserve，保留合并时产生的临时文件
    parser.add_argument(
        '-p',
        '--preserve', 
        default=False,
        action='store_true', 
        help='preserve temp PDF'
    )
    parser.add_argument('path', nargs='+', help='file path or dir path')
    args = parser.parse_args()
    preserve = args.preserve
    _LOGGER.info('[Merge] Started.')

    # 过滤doc/docx/pdf
    _LOGGER.debug('[Merge] arg_paths = "{}".'.format(args.path))
    # 传入的参数有顺序要求，不能使用set
    target_paths = []
    for arg_path in args.path:
        target_paths.extend(Converter.walk.file(arg_path, ['.doc', '.docx', '.pdf']))
    _LOGGER.debug('[Merge] target_paths = "{}".'.format(target_paths))

    # 调用Converter.document处理
    temp_PDF_paths = []
    try:
        for target_path in target_paths:
            temp_PDF_paths.append(Converter.document.convert_PDF(target_path))
        Converter.document.merge_PDF(temp_PDF_paths)
        if not preserve:
            for temp_PDF_path in set(temp_PDF_paths).difference(target_paths):
                os.remove(temp_PDF_path)
    except Exception as err:
        _LOGGER.warning('[Merge] Merge failure due to "{}"'.format(err))

    _LOGGER.info('[Merge] Finished.')

if __name__ == '__main__':
    main()
    sleep(2)

