# epub自动翻译程序
- 用于翻译各种日语、英语书。
- 使用的是同花顺API，目前限时免费。
- 20分钟一本书。
- 有断点记录功能，闪退了可以继续工作。
- 日语书籍的ruby先去掉再翻译提高准确率。

# 使用方法
- 注册[同花顺翻译](https://translate.aicubes.cn/api "同花顺翻译")
- API应用管理中找到appid和appkey，填入脚本中

# 需要安装的包
- beautifulsoup4==4.10.0
- requests==2.26.0
- tqdm==4.62.1
