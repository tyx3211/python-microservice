# 客户端向服务端发送ping帧模式的demo ，这个是客户端部分

import websockets
import asyncio
from websockets.legacy.client import WebSocketClientProtocol
import time
import json # 用于获取json反序列化内容得到字典

# 创建 用于得到距离某个时间戳的延时时间 的函数
# 传入参数：目标时间戳，延时时间（函数内获取当前时间戳）
# delay和timestamp都是秒级别的
def wait_time_from(timestamp:float,delay:float)->int:
    consumedTime = time.time() - timestamp
    return 0 if (delay - consumedTime) < 0 else (delay - consumedTime)
 

SERVER_URI = "ws://localhost:8000/ws"  # 服务端 WebSocket 地址
MAX_PONGNUMS = 3 # 最大pong帧容忍数
PING_INTERVAL = 30  # 每 30 秒发送一次 ping
TIMEOUT = 10  # 每次等待 pong 的超时时间

failureCount = 0 # 失败次数标记

#定义整体任务分派逻辑...

# 1.获取任务分派事件列表
def get_events():
    events = {
        "ping_pong":{"recv":asyncio.Event(),"data":None},
        "business":{"recv":asyncio.Event(),"data":None}
    }
    return events

# 2.定义公共接收入口和分派函数
async def public_recv(ws:WebSocketClientProtocol,events):
    while True:
        try:          
            response = await ws.recv()
            response_data = json.loads(response)
            
            # 启动分发
            events[response_data["type"]]["data"] = response_data
            events[response_data["type"]]["recv"].set()
        except websockets.exceptions.ConnectionClosed: # 处理连接关闭异常
            break
        except Exception: #处理其它异常
            break

# 定义心跳处理函数
async def ping_pong(ws:WebSocketClientProtocol,event): # 使用type-hint
    global failureCount # 声明使用全局变量failureCount
    while True:
        try:
            # 每隔PING_INTERVAL发送ping帧
            await ws.send("ping")
            last_ping = time.time() # 记录完发送ping帧的时间戳
            print("Send ping to Server.")
            
            # 使用 await asyncio.wait_for 设置超时，如果 10 秒内没有收到 pong，就会超时
            await asyncio.wait_for(event["recv"].wait(), timeout=TIMEOUT)
            event["recv"].clear()
            failureCount = 0
            pong = event["data"]
            
            print(f"receive {pong} at {time.time()}") # 日志消息
            
            if pong["data"] == "pong": #检测pong帧合法性
                print("Received pong from server.")
            else:
                print("Unexpected message received:", pong)
                
            await asyncio.sleep(wait_time_from(last_ping,PING_INTERVAL)) # 若10s内正常收到pong，据上次发送ping帧30s的时间再发送ping
            
        except asyncio.TimeoutError: # 处理超时异常
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接，并准备重连
                print(f"Timeout! No pong received within {TIMEOUT} seconds.")
                failureCount = 0
                break  # 退出这次ping-pong，交给重连逻辑
            await asyncio.sleep(PING_INTERVAL - TIMEOUT) # 失败了，等PING_INTERVAL - TIMEOUT时间，也就是据上次发送ping帧30s的时间再发送ping
        except Exception as e:
            print(f"Error during ping-pong: {e}")
            break  # 发生错误退出循环

# 模拟sender业务逻辑函数，用它来替代一次心跳
async def business_main(ws:WebSocketClientProtocol,event):
    global failureCount
    while True:
        try:
            await asyncio.sleep(3) # 每隔3s 发送业务请求
            await ws.send("business-request")
            
            # 使用 await asyncio.wait_for 设置超时，如果 10 秒内没有收到 response，就会超时
            await asyncio.wait_for(event["recv"].wait(), timeout=TIMEOUT)
            event["recv"].clear()
            failureCount = 0
            response = event["data"]
            
            print(f"receive {response} at {time.time()}") #日志消息
             
        except asyncio.TimeoutError:
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接，并准备重连
                print(f"Timeout! No pong received within {TIMEOUT} seconds.")
                failureCount = 0
                break  # 退出业务发送，交给重连逻辑
            continue #回信超时，开始下次业务数据发送
        except websockets.exceptions.ConnectionClosed: # 处理连接关闭异常
            break # 退出循环，停止业务
        except Exception as e:
            print(f"Error during business: {e}")
            break  # 发生错误退出循环

# 定义连接/重连函数
async def connect():
    while True:
        try:
            async with websockets.connect(SERVER_URI) as ws: # 发起webSocket连接，连接成功后webSocket对象引用给到ws
                # 先写事件分派
                events = get_events()
                asyncio.create_task(public_recv(ws,events)) # 异步添加公共接受点任务
                    
                asyncio.create_task(business_main(ws,events["business"])) # 异步添加任务 处理 业务逻辑
                await ping_pong(ws,events["ping_pong"]) # 开始ping-pong 心跳
                # 如果 ping-pong心跳结束，那么客户端认为服务端断线(或者服务端主动断开了webSocket连接)，这个时候重连
                await ws.close() # 确保webSocket关闭(已经关闭的话，该行无效果) ， 然后进入下一轮循环(重连)
        except Exception as e:
            print(f"Error during ping-pong: {e}")
        print("Server Offline. try-reconnect")
    
#定义总体接收函数
    
if __name__ == "__main__":
    asyncio.run(connect()) # 启动连接/重连