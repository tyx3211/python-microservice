from sanic import Sanic
from websockets.legacy.client import WebSocketClientProtocol
import asyncio
import time

# 创建 用于得到距离某个时间戳的延时时间 的函数
# 传入参数：目标时间戳，延时时间（函数内获取当前时间戳）
# delay和timestamp都是秒级别的
def wait_time_from(timestamp:float,delay:float)->int:
    consumedTime = time.time() - timestamp
    return (delay - consumedTime)


MAX_PINGNUMS = 3 # 最大ping帧容忍数
PING_INTERVAL = 35  # 每 40 秒检查一次是否有ping帧(30s加上10s容忍时间(ping帧发送到接收的可容忍最大时间))

# 创建Sanic应用
app = Sanic("webSocketServer")

# 将异常反馈以json形式输出
app.config.FALLBACK_ERROR_FORMAT = "json"

@app.websocket("/ws")
async def ws_echo(request,ws:WebSocketClientProtocol):
    message = await asyncio.wait_for(ws.recv(),timeout=PING_INTERVAL) # 等待客户端的请求 message，超时就抛出异常
    
    # 检查message是业务消息还是ping帧
    if message == "ping":
        ws.send("pong") #回信pong帧
    else:
        # 处理业务逻辑
        ws.send(f"deal_business about {message}")
    