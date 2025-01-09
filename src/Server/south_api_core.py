"""
南向接口核心实现
"""

import asyncio
import json
import bcrypt
import websockets
from sanic import response
from websockets.legacy.client import WebSocketClientProtocol
from Database_OP import deviceOP,groupOP,relationOP


device_websocket_map = {} # 用于保存设备和其对应的webSocket连接的字典,并顺带保存和该device和当前webSocket关联的giveOrderEvent

def safe_json_loads(json_string):
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        return None

def freeResource(device_id):
    if device_id in device_websocket_map:
        del device_websocket_map[device_id]
        del DevicesStatusInfo[device_id]
        del DeviceFailureCount[device_id]

# 1.登录鉴权，可基于ID或SN_MODEL对或密码鉴权
async def loginCheck(ws:WebSocketClientProtocol,result):
    try:
        loginInfo = await asyncio.wait_for(ws.recv(),timeout=5)
        loginInfo = safe_json_loads(loginInfo)
        if loginInfo is False:
            await ws.send(json.dumps({"status":"fail","message":"Invalid Json"}))
            return False
        if "password" not in loginInfo:
            await ws.send(json.dumps({"status":"fail","message":"Not provide password"}))
            return False
        if "device_id" in loginInfo:
            try:
                queryResult = await deviceOP.query(device_id=loginInfo["device_id"])
            except Exception as e:
                await ws.send(json.dumps({"status":"fail","message":str(e)}))
                return False
            if bcrypt.checkpw(loginInfo["password"].encode("utf-8"),queryResult["password"].encode("utf-8")) is False:
                await ws.send(json.dumps({"status":"fail","message":"password Not Correct"}))
                return False
            else:
                await ws.send(json.dumps({"status":"success","data":{"device_id":queryResult["device_id"]}}))
                result["device_id"] = queryResult["device_id"]
                return True
        elif ("device_sn" in loginInfo) and ("device_model" in loginInfo):
            try:
                queryResult = await deviceOP.query(SN_Model=(loginInfo["device_sn"],loginInfo["device_model"]))
                # print(queryResult)
            except Exception as e:
                await ws.send(json.dumps({"status":"fail","message":str(e)}))
                return False
            if bcrypt.checkpw(loginInfo["password"].encode("utf-8"),queryResult["password"].encode("utf-8")) is False:
                await ws.send(json.dumps({"status":"fail","message":"password Not Correct"}))
                return False
            else:
                await ws.send(json.dumps({"status":"success","data":{"device_id":queryResult["device_id"]}}))
                result["device_id"] = queryResult["device_id"]
                return True
        else:
            await ws.send(json.dumps({"status":"fail","message":"Missing required Parameters!"}))
            return False
    except asyncio.TimeoutError:
        await ws.send(json.dumps({"status":"fail","message":"TimeOut."}))
        return False
    except Exception as e:
        # print(e)
        await ws.send(json.dumps({"status":"fail","message":"Unknown Error"}))
        return False


###################################################################################

DevicesOnlineState = {} # 设备是否在线信息

DevicesStatusInfo = {} # 全局在线设备的状态信息字典

DeviceFailureCount = {} # 心跳失败计数统计字典，初值为0，边端状态上传未接收到或者边端指令回应未接收到亦可贡献，至三可判断边端设备断线
# 注意，业务报文引起的替代心跳发送的操作是由边端完成的，由边端决定心跳报文的延迟量

###### 和北向接口相关：定义查询设备当前状态信息函数#######

def queryDeviceStatusInfo(device_id):
    if (device_id not in DevicesStatusInfo) or (device_id not in DevicesOnlineState):
        return None
    Result =  {"device_id":device_id}
    Result.update(DevicesStatusInfo[device_id])
    Result.update({"dev_state":DevicesOnlineState[device_id]})
    return Result


######################################################

# 获取各任务分派事件列表
def get_events():
    Events = {
        # "ping_pong":{"event":asyncio.Event(),"data":None},
        # "receive_status_info":{"event":asyncio.Event(),"data":None},
        "receive_instruction_result":{"event":asyncio.Event(),"data":None}
    }
    return Events

async def TransDeviceState(device_id,ToState): # 由于在线状态其实是即时的，不需要持久化保存，其实可以去除数据库表中的dev_state以提高效率（以后的优化考虑）
    DevicesOnlineState[device_id] = ToState
    dev_state_trans = [None] * 13
    dev_state_trans[11] = ToState
    try:
        await deviceOP.update(device_id,tuple(dev_state_trans))
    except Exception:
        pass

# 定义公共接收入口和分派函数，注意到，由于我们在边端经常使用一次业务报文发送替代一次心跳，来表明边端对云端有整体活跃请求（不管这个请求是心跳还是业务报文），因此对于failureCount的计算应该以来自边端的整体请求衡量，即在public_recv中计算failureCount即可
    # 注意到，由于延迟机制，心跳总是相比上一个请求最多延迟5s发送（除非这5s内又有新的请求，因此不妨将宽容度制定为7.5,5,5）
