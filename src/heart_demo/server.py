from sanic import Sanic
from websockets.legacy.client import WebSocketClientProtocol
import asyncio
import time
import websockets
import json

# 创建 用于得到距离某个时间戳的延时时间 的函数
# 传入参数：目标时间戳，延时时间（函数内获取当前时间戳）
# delay和timestamp都是秒级别的
def wait_time_from(timestamp:float,delay:float)->int:
    consumedTime = time.time() - timestamp
    return (delay - consumedTime)


MAX_PINGNUMS = 3 # 最大ping帧容忍数
TIMEOUT = 35  # 每 40 秒检查一次是否有ping帧(30s加上10s容忍时间(ping帧发送到接收的可容忍最大时间))
failureCount = 0

# 创建Sanic应用
app = Sanic("webSocketServer")

# 将异常反馈以json形式输出
app.config.FALLBACK_ERROR_FORMAT = "json"

@app.websocket("/ws")
async def ws_echo(request,ws:WebSocketClientProtocol):
    global failureCount # 声明全局变量,先只考虑服务端收数据并回信
    while True:
        try:
            message = await asyncio.wait_for(ws.recv(),timeout=TIMEOUT) # 等待客户端的请求 message，超时就抛出异常
            print(f"receive {message} at {time.time()}") # 日志消息
            # 检查message是业务消息还是ping帧
            if message == "ping":
                await ws.send(json.dumps({"type":"ping_pong","data":"pong"})) #回信pong帧
            else:
                # 处理业务逻辑
                await ws.send(json.dumps({"type":"business","data":"deal_request"}))
        except asyncio.TimeoutError:
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接，并准备重连
                print(f"Timeout! No pong received within {TIMEOUT} seconds.")
                failureCount = 0
                await ws.close() #关闭后等待客户端重连
                break  # 退出业务发送，交给客户端重连
            continue #超时，开始下次等待
        except websockets.exceptions.ConnectionClosed: # 处理连接关闭异常
            await ws.close()
            break # 退出循环，停止业务
        except Exception as e:
            await ws.close()
            print(f"Error during business: {e}")
            break  # 发生错误退出循环

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8000)