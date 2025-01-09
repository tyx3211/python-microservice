import os
from controller.controller_main import startControllerBasicApp
from User import user,password # 这个实际不需要

Host = "112.124.43.208"

Port = 9090

sftp_user = user # 这里替换为实际的云服务器sftp用户名

sftp_password = password # 这里替换为实际的云服务器sftp用户密码

# 自定义指令中执行函数要求使用关键字参数，远程json在params对象中使用

# 指令：test_order

def test_order_exec(SomethingToPrint="Hello World"):
    print(SomethingToPrint)

# 至少提供SN和Model，否则无法获取状态信息
startControllerBasicApp(
    host=Host,
    port=Port,
    sftp_host=Host,
    sftp_port=22,
    sftp_username=sftp_user,
    sftp_password=sftp_password,
    device_id=None,
    device_password="testpassword",
    device_hardware_sn="SN123",
    device_hardware_model="ModelB",
    device_log_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..","device2_log"),
    device_log_name="device2.log",
    max_retries=5,
    outer_order_dict={"test_order":test_order_exec} # 暴露给用户的可配置自定义指令字典
)