# Nessus CSV自动翻译

使用 Google Cloud Translation 将Nessus导出CSV的部分英文描述字段（``Name``、``Synopsis``、``Description``、``Solution``）翻译成中文。翻译时仅采用``Plugin ID``匹配，并修改原始CSV的对应字段（不存在时则新建）。

## 使用方式

``` 
usage: Nessus [-h] [-u] path [path ...]

positional arguments:
  path          file path or dir path

optional arguments:
  -h, --help    show this help message and exit
  -u, --update  update local DB and exit
  
**无输入参数时进入更新模式**
```

- 可以打开一个或多个csv文件。如果使用exe，则可以直接把文件拖到exe上打开。
- 转换输出时，使用原始文件名增加后缀*_converted.csv。
- 转换时优先使用本地数据库，之后使用NTS服务端的数据库，均未命中时提交翻译请求。
- 未联网时，仅可使用本地数据库翻译，并跳过所有未命中缓存的``Plugin ID``。
- 在stdout输出INFO级别日志，在程序同目录下Converter.log输出DEBUG级别日志。

## 服务端

目前所有翻译请求由NTS-API转发，并暂存在NTS数据库中。NTS数据库每天生成sqlite格式的本地数据库，可在[chenqlz.top](https://nt.chenqlz.top/)下载。

目前不考虑爬取[NessusPlugins](https://www.tenable.com/plugins)上的数据（虽然很好爬）。