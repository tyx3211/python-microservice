```

.git/                   # Git版本控制文件夹
.venv/                  # Python虚拟环境文件夹
src/                    # 项目主代码目录
  controller_part/          # 边端controller部分
    controller/                 # 边端基础依赖库：controller包
      __init__.py                   # 包初始化文件
      config.py                     # 配置模块
      controller_main.py            # 边端核心逻辑模块
      execorder.py                  # 指令执行模块
      getStatusInfo.py              # 获取状态信息模块
      logger.py                     # 日志记录模块
      sftp_upload.py                # SFTP文件上传模块
    test_start_1.py               # 测试脚本1
    test_start_2.py               # 测试脚本2
    User.py                       # 用户配置
  Server/               # 服务端相关部分
    api.py                  # API 接口逻辑
    database_ini.json       # 数据库初始化配置文件
    Database_OP.py          # 数据库操作模块
    pre_SQL.sql             # 数据库预定义SQL脚本
    south_api_core.py       # 南向接口核心逻辑实现
    start.sh                # 启动服务的Shell脚本
.gitignore              # Git忽略规则文件
README.md               # 项目说明文档
requirements.txt        # Python依赖库清单

```

1. 如上目录所示，请自行创建.vnev虚拟环境，并安装所需依赖库(见requirements.txt)。
2. 请在src/Server/database_ini.json中配置数据库连接信息。
3. 切换为 root 用户，并进入src/Server目录，运行api.py文件，启动服务端。
4. 或者也可以sudo bash start.sh启动服务端。
5. 对于边端，test_start_1.py和test_start_2.py为启动脚本，使用它们启动边端服务。
