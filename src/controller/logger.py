import logging
from logging.handlers import TimedRotatingFileHandler
import os

# 获取当前模块文件的所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 创建 log 子目录
log_dir = os.path.join(current_dir, "log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日志文件路径
log_file = os.path.join(log_dir, "app.log")

# 配置日志处理器
handler = TimedRotatingFileHandler(
    log_file, when="D", interval=3, backupCount=0, encoding="utf-8"
)
# when="D"：按天分片
# interval=3：每 3 天分片一次
# backupCount=0：不保留日志文件
# encoding="utf-8"：避免中文乱码

# 设置日志格式
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# 配置日志
myLogger = logging.getLogger("ThreeDayRotatingLogger")
myLogger.setLevel(logging.DEBUG)  # 日志级别
myLogger.addHandler(handler)

# 测试日志
if __name__ == "__main__":
    myLogger.info("This is a test log.")
    myLogger.info("Logs will rotate every 3 days.")
