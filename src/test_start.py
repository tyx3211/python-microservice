from controller.controller import startControllerBasicApp
from User import user,password # 这个实际不需要

Host = "47.97.81.99"

Port = 9090

sftp_user = user # 这里替换为实际的云服务器sftp用户名

sftp_password = password # 这里替换为实际的云服务器sftp用户密码

startControllerBasicApp(
    host=Host,
    port=Port,
    sftpUser=sftp_user,
    sftp_password=sftp_password
)