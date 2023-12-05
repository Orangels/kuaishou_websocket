# 使用说明

## 目录结构
```
快手弹幕
│
├── cookie  # 登录后存放cookie文件
│     └── 手机号.json # cookie文件
├── config.ini  # 配置文件 
├── main.py    # 前端运行文件
├── kuaishou_pb2.py  # 弹幕解析文件
└── requirements.txt # 依赖文件
```
## 安装
- 执行下列命令安装
```
pip install -r requirements.txt
playwright install firefox
pyi-makespec -F -w .\run.py
Pyinstaller run.spec
```
修改 run.spec 的 ['run.py','kuaishou_pb2.py', 'giftJson.py']  
[pyinstaller 和 playwright](https://blog.csdn.net/xiaohouzi112233/article/details/128013408)  
[pyinstaller](https://xiaokang2022.blog.csdn.net/article/details/127585881?spm=1001.2101.3001.6650.3&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7ERate-3-127585881-blog-123668136.235%5Ev38%5Epc_relevant_yljh&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7ERate-3-127585881-blog-123668136.235%5Ev38%5Epc_relevant_yljh&utm_relevant_index=4)
python3.10以上下载的playinstaller 需要指定版本[github](https://github.com/TomSchimansky/CustomTkinter/wiki/Packaging#windows-pyinstaller-auto-py-to-exe)  
```
pip install "pyinstaller>=5.12"
```
## 优点
- 速度快
- 可以多线程
## 缺点
- 由于有滑块存在所以暂不支持无头模式

## 配置文件`config.ini`详解
```
live_ids = KPL704668133 多个使用','间隔
thread = 2
phone = 登录的手机号
```

## 待优化
- 移动快手滑块
