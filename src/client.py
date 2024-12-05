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
    return (delay - consumedTime)


SERVER_URI = "ws://localhost:8000/ws"  # 服务端 WebSocket 地址
MAX_RETRIES = 5  # 最大重连次数
MAX_PONGNUMS = 3 # 最大pong帧容忍数
PING_INTERVAL = 30  # 每 30 秒发送一次 ping
TIMEOUT = 10  # 每次等待 pong 的超时时间

failureCount = 0 # 失败次数标记

#定义整体任务分派逻辑...

# 定义心跳处理函数
async def ping_pong(ws:WebSocketClientProtocol): # 使用type-hint
    global failureCount # 声明使用全局变量failureCount
    while True:
        try:
            # 每隔PING_INTERVAL发送ping帧
            await ws.send("ping")
            last_ping = time.time() # 记录完发送ping帧的时间戳
            print("Send ping to Server.")
            
            # 使用 await asyncio.wait_for 设置超时，如果 10 秒内没有收到 pong，就会超时
            pong = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
            
            if pong == "pong": #检测pong帧合法性
                print("Received pong from server.")
            else:
                print("Unexpected message received:", pong)
                
            await asyncio.sleep(wait_time_from(last_ping,PING_INTERVAL)) # 若10s内正常收到pong，据上次发送ping帧30s的时间再发送ping
            
        except asyncio.TimeoutError: # 处理超时异常
            failureCount += 1 # 失败次数递增
            if failureCount == 3: # 失败三次断开连接，并准备重连
                print(f"Timeout! No pong received within {TIMEOUT} seconds.")
                failureCount = 0
                break  # 退出这次ping-pong，交给重连逻辑
            await asyncio.sleep(PING_INTERVAL - TIMEOUT) # 失败了，等PING_INTERVAL - TIMEOUT时间，也就是据上次发送ping帧30s的时间再发送ping
        except Exception as e:
            print(f"Error during ping-pong: {e}")
            break  # 发生错误退出循环

# 模拟sender业务逻辑函数，用它来替代一次心跳
async def business_main(ws:WebSocketClientProtocol):
    while True:
        try:
            await asyncio.sleep(3) # 每隔3s 发送业务请求
            await ws.send("business-request")
            response = await ws.recv()
            print(response)
            
        except websockets.exceptions.ConnectionClosed: # 处理连接关闭异常
            break # 退出循环，停止业务
        except Exception as e:
            print(f"Error during business: {e}")
            break  # 发生错误退出循环

# 定义连接/重连函数
async def connect():
    retries = 0 # 定义重连计数
    while retries < MAX_RETRIES:
        try:
            async with websockets.connect(SERVER_URI) as ws: # 发起webSocket连接，连接成功后webSocket对象引用给到ws
                                                        #需要添加任务分派逻辑
                asyncio.create_task(business_main(ws)) # 异步添加任务 处理 业务逻辑
                await ping_pong(ws) # 开始ping-pong 心跳
                # 如果 ping-pong心跳结束，那么客户端认为服务端断线(或者服务端主动断开了webSocket连接)，这个时候重连
                await ws.close() # 确保webSocket关闭(已经关闭的话，该行无效果) ， 然后进入下一轮循环(重连)
                retries+=1 # 重连计数增加
        except Exception as e:
            print(f"Error during ping-pong: {e}")
    print("Server Offline.")
    
#定义总体接收函数
    
if __name__ == "__main__":
    asyncio.run(connect()) # 启动连接/重连