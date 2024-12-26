import asyncio
import asyncssh
import json
import time
import websockets

from websockets.legacy.client import WebSocketClientProtocol

import os
import sys


from logger import myLogger
from sftp_upload import sftp_upload_log

HOST = None
PORT = None
SFTPUSER = None
SFTPPASSWORD = None

async def inner_order_exec(ws:WebSocketClientProtocol,order_request,restartConfirmEvent:asyncio.Event,outer_order_dict):
    if order_request["Headers"]["order_type"] == "restart":
        myLogger.info("request Server Restart Confirm.")
        await ws.send(json.dumps({"type":"upload_instruction_result","status":"success","Headers":{"message":"wait Server Confirm"},"data":{}}))
        try:
            await asyncio.wait_for(restartConfirmEvent["event"].wait(),timeout = 20) # 对于重启指令，额外有一个确认步骤，但是最多等3s
            myLogger.info("Receive Restart Confirm:start to Restart.")
        except Exception:
            myLogger.info("start Restart but failed to receive Server Confirm.")
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    elif order_request["Headers"]["order_type"] == "upload_log":
        device_id = order_request["data"]["device_id"]
        remote_dir = order_request["data"]["remote_dir"]
        dir = os.path.dirname(__file__)
        log_file = os.path.join(dir,"log","app.log")
        try:
            if await sftp_upload_log(device_id,log_file,remote_dir,HOST,22,SFTPUSER,SFTPPASSWORD) is False:
                await ws.send(json.dumps({"type":"upload_instruction_result","status":"fail","Headers":{"message":"fail to upload log."},"data":{}}))
            else:
                await ws.send(json.dumps({"type":"upload_instruction_result","status":"success","Headers":{"message":"successfully upload log."},"data":{}}))
        except Exception:
            pass

async def outer_order_exec(ws:WebSocketClientProtocol,order_request,restartConfirmEvent:asyncio.Event,outer_order_dict):
    pass

async def order_exec(ws:WebSocketClientProtocol,order_request,restartConfirmEvent:asyncio.Event,outer_order_dict,host,port,sftp_user,sftp_password):
    global HOST,PORT,SFTPUSER,SFTPPASSWORD
    HOST = host
    PORT = port
    SFTPUSER = sftp_user
    SFTPPASSWORD = sftp_password
    myLogger.info("receive instruction from Server:" + str(order_request["Headers"]["order_type"]))
    if order_request["Headers"]["isInner"] == True:
        await inner_order_exec(ws,order_request,restartConfirmEvent,outer_order_dict)
    else:
        await outer_order_exec(ws,order_request,restartConfirmEvent,outer_order_dict)