# 配置对象，用于初始化时指定配置参数
# 含有以下属性：
#   - host: 服务器地址(默认None)
#   - port: 服务器端口(默认None)
#   - sftp_host: sftp服务器地址(默认None)
#   - sftp_port: sftp服务器端口(默认None)
#   - sftp_username: sftp用户名(默认None)
#   - sftp_password: sftp密码(默认None)
#   - device_id: 设备ID(默认None)
#   - device_password: 设备密码(默认None)
#   - device_hardware_sn: 设备硬件序列号(默认None)
#   - device_hardware_model: 设备硬件型号(默认None)
#   - server_url: 服务器地址(默认None),由host和port组成
#   - device_log_dir: 设备日志目录(默认当前所在目录下的log文件夹)
#   - device_log_name: 设备日志名称(默认device.log)
#   - device_log_local_path: 设备日志本地路径(默认None),由device_log_dir和device_log_name组成
#   - max_retries: 最大重连次数(默认5)
#   - outer_order_dict : 外部指令字典(默认{})

import os

current_dir = os.path.dirname(os.path.abspath(__file__))


class Config:
    def __init__(
        self,
        host=None,
        port=None,
        sftp_host=None,
        sftp_port=None,
        sftp_username=None,
        sftp_password=None,
        device_id=None,
        device_password=None,
        device_hardware_sn=None,
        device_hardware_model=None,
        device_log_dir=current_dir,
        device_log_name="device.log",
        max_retries=5,
        outer_order_dict={},
    ):
        self.host = host
        self.port = port
        self.sftp_host = sftp_host
        self.sftp_port = sftp_port
        self.sftp_username = sftp_username
        self.sftp_password = sftp_password
        self.device_id = device_id
        self.device_password = device_password
        self.device_hardware_sn = device_hardware_sn
        self.device_hardware_model = device_hardware_model
        self.device_log_dir = device_log_dir
        self.device_log_name = device_log_name
        self.max_retries = max_retries
        self.outer_order_dict = outer_order_dict

        # 通过参数中的host和port生成server_url
        if host and port:
            self.server_url = f"ws://{host}:{port}/ws"
        else:
            self.server_url = None

        # 通过参数中的device_log_dir和device_log_name生成device_log_local_path,如果参数中没有指定device_log_dir则默认使用当前目录下的log文件夹
        if device_log_dir and device_log_name:
            self.device_log_local_path = os.path.join(device_log_dir, device_log_name)
        else:
            self.device_log_local_path = os.path.join(current_dir, "log", "device.log")

    def Set(
        self,
        host=None,
        port=None,
        sftp_host=None,
        sftp_port=None,
        sftp_username=None,
        sftp_password=None,
        device_id=None,
        device_password=None,
        device_hardware_sn=None,
        device_hardware_model=None,
        device_log_dir=None,
        device_log_name=None,
        max_retries=None,
        outer_order_dict={},
    ):
        if host:
            self.host = host
        if port:
            self.port = port
        if sftp_host:
            self.sftp_host = sftp_host
        if sftp_port:
            self.sftp_port = sftp_port
        if sftp_username:
            self.sftp_username = sftp_username
        if sftp_password:
            self.sftp_password = sftp_password
        if device_id:
            self.device_id = device_id
        if device_password:
            self.device_password = device_password
        if device_hardware_sn:
            self.device_hardware_sn = device_hardware_sn
        if device_hardware_model:
            self.device_hardware_model = device_hardware_model
        if device_log_dir:
            self.device_log_dir = device_log_dir
        if device_log_name:
            self.device_log_name = device_log_name
        if max_retries:
            self.max_retries = max_retries
        if outer_order_dict:
            self.outer_order_dict = outer_order_dict

        # 通过参数中的host和port生成server_url
        if host and port:
            self.server_url = f"ws://{host}:{port}/ws"
        else:
            self.server_url = None

        # 通过参数中的device_log_dir和device_log_name生成device_log_local_path,如果参数中没有指定device_log_dir则默认使用当前目录下的log文件夹
        if device_log_dir and device_log_name:
            # print("device_log_dir:", device_log_dir)
            # print("device_log_name:", device_log_name)
            self.device_log_local_path = os.path.join(device_log_dir, device_log_name)


# 暴露单例对象
config: Config = Config()
