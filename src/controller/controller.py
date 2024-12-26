import asyncio
import asyncssh
import json
import time
import websockets
from websockets.legacy.client import WebSocketClientProtocol
from logger import myLogger
from execorder import order_exec

import getStatusInfo

# 边端设备至少记录了SN_MODEL对和password
device = {
    "hardware":{
        "sn":"SN123456789",
        "model":"ModelA"
    }
}

password = "test-password"

device_id = ""

# 服务端HOST以及端口配置

Host = ""
Port = None
server_url = ""

sftp_user = ""
sftp_password = ""

def safe_json_loads(json_string):
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        return None
    
############################################################
# 更完善的实现可加入 应答号

failureCount = 0

Flag = 0 # 变化为1代表可以延迟一次心跳执行（即替代了一次心跳）

latestBussinessTimeStamp = None # 除心跳外上次其它业务成功执行的时间戳，用于规范心跳延时时间

# 创建用于得到距离某个时间戳的延时时间的函数
# 传入参数：目标时间戳，延时时间（函数内获取当前时间戳）
# delay和timestamp都是秒级别的
def wait_time_from(timestamp:float,delay:float)->int:
    consumedTime = time.time() - timestamp
    return 0 if (delay - consumedTime) < 0 else (delay - consumedTime)

# 1. 处理登录鉴权
async def Login(ws:WebSocketClientProtocol):
    try:
        myLogger.info("try to login.")
        if device_id == "":
            await ws.send(json.dumps({"device_sn":device["hardware"]["sn"],"device_model":device["hardware"]["model"],"password":password}))
        else:
            await ws.send(json.dumps({"device_id":device_id}))
        result = await asyncio.wait_for(ws.recv(),timeout=6)
        result = safe_json_loads(result)
        if result["status"] == "fail":
            myLogger.info("failed to login,reason:" + result["message"])
            return False
        else:
            myLogger.info("successfully login.")
            return True
    except asyncio.TimeoutError:
        # 超时，直接退出，重新连接
        myLogger.info("failed to login:TimeOut.")
        return False
    except Exception as e:
        myLogger.info(f"failed to login:{e}.")
        return False



def get_events():
    Events = {
        "ping_pong":{"event":asyncio.Event(),"data":None},
        "receive_statusSend_response":{"event":asyncio.Event(),"data":None},
        # "receive_sendInstruction":{"event":asyncio.Event(),"data":None}
        "restart_confirm":{"event":asyncio.Event(),"data":None} # 这个Event仅用来针对重启指令，接收云端的确认重启回复
    }
    return Events

# 2.定义公共接收入口和分派函数
async def public_recv(ws:WebSocketClientProtocol,Events):
    while True:
        try:          
            response = await ws.recv()
            response_data = safe_json_loads(response)
            print(response_data)
            if response_data is None:
                print(response_data)
                continue
            # 启动分发（这里需要这么处理，而微服务端有更简单的处理方式的主要原因是：心跳和状态报文都是客户端主动发出的，且其延时都需要客户端去主动控制，按照服务端的方法放在一个协程里，会导致不能并发处理而阻塞）
            #        （服务端可以那么处理，主要是它其实只需要立即回信，延时是由客户端控制的）
            if response_data.get("type") == "ping_pong": # 接收到pong帧
                Events["ping_pong"]["data"] = response_data
                Events["ping_pong"]["event"].set()
            elif response_data.get("type") == "send_statusInfo_response": # 接收到对状态上传的回应
                Events["receive_statusSend_response"]["data"] = response_data
                Events["receive_statusSend_response"]["event"].set()
            elif response_data.get("type") == "give_order":                  # 接收到下达指令
                await execOrder(ws,response_data,Events["restart_confirm"])  #  注意由于指令执行是我们接收到的是请求，因此我们只需要立即给出回应即可。因此不需要管理所谓的延时，因此可以直接启动相应协程处理，不需要event。
                                                                             # 而由于心跳和状态我们接收到的是响应，我们若需要再发出下一次请求，需要主动延时处理，因此使用event。
            elif response_data.get("type") == "restart_confirm":
                Events["restart_confirm"]["data"] = response_data    # 注意由于python传递了Events的引用，因此后序set的Events["restart_confirm"]["event"]照样可以传递到相应execOrder处理模块下
                Events["restart_confirm"]["event"].set()
            else:
                pass
        except websockets.exceptions.ConnectionClosed: # 处理连接关闭异常
            break
        except Exception: #处理其它异常
            break

