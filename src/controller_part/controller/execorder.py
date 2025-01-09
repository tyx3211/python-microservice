import asyncio
import asyncssh
import json
import time
import websockets

from websockets.legacy.client import WebSocketClientProtocol

import os
import sys


from controller.logger import myLogger
from controller.sftp_upload import sftp_upload_log
from controller.config import config

async def inner_order_exec(ws:WebSocketClientProtocol, order_request, restartConfirmEvent:asyncio.Event):
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
        try:
            # print(config.host,config.port,config.sftp_host,config.sftp_port,config.sftp_username,config.sftp_password) # 测试用，打印sftp配置信息
            if await sftp_upload_log(device_id, config.device_log_local_path, remote_dir,config.sftp_host, config.sftp_port, config.sftp_username, config.sftp_password) is False:
                await ws.send(json.dumps({"type":"upload_instruction_result","status":"fail","Headers":{"message":"fail to upload log."},"data":{}}))
            else:
                await ws.send(json.dumps({"type":"upload_instruction_result","status":"success","Headers":{"message":"successfully upload log."},"data":{}}))
        except Exception:
            pass

async def outer_order_exec(ws:WebSocketClientProtocol, order_request):
    if order_request["Headers"]["order_type"] not in config.outer_order_dict:
        await ws.send(json.dumps({"type":"upload_instruction_result","status":"fail","Headers":{"message":"order not in config"},"data":{}}))
    try:
        execFunc = config.outer_order_dict[order_request["Headers"]["order_type"]]
        if "params" not in order_request["data"] or (not isinstance(order_request["data"]["params"],dict)):
            execFunc()
        elif len(order_request["data"]["params"]) == 0:
            execFunc()
        else:
            execFunc(**order_request["data"]["params"])
            myLogger.info("successfully exec order.")
        await ws.send(json.dumps({"type":"upload_instruction_result","status":"success","Headers":{"message":"successfully exec order."},"data":{}}))
    except Exception as e:
        await ws.send(json.dumps({"type":"upload_instruction_result","status":"fail","Headers":{"message":f"Error in exec order: {e}"},"data":{}}))

async def order_exec(ws:WebSocketClientProtocol,order_request,restartConfirmEvent:asyncio.Event):
    myLogger.info("receive instruction from Server:" + str(order_request["Headers"]["order_type"]))
    if order_request["Headers"]["isInner"] == True:
        await inner_order_exec(ws,order_request, restartConfirmEvent)
    else:
        await outer_order_exec(ws,order_request)