async def public_recv(ws:WebSocketClientProtocol,Events,device_id):
    while True:
        try:
            if DeviceFailureCount[device_id] == 0:
                t = (5 + 2.5)
            else:
                t = 5.5  
            response = await asyncio.wait_for(ws.recv(),timeout=10)
            response_data = safe_json_loads(response)
            print(response_data) # 打印接收到的报文，仅用于调试
            if response_data is None:
                continue
            ##########考虑状态转换
            if DevicesOnlineState[device_id]!= "online":
                await TransDeviceState(device_id,"online")
            #####################
            # 启动分发（注意到由于不像边端一样有互相影响的延时机制，而且是接收到边端请求就马上回应给边端，因此心跳和状态报文的回信可以这样简化处理）
            if response_data.get("type") == "ping_pong":
                await ws.send(json.dumps({"type":"ping_pong","Headers":{},"data":"pong"})) # 处理心跳

            elif response_data.get("type") == "upload_status_info":
                DevicesStatusInfo[device_id] = response_data["data"]
                await ws.send(json.dumps({"type":"send_statusInfo_response","Headers":{},"data":{}})) # 处理状态报文回信

            # 但是依旧注意到指令下达很特殊，此时接收到的不是边端请求，而已经是边端对指令执行的回应，将回应结果传递给请求协程giveOrder依旧需要Event处理
            elif response_data.get("type") == "upload_instruction_result":
                Events["receive_instruction_result"]["data"] = response_data
                Events["receive_instruction_result"]["event"].set()

            else:
                pass
        except asyncio.TimeoutError:
            if DevicesOnlineState[device_id]!= "Unknown":
                await TransDeviceState(device_id,"Unknown")
            DeviceFailureCount[device_id] += 1 # 失败次数递增
            if DeviceFailureCount[device_id] >= 3: # 失败三次断开连接，并等待边端重连
                print(f"Timeout! No ping received within 5 seconds.")
                freeResource(device_id)
                await TransDeviceState(device_id,"offline")
                break  # 退出业务发送，交给客户端重连
            continue #超时，开始下次等待
        except (websockets.exceptions.ConnectionClosed,asyncio.CancelledError): # 处理连接关闭异常
            freeResource(device_id)
            await TransDeviceState(device_id,"offline")
            break
        except Exception: #处理其它异常
            freeResource(device_id)
            await TransDeviceState(device_id,"offline")
            break

##############################################################################

# 定义指令下发函数，可供北向接口使用

devices_instruction_dealing = {} # 记录哪个设备正在处理指令的字典

async def giveOrder(device_id,order):
    if (device_id not in DevicesOnlineState) or (DevicesOnlineState[device_id] == "offline"):
        return response.json({"status":"fail","message":"Device is offline!"})
    if DevicesOnlineState[device_id] == "Unknown":
        return response.json({"status":"fail","message":"Device state is Unknown!"})
    
    if ((device_id in devices_instruction_dealing) and devices_instruction_dealing.get(device_id) == True): # 对单设备的并发控制
        return response.json({"status":"fail","message":"Device busy!"})
    devices_instruction_dealing[device_id] = True
    # print(device_websocket_map)
    Ws = device_websocket_map[device_id]["ws"]
    ReceiveResultEvent = device_websocket_map[device_id]["receiveOrderResultEvent"]

    # 下达指令
    try:
        await Ws.send(json.dumps(order))
        await asyncio.wait_for(ReceiveResultEvent["event"].wait(),timeout=3) # 当边端回应时可继续，但不能超过10s，否则认为这次指令下达失败
        ReceiveResultEvent["event"].clear()

        if order["Headers"]["order_type"] == "restart": # 对于重启，额外确认
            try:
                await Ws.send(json.dumps({"type":"restart_confirm","Headers":{},"data":{}}))
            except Exception as e:
                pass

        result = ReceiveResultEvent["data"]
        if result["status"] == "success":
            devices_instruction_dealing[device_id] = False
            return response.json({"status":"success","data":{}})
        else:
            devices_instruction_dealing[device_id] = False
            # print(result)
            return response.json({"status":"fail","message":result["Headers"]["message"]})
    except Exception:
        devices_instruction_dealing[device_id] = False
        return response.json({"status":"fail","message":"Unknown Error!"})
    

async def Ws_Serve_Core(ws:WebSocketClientProtocol):
    # 先登录鉴权
    result = {} #传出参数
    if await loginCheck(ws,result) is False:
        return
    
    # 登录成功后，做准备工作
    Events = get_events()
    device_id = result["device_id"]
    await TransDeviceState(device_id,"online")
    device_websocket_map[device_id] = {"ws":ws,"receiveOrderResultEvent":Events["receive_instruction_result"]}
    DeviceFailureCount[device_id] = 0 # 初始化心跳失败计数
    
    # 再正式启动南向接口服务   
    await public_recv(ws,Events,device_id) # 启动心跳、状态报文、以及指令下达的公共处理模块