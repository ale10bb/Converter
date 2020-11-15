# Word转换PDF及合并

将所有输入的doc/docx/pdf文件合并为一个PDF。

## 使用方式

``` 
usage: Merge [-h] [-p] path [path ...]

positional arguments:
  path            file path or dir path

optional arguments:
  -h, --help      show this help message and exit
  -p, --preserve  preserve temp PDF
```

- 可以打开一个或多个doc/docx/pdf文件。如果使用exe，则可以直接把文件拖到exe上打开。
- 合并结果输出在第一个文件所在目录下的output.pdf。
- 合并完成后将清理临时文件，可以使用``--preserve``参数保留。
- 在stdout输出INFO级别日志，在程序同目录下Converter.log输出DEBUG级别日志。