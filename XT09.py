# -*- coding: utf-8 -*-
import os
import sys
import shutil
import argparse
from time import sleep

from Converter.macros import _LOGGER, _RESOURCE_PATH
import Converter.walk
import Converter.document

def main():
    # argparse：传入path
    parser = argparse.ArgumentParser(prog='XT09', description='读取等保方案文件XT17，根据其中信息自动生成方案审核意见单XT09，并尝试转换PDF。')
    # 传入no-pdf，关闭自动生成PDF
    parser.add_argument(
        '-np',
        '--no-pdf', 
        default=False,
        action='store_true', 
        help='disable PDF generation'
    )
    parser.add_argument('path', nargs='+', help='file path or dir path')
    args = parser.parse_args()
    _LOGGER.info('[XT09] Started.')

    # 过滤doc/docx并去重
    _LOGGER.debug('[XT09] arg_paths = "{}".'.format(args.path))
    target_paths = set()
    for arg_path in args.path:
        target_paths = target_paths.union(set(Converter.walk.file(arg_path, ['.doc', '.docx'])))
    _LOGGER.debug('[XT09] target_paths = "{}".'.format(target_paths))

    # 读取自定义字典
    customized_advices = []
    try:
        # 字典文件不存在时释放res资源
        if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'AdviceList.txt')):
            shutil.copy(_RESOURCE_PATH(os.path.join('res', 'AdviceList.txt')), os.path.dirname(sys.argv[0]))
        # 尝试读取自定义字典文件
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'AdviceList.txt'), encoding='utf-8') as f:
            raw_lines = f.readlines()
        for raw_line in raw_lines:
            if not raw_line.lstrip().startswith('#'):
                customized_advices.append(raw_line.strip())
    except:
        _LOGGER.warning('[XT09] Fail to read "AdviceList.txt".')

    # 调用Converter.document处理
    count = 0
    for target_path in target_paths:
        try:
            # 读取基本信息，并写入随机审核意见
            info = Converter.document.read_XT17(target_path)
            info['advices'] = Converter.walk.XT09_advices(customized_advices)
            # 根据读取的信息生成审核意见单，并转换成PDF
            XT09_file_path = Converter.document.make_XT09(os.path.dirname(target_path), info)
            if not args.no_pdf:
                Converter.document.convert_PDF(XT09_file_path)
            count += 1
        except Exception as err:
            _LOGGER.warning('[XT09] Generation failure due to "{}"'.format(err))

    _LOGGER.info('[XT09] Finished with {} generated.'.format(count))

if __name__ == '__main__':
    main()
    sleep(2)

