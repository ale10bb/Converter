# 方案审核意见单

根据测评方案XT17中的信息，自动生成方案审核意见单XT09。

## 程序流程

- 从字典中随机选取审核意见
- 打开测评方案XT17，读取项目编号、项目名称、方案日期、编写人
- 在测评方案的同一目录下生成方案审核意见单XT09
- 将XT09转换为PDF

## 使用方式

``` 
usage: XT09 [-h] [-np] path [path ...]

positional arguments:
  path           file path or dir path

optional arguments:
  -h, --help     show this help message and exit
  -np, --no-pdf  disable PDF generation
```

- 可以打开一个或多个doc/docx文件。如果使用exe，则可以直接把文件拖到exe上打开。
- 转换输出时，使用原始文件名增加后缀*_converted.xml。
- 可以使用``--no-pdf``参数，关闭自动转换PDF的功能。
- 首次打开时，会在程序同目录生成AdviceList.txt。可以在文件中自定义审核意见，有效数量超过4条时，程序使用自定义审核意见替换内置字典。
- 在stdout输出INFO级别日志，在程序同目录下Converter.log输出DEBUG级别日志。