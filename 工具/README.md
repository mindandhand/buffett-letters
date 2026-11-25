# 生成与检查工具

在项目根目录运行命令。工具只依赖项目内文件，不需要原整理工作目录。

```sh
python3 -m pip install -r 工具/requirements.txt
python3 工具/build_word.py
python3 工具/check_project.py
```

也可以只生成一个年度或一个版本：

```sh
python3 工具/build_word.py --year 2024 --language 中文版
```

Word使用宋体家族和Times New Roman，固定宽度英文表格使用Courier New。生成时需要阅读软件具备相应字体或合适的中文替代字体。原始图片嵌入Word时转换为RGB，以兼容CMYK JPEG照片。

中英对照由已审核的段落组或原文页组成。`校对记录/对齐数据.json`保存对应关系；修改原文或译文后，先更新这份数据，再生成对照版：

```sh
python3 工具/build_bilingual.py
python3 工具/build_word.py
python3 工具/check_project.py
```

检查工具核对48年文件覆盖、原始资料哈希、本地链接，以及Markdown与Word的数字序列、中文字符序列和英文词序。通过这些检查不能替代语义校对或Word逐页视觉终审。

修改Word样式后，应重新使用LibreOffice导出PDF与页面图片，检查字体、表格、图片和分页。页面图片属于排版检查资料，不放进阅读目录。
