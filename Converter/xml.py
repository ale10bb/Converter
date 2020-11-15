# -*- coding: UTF-8 -*-
import xml.etree.ElementTree as ET
import re

from .macros import _LOGGER

def read_AppScan(src_file_path:str) -> ET.Element:
    ''' 尝试以AppScan模式读取{src_file_path}，并按照测评能手标准XML生成ET元素树。

    Args:
        src_file_path(str): 读取文件的路径

    Returns:
        ET.Element: ET元素树的根节点

    Raises:
        ValueError: 如果文件不是一个AppScan的XML
    '''

    _LOGGER.info('[Converter/xml/read_AppScan] Reading "{}".'.format(src_file_path))
    srcXMLRoot = ET.ElementTree().parse(src_file_path)
    if srcXMLRoot.tag != 'xml-report' or srcXMLRoot.get('name') != 'AppScan Report':
        raise ValueError('Not an AppScan XML.')

    XMLVersion = srcXMLRoot.get('xmlExportVersion')
    _LOGGER.debug('[Converter/xml/read_AppScan] XMLVersion = ' + XMLVersion)
    newRoot = ET.Element('REPORT')

    # ====读写扫描基本信息====
    timeResult = srcXMLRoot.find('./scan-information/scan-date-and-time').text
    taskResult = srcXMLRoot.find('./scan-information/scan-name').text
    _LOGGER.debug('[Converter/xml/read_AppScan] scan-date-and-time = "{}".'.format(timeResult))
    _LOGGER.debug('[Converter/xml/read_AppScan] scan-name = "{}".'.format(taskResult))
    ET.SubElement(newRoot, 'SCANINFO', {'FILE_ID': 'Converted', 'MAKERS': 'HCL', 'POLICY': '完全扫描', 'SCANTASK': taskResult, 'SCANTIME': timeResult, 'TOOLNAME': 'AppScan Standard'})
    
    # ====读取起始url，用作扫描资产 ====
    # 并在此生成host外部格式
    assetUrl = srcXMLRoot.find('./scan-configuration/starting-url').text
    _LOGGER.debug('[Converter/xml/read_AppScan] assetUrl = "{}".'.format(assetUrl))
    newDataRoot = ET.SubElement(newRoot, 'SCANDATA', {'TYPE': 'WEB'})
    newHostRoot = ET.SubElement(newDataRoot, 'HOST', {'WEB': assetUrl})
    ET.SubElement(newHostRoot, 'WEBSERVERBANNER')
    ET.SubElement(newHostRoot, 'SERVERVERSION')
    ET.SubElement(newHostRoot, 'TECHNOLOGIES')
    newHostDataRoot = ET.SubElement(newHostRoot, 'DATA')

    # ====构建字典====
    # 漏洞整改建议
    fixRecommendationGroup = {}
    for fixRecommendationNode in srcXMLRoot.find('./fix-recommendation-group'):
        # 该版本xml中，fix-recommendation可能会针对asp/j2ee/php提出不同的建议，但一定有general
        # 为了省力，仅读取general的整改建议
        # 每个node下，还需要进入<general><fixRecommendation type="General">两层标签，之后读取text、去除None、拼接
        fixRecommendationGroup[fixRecommendationNode.get('id')] = '\n'.join(filter(
            None, 
            [
                fixRecommendationContent.text 
                for fixRecommendationContent in fixRecommendationNode.findall('./general/fixRecommendation/*')
            ]
        ))
    _LOGGER.debug('[Converter/xml/read_AppScan] fixRecommendationGroup = "{}".'.format(fixRecommendationGroup.keys()))
    # 漏洞种类
    threatClassGroup = {}
    for threatClassNode in srcXMLRoot.find('./threat-class-group'):
        threatClassGroup[threatClassNode.get('id')] = threatClassNode.text
    _LOGGER.debug('[Converter/xml/read_AppScan] threatClassGroup = "{}".'.format(threatClassGroup.keys()))
    # 漏洞简述
    securityRiskGroup = {}
    for securityRiskNode in srcXMLRoot.find('./security-risk-group'):
        securityRiskGroup[securityRiskNode.get('id')] = securityRiskNode.text
    _LOGGER.debug('[Converter/xml/read_AppScan] securityRiskGroup = "{}".'.format(securityRiskGroup.keys()))
    # 漏洞涉及url
    urlGroup = {}
    for urlNode in srcXMLRoot.find('./url-group'):
        urlGroup[urlNode.get('id')] = urlNode.find('./name').text
    _LOGGER.debug('urlGroup has "{}".'.format(urlGroup.keys()))
    # 实体参数
    entityGroup = {}
    for entityNode in srcXMLRoot.find('./entity-group'):
        # issue(200819-1)某些xml中，entity的<name>标签没有内容，导致转换报错
        # bugfix：增加空值判断
        # 顺带增加包含标签情况的判断，如果含标签符号(<)也不读取
        if entityNode.find('name').text and '<' not in entityNode.find('name').text:
            entityGroup[entityNode.get('id')] = entityNode.find('name').text
        else:
            entityGroup[entityNode.get('id')] = ''
    _LOGGER.debug('[Converter/xml/read_AppScan] entityGroup = "{}".'.format(entityGroup.keys()))
    # 漏洞详情
    # issues = {issueType: [{'URL': xxx, 'PARAMETER': xxx, 'REQUEST': xxx, 'RESPONSE': xxx}, ..]}
    issues = {}
    # issue-group的每个item对应单个实体的单个漏洞
    for issueNode in srcXMLRoot.find('./issue-group'):
        issueType = issueNode.find('./issue-type/ref').text
        if not issues.__contains__(issueType):
            issues[issueType] = []
        #<test-http-traffic>下记录了测试的请求响应，去除appscan的标记符后，采用'HTTP/'作为标识分割请求和响应
        HTTPTrafficTexts = re.sub(
            '--begin_mark_tag--|--end_mark_tag--|--begin_highlight_tag--|--end_highlight_tag--', 
            '', 
            issueNode.find('./variant-group/item/test-http-traffic').text
        ).split('\nHTTP/', 1)
        #bugfix:非常规的HTTP请求响应，导致未分割时，手动增加一个空元素
        if len(HTTPTrafficTexts) == 1:
            HTTPTrafficTexts.append('Unknown')
        else:
            HTTPTrafficTexts[1] = 'HTTP/' + HTTPTrafficTexts[1]
        issues[issueType].append({
            'URL': urlGroup[issueNode.find('./url/ref').text] + '->' + entityGroup[issueNode.find('./entity/ref').text],
            'PARAMETER': entityGroup[issueNode.find('./entity/ref').text], 
            'REQUEST': HTTPTrafficTexts[0], 
            'RESPONSE': HTTPTrafficTexts[1]
        })
    _LOGGER.debug('[Converter/xml/read_AppScan] issues = "{}".'.format(issues.keys()))

    # ====定位到issue-type-group，读取漏洞类别====
    # 并在此生成新Data
    _LOGGER.debug('[Converter/xml/read_AppScan] -- Begin Issue Type --')
    for issueTypeNode in srcXMLRoot.find('./issue-type-group'):
        vulRoot = ET.SubElement(newHostDataRoot, 'VULNERABLITY')
        issueName = issueTypeNode.find('./name').text
        ET.SubElement(vulRoot, 'NAME').text = issueName
        ET.SubElement(vulRoot, 'NO', {'CNVD': 'NONE', 'CVE': 'NONE', 'MS': 'NONE', 'OTHER': 'NONE'})
        ET.SubElement(vulRoot, 'VULTYPE').text = threatClassGroup[issueTypeNode.find('./threat-class/ref').text]
        #转换风险
        if issueTypeNode.get('maxIssueSeverity') == '0':
            risk = '信息'
        if issueTypeNode.get('maxIssueSeverity') == '1':
            risk = '低危'
        if issueTypeNode.get('maxIssueSeverity') == '2':
            risk = '中危'
        if issueTypeNode.get('maxIssueSeverity') == '3':
            risk = '高危'
        ET.SubElement(vulRoot, 'RISK').text = risk
        ET.SubElement(vulRoot, 'SYNOPSIS').text = securityRiskGroup[issueTypeNode.find('./security-risks/ref').text]
        ET.SubElement(vulRoot, 'DESCRIPTION').text = securityRiskGroup[issueTypeNode.find('./security-risks/ref').text]
        ET.SubElement(vulRoot, 'SOLUTION').text = fixRecommendationGroup[issueTypeNode.find('./fix-recommendation/ref').text]
        ET.SubElement(vulRoot, 'VALIDATE')
        ET.SubElement(vulRoot, 'REFERENCE')
        # <DETAIL>中的四个元素，直接从issue字典中读取
        vulDetailsRoot = ET.SubElement(vulRoot, 'DETAILS')
        for issue in issues[issueTypeNode.get('id')]:
            URLRoot = ET.SubElement(vulDetailsRoot, 'URL', {'URL': issue['URL']})
            ET.SubElement(URLRoot, 'TYPE')
            ET.SubElement(URLRoot, 'PARAMETER').text = issue['PARAMETER']
            ET.SubElement(URLRoot, 'REQUEST').text = issue['REQUEST']
            ET.SubElement(URLRoot, 'RESPONSE').text = issue['RESPONSE']
        _LOGGER.debug('[Converter/xml/read_AppScan] "{}" has {} entities.'.format(issueName, len(issues[issueTypeNode.get('id')])))
    _LOGGER.debug('[Converter/xml/read_AppScan] -- End Issue Type --')

    return newRoot

def write(root:ET.Element, dst_file_path:str) -> int:
    ''' 将{root}为根的ET元素树写入{dst_file_path}

    Args:
        root(ET.Element): ET元素树的根节点
        dst_file_path(str): 写入文件的路径

    Returns:
        0: 操作完成
    '''

    new_tree = ET.ElementTree(root)
    new_tree.write(dst_file_path, encoding='utf-8')
    return 0