1. pip install -r ./requirements.txt
2. src目录为核心代码，其中no_used子目录和test子目录是临时测试代码（不需要关注），heart_demo心跳样例（不需要关注）
3. 真正需要的：src/Server 目录 下是微服务核心逻辑代码，其中
   - api.py 是微服务启动文件
   - south_api_core.py是 微服务依赖的南向接口核心功能的封装文件
   - DataBase_OP.py是 封装好的数据库操作模块
4. 边端核心代码：在src/controller目录下
   - controller.py是 边端依赖级基础功能的暴露模块
   - getStatusInfo.py 是封装好的拿到边端状态的模块
   - logger.py 是封装好的日志模块
   - execorder.py 指令执行指令模块

