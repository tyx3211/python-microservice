import logging
from logging.handlers import TimedRotatingFileHandler
import os
# from controller.config import config

# 暴露日志单例对象
myLogger = logging.getLogger("ThreeDayRotatingLogger")

def SetLogMessage(logger_object, log_dir, log_path):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 配置日志处理器
    handler = TimedRotatingFileHandler(
        log_path, when="D", interval=3, backupCount=0, encoding="utf-8"
    )
    # when="D"：按天分片
    # interval=3：每 3 天分片一次
    # backupCount=0：不保留日志文件
    # encoding="utf-8"：避免中文乱码

    # 设置日志格式
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # 配置日志对象
    logger_object.setLevel(logging.DEBUG)  # 日志级别
    logger_object.addHandler(handler)

# 测试日志
if __name__ == "__main__":
    SetLogMessage(myLogger, "./test_log_dir")
    myLogger.info("This is a test log.")
    myLogger.info("Logs will rotate every 3 days.")