# 3.定义心跳处理函数
async def ping_pong(ws:WebSocketClientProtocol,event:asyncio.Event): # 注意心跳处理是宽容的，每一次收到云端回应都代表可以认为在线5s(延迟5s)，除非回应超时(此时立即执行)
    global failureCount,Flag                          # 相较之下，上传边端基础信息不是宽容的，因为总希望云端获得尽可能新的状态信息
    while True:
        try:
            while Flag == 1:
                Flag = 0
                await asyncio.sleep(wait_time_from(latestBussinessTimeStamp,5))
            await ws.send(json.dumps({"type":"ping_pong","Headers":{},"data":"ping"}))
            myLogger.info(f"send ping")
            await asyncio.wait_for(event["event"].wait(),timeout=3) # 发出ping到接收pong最多等3秒
            event["event"].clear()

            failureCount = 0 # 成功一次后失败次数就清零
            Flag = 0 # 观察后5s内是否有别的业务报文上传

            myLogger.info(f"successfully receive pong")
            await asyncio.sleep(5) # 等到了pong，就有5s的容许期
        except asyncio.TimeoutError:
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接
                myLogger.info(f"Timeout! No pong received within 5 seconds.")
                failureCount = 0
                break  # 退出业务发送，准备重连
            continue #超时，直接开始下次心跳发送
        except websockets.exceptions.ConnectionClosed: # 处理连接关闭异常
            break # 退出循环，停止业务
        except Exception as e:
            myLogger.error(f"Error during business: {e}")
            break  # 发生错误退出循环，停止业务

# 4.定义状态上传函数

async def uploadStatusInfo(ws:WebSocketClientProtocol,event:asyncio.Event):
    # 注意状态上传没有心跳那样的包容性，其15s间隔指的是发起请求的间隔固定15s
    global failureCount,Flag,latestBussinessTimeStamp
    while True:
        try:
            StatusInfo = getStatusInfo.collect_status_info()
            await ws.send(json.dumps({"type":"upload_status_info","Headers":{},"data":StatusInfo}))
            myLogger.info(f"Send StatusInfo")
            Flag = 1
            last_send_status = latestBussinessTimeStamp = time.time()

            await asyncio.wait_for(event["event"].wait(),timeout=3) # 一样最多等3秒
            event["event"].clear()
            failureCount = 0 # 成功一次后失败次数就清零
            myLogger.info(f"successfuly send StatusInfo")

            await asyncio.sleep(wait_time_from(last_send_status,15)) # 每隔15s发送状态报文
        except asyncio.TimeoutError:
            myLogger.info(f"Timeout! Failed to send StatusInfo.")
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接
                failureCount = 0
                break  # 退出业务发送，准备重连
            continue #超时，直接开始下次状态报文发送
        except websockets.exceptions.ConnectionClosed: # 处理连接关闭异常
            break # 退出循环，停止业务
        except Exception as e:
            myLogger.error(f"Error during business: {e}")
            break  # 发生错误退出循环，停止业务


# 5.定义接收指令并执行的函数

async def execOrder(ws:WebSocketClientProtocol,order_request,restartConfirmEvent:asyncio.Event):
    await order_exec(ws,order_request,restartConfirmEvent,{},Host,Port,sftp_user,sftp_password)


# 6.发起连接

async def connect():
    while True:
        try:
            myLogger.info("Ready to connect to Server.")
            async with websockets.connect(server_url) as ws: # 发起webSocket连接，连接成功后webSocket对象引用给到ws
                myLogger.info("successfully connect to Server.")
                # 先鉴权
                if await Login(ws) is False:
                    continue
                # 写事件分派
                events = get_events()
                asyncio.create_task(public_recv(ws,events)) # 异步添加公共接受点任务（在其中也解决了对指令执行的调动）
                asyncio.create_task(uploadStatusInfo(ws,events["receive_statusSend_response"])) # 异步添加上传状态信息任务   
                await ping_pong(ws,events["ping_pong"]) # 开始ping-pong 心跳，心跳结束即进入重连
        except Exception as e:
            myLogger.error(f"Error: {e},disconnect to Server.")
        myLogger.info("Server Offline. try-reconnect")


# 7. 暴露给外界自定义功能

async def startControllerBasicApp(host=None,port=None,sftpUser=None,sftpPassword=None,outer_order_list={}):
    ####
    global server_url,Host,Port,sftp_user,sftp_password
    Host = host
    Port = port
    server_url = f"ws://{host}:{port}/ws"
    sftp_user = sftpUser
    sftp_password = sftpPassword

    ####
    asyncio.run(connect())

if __name__ == "__main__":
    Host = "127.0.0.1"
    Port = 9090
    server_url = "ws://127.0.0.1:9090/ws"
    sftp_user = ""
    sftp_password = ""
    asyncio.run(connect())