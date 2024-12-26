import asyncio
import asyncssh
import os
from logger import myLogger

async def sftp_upload_log(device_id: str, log_file: str, remote_dir: str, sftp_host: str, sftp_port: int, sftp_username: str, sftp_password: str):
    """
    上传日志到远程 SFTP 服务器。

    :param device_id: 设备 ID，用于文件命名。
    :param log_file: 本地日志文件路径。
    :param remote_dir: 远程目录路径。
    :param sftp_host: SFTP 服务器地址。
    :param sftp_port: SFTP 端口号。
    :param sftp_username: SFTP 用户名。
    :param sftp_password: SFTP 密码。
    """
    # 确保日志目录和文件存在，不存在就创建
    if not os.path.exists(log_file):
        with open(log_file, 'w') as file:
            pass

    remote_file = os.path.join(remote_dir, f"{device_id}.log")
    
    # 使用 asyncssh 执行 SFTP 上传操作
    try:
        myLogger.info("try to upload log.")
        async with asyncssh.connect(sftp_host, port=sftp_port, username=sftp_username, password=sftp_password) as conn:
            sftp = await conn.start_sftp_client()
            # 上传文件
            await sftp.put(log_file, remote_file)
            myLogger.info(f"Successfully uploaded {log_file} to {remote_file}")
            return True
    except Exception as e:
        myLogger.error(f"Failed to upload log file {log_file}: {e}")
        return False
