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
#   - outer_order_dict : 外部指令字典(默认[])

class Config:
    def __init__(self, host=None, port=None, sftp_host=None, sftp_port=None, sftp_username=None, sftp_password=None, device_id=None, device_password=None, device_hardware_sn=None, device_hardware_model=None, outer_order_dict=[]):
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
        self.outer_order_dict = outer_order_dict
        
        # 通过参数中的host和port生成server_url
        if host and port:
            self.server_url = f"ws://{host}:{port}/ws"
        else:
            self.server_url = None
        
# 暴露单例对象
config:Config = Config()