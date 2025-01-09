import asyncio
import asyncssh
import json
import time
import websockets
from websockets.legacy.client import WebSocketClientProtocol

from controller.config import config,Config
from controller.execorder import order_exec
from controller.logger import myLogger,SetLogMessage
from controller import getStatusInfo

Ws = None # 用来检测当前连接是否最新（Ws保存最新连接）

# 边端设备至少记录了SN_MODEL对和password，因此可以直接从config中获取

# 服务端HOST以及端口配置

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
        if config.device_id == None:
            await ws.send(json.dumps({"device_sn":config.device_hardware_sn,"device_model":config.device_hardware_model,"password":config.device_password}))
        else:
            await ws.send(json.dumps({"device_id":config.device_id,"password":config.device_password}))
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
            print(response_data) # 打印接收到的消息，用于调试
            # 启动分发（这里需要这么处理，而微服务端有更简单的处理方式的主要原因是：心跳和状态报文都是客户端主动发出的，且其延时都需要客户端去主动控制，按照服务端的方法放在一个协程里，会导致不能并发处理而阻塞）
            #        （服务端可以那么处理，主要是它其实只需要立即回信，延时是由客户端控制的）
            if response_data.get("type") == "ping_pong": # 接收到pong帧
                Events["ping_pong"]["data"] = response_data
                Events["ping_pong"]["event"].set()
            elif response_data.get("type") == "send_statusInfo_response": # 接收到对状态上传的回应
                Events["receive_statusSend_response"]["data"] = response_data
                Events["receive_statusSend_response"]["event"].set()
            elif response_data.get("type") == "give_order":
                # print("hello")                 # 接收到下达指令
                asyncio.create_task(execOrder(ws,response_data,Events["restart_confirm"]))  # 特别注意！！！ ： 由于在execOrder模块下，我们可能会有await确认的操作（如Restart，确认需要服务端再发信），因此一定不能await调用构成依赖！否则会导致Restart依赖服务端确认才能执行完（否则超时），但是接收服务端确认的public_recv又依赖execOrder结果，导致Restart只能超时，因此这里应该异步启动新任务
                                                                             #  注意由于指令执行是我们接收到的是请求，因此我们只需要立即给出回应即可。因此不需要管理所谓的延时，因此可以直接启动相应协程处理，不需要event。
                                                                             # 而由于心跳和状态我们接收到的是响应，我们若需要再发出下一次请求，需要主动延时处理，因此使用event。
            elif response_data.get("type") == "restart_confirm":
                Events["restart_confirm"]["data"] = response_data    # 注意由于python传递了Events的引用，因此后序set的Events["restart_confirm"]["event"]照样可以传递到相应execOrder处理模块下
                Events["restart_confirm"]["event"].set()
            else:
                pass
        except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError): # 处理连接关闭异常
            break
        except Exception: #处理其它异常
            break

# 3.定义心跳处理函数
async def ping_pong(ws:WebSocketClientProtocol,event:asyncio.Event):
    global failureCount,Flag                          
    while True:
        try:
            while Flag == 1:
                Flag = 0
                await asyncio.sleep(wait_time_from(latestBussinessTimeStamp,5))
            
            # 因为网络波动客观存在，因此总是设置 “发起ping请求间隔” 为5s
            await ws.send(json.dumps({"type":"ping_pong","Headers":{},"data":"ping"}))
            last_send_ping = time.time()
            myLogger.info(f"send ping")
            
            await asyncio.wait_for(event["event"].wait(),timeout=3) # 发出ping到接收pong最多等3秒
            event["event"].clear()

            failureCount = 0 # 成功一次后失败次数就清零
            Flag = 0 # 观察后5s内是否有别的业务报文上传

            myLogger.info(f"successfully receive pong")
            await asyncio.sleep(wait_time_from(last_send_ping,5)) # 等到了pong，就有5s的容许期
        except asyncio.TimeoutError:
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接
                myLogger.info(f"Timeout! No pong received within 5 seconds.")
                failureCount = 0
                break  # 退出业务发送，准备重连
            continue #超时，直接开始下次心跳发送
        except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError): # 处理连接关闭异常
            break # 退出循环，停止业务
        except Exception as e:
            myLogger.error(f"Error during business: {e}")
            break  # 发生错误退出循环，停止业务

# 4.定义状态上传函数

async def uploadStatusInfo(ws:WebSocketClientProtocol,event:asyncio.Event):
    # 发起请求间隔为15s
    global failureCount,Flag,latestBussinessTimeStamp,Ws
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
            myLogger.info(f"successfully receive response of statusSend")

            await asyncio.sleep(wait_time_from(last_send_status,15)) # 每隔15s发送状态报文
        except asyncio.TimeoutError:
            if ws != Ws: # 若连接断开，则不再发送状态报文(只需对非心跳活动检测，因为是由ping_pong决定断开的，这一步是为了在断开后正确析构未释放的资源)
                break
            myLogger.info(f"Timeout! Failed to send StatusInfo.")
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接
                failureCount = 0
                break  # 退出业务发送，准备重连
            continue #超时，直接开始下次状态报文发送
        except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError): # 处理连接关闭异常
            break # 退出循环，停止业务
        except Exception as e:
            myLogger.error(f"Error during business: {e}")
            break  # 发生错误退出循环，停止业务


# 5.定义接收指令并执行的函数

async def execOrder(ws:WebSocketClientProtocol,order_request,restartConfirmEvent:asyncio.Event):
    try: 
        await order_exec(ws,order_request,restartConfirmEvent)
    except Exception as e:
        # print(e)
        pass


# 6.发起连接

async def connect():
    global failureCount,Ws,Flag
    retries = 0
    while retries < config.max_retries:
        try:
            myLogger.info("Ready to connect to Server.")
            async with websockets.connect(config.server_url) as ws: # 发起webSocket连接，连接成功后webSocket对象引用给到ws
                myLogger.info("successfully connect to Server.")
                Ws = ws # 保存最新连接
                failureCount = 0 # 重置失败次数
                Flag = 0 # 重置Flag
                
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
        myLogger.info("Server Offline. try-reconnect 10s later.")
        retries += 1
        await asyncio.sleep(10) # 重连间隔10s


# 7. 暴露给外界自定义功能

# startControllerBasicApp要有和Config类一样的参数，以便于外部调用时传入配置信息

def startControllerBasicApp(host=None, port=None, sftp_host=None, sftp_port=None, sftp_username=None, sftp_password=None, device_id=None, device_password=None, device_hardware_sn=None, device_hardware_model=None, device_log_dir=None, device_log_name=None, max_retries=None, outer_order_dict={}):
    global config
    config.Set(host=host, port=port, sftp_host=sftp_host, sftp_port=sftp_port, sftp_username=sftp_username, sftp_password=sftp_password, device_id=device_id, device_password=device_password, device_hardware_sn=device_hardware_sn, device_hardware_model=device_hardware_model, device_log_dir=device_log_dir, device_log_name=device_log_name, max_retries=max_retries, outer_order_dict=outer_order_dict)
    SetLogMessage(myLogger,config.device_log_dir,config.device_log_local_path) # 配置完config后再配置日志
    asyncio.run(connect()) # 启动连接