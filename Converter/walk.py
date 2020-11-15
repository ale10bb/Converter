# -*- coding: UTF-8 -*-
import os
import random
from walkdir import filtered_walk, file_paths

from Converter.macros import _LOGGER

def file(path:str, exts:list) -> list:
    ''' 在{path}中搜索所有扩展名符合{exts}的文件，并转换成绝对路径。

    Args:
        path: 文件或目录
        exts: 扩展名列表

    Returns:
        list: 文件绝对路径列表
    '''

    # 将path转换为绝对路径
    if not os.path.isabs(path):
        abs_path = os.path.join(os.getcwd(), path)
    else:
        abs_path = path
    # 遍历path，并返回指定扩展名的文件
    if os.path.isfile(path) and os.path.splitext(path)[1].lower() in exts:
        return [abs_path]
    if os.path.isdir(abs_path):
        return filter(None, list(file_paths(filtered_walk(abs_path, included_files=['*' + e for e in exts]))))


def XT09_advices(customized_advices:list=[]) -> str:
    ''' 生成XT09的建议。如果自定义建议数量少于四个，则使用内置字典。

    Args:
        customized_advices(list): 自定义建议列表

    Returns:
        str: 生成的建议（按\n换行）
    '''

    # 内置建议字典
    advices = [
        '封面的项目编号有误。',
        '方案中的被测单位名称可能有误，请与用户方充分沟通并确认。',
        '方案页脚的页码和总页码处不正确。',
        '方案中1.4、4.2等相关章节的段落缩进、字体大小等格式方面有不一致等问题，请通篇查找并修订。',
        '图1.1的图题描述错误，应为“等级保护测评工作流程图”。',
        '1.3章节测评过程中的个别年份存在笔误。',
        '2.2章节内容缺失。',
        '2.2章节“承载业务情况”的个别信息资产描述与2.4章节相关信息资产表的内容不一致。',
        '2.4章节信息资产表中个别信息资产的版本及型号未描述完善。',
        '2.4章节信息资产表中个别栏目为空，且未阐明原因或加以注销。',
        '3.1.1章节关注的抽选信息资产类别，未在3.1.2章节予以体现完整，例如终端这类信息资产。',
        '3.1.2章节抽选的信息资产列表中的个别信息资产类别，未在3.1.1章节中体现，存在上下文不一致的情况。',
        '3.3章节内容缺失。',
        '4.1章节内容有误。',
        '5.2章节，应对测试工具的接入点加以补充和完善，并与用户方做充分的沟通，确保扫描和渗透性测试的顺利实施。',
        '6.2章节扩展安全要求中个别栏目为空，且未阐明原因或加以注销。',
        '8.1章节“项目组织”中表格内的个别栏目未填写内容，请补充完善。'
        ]
    
    if len(customized_advices) >= 4:
        advices = customized_advices
        _LOGGER.info('[Converter/word/get_advices] Using customized advices.')
    else:
        _LOGGER.info('[Converter/word/get_advices] Using bulitin advices.')

    # 随机取2-4个索引
    chosen_indexs = random.sample(range(0, len(advices)), random.randint(2, 4))
    # 拼接审核意见字符串
    seq = 1
    chosen_advices = []
    for chosen_index in chosen_indexs:
        chosen_advices.append('{}、{}'.format(seq, advices[chosen_index]))
        seq += 1
    _LOGGER.debug('[Converter/word/get_advices] chosen_advices = "{}".'.format(chosen_advices))
    return '\n'.join(chosen_advices)