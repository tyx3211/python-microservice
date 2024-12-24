from sanic import Sanic
from sanic.response import json as JSON
import json
from sanic.exceptions import ServerError
from websockets.legacy.client import WebSocketClientProtocol
import asyncio
import aiomysql

# 全局连接池
pool:aiomysql.Pool = None

# 创建Sanic应用
app = Sanic("webSocketServer")

# 将异常反馈以json形式输出
app.config.FALLBACK_ERROR_FORMAT = "json"

async def connect_to_database():
    global pool
    # 初始化连接池
    pool = await aiomysql.create_pool(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="root",
        db="mytest",
        minsize=15, # 最小(基础)连接数
        maxsize=100,  # 可以设置最大连接数
    )
    
@app.listener("before_server_start")
async def setup_db(app,loop):
    # 服务正式启动前先连接数据库
    await connect_to_database()
    
@app.listener("after_server_stop")
async def setup_db(app,loop):
    pool.close()
    await pool.wait_closed()

@app.post("/query")
async def Deal_Query(request):
    data = request.json
    # 事务需要连接池分配连接(一般直接复用)，保证数据库可以区分不同事务，再根据MVVC保证不同事务独立性（可以看java对于多线程操作事务时对连接池的要求，并发都要这样的）
    # 这里我们采用默认的InnoDB + RR级别 ， 将基本操作封装成事务，事务最好是单操作的，对于事务要求可以看markdown
    # 这里写一个测试用的事务
    try:
        async with pool.acquire() as conn:
            try:
                async with conn.cursor(aiomysql.DictCursor) as cursor:  # 获取字典格式
                    await cursor.execute(data["sql"])
                    result = await cursor.fetchall()
                    # await conn.commit()
                    result = JSON(result)  # 返回 JSON 格式结果
            except aiomysql.Error as db_error:
                raise ServerError(f"Database query failed: {str(db_error)}", status_code=500)
        return result
    except Exception as e:
        # 捕获其他异常并返回友好的错误信息
        raise ServerError(f"An error occurred: {str(e)}", status_code=500)

@app.post("/URD")
async def Deal_Other(request):
    data = request.json
    try:
        async with pool.acquire() as conn:
            try:
                async with conn.cursor(aiomysql.DictCursor) as cursor: # 用于指明获取字典
                    await cursor.execute(data["sql"])
                    await conn.commit()
            except aiomysql.Error as db_error:
                raise ServerError(f"Database query failed: {str(db_error)}", status_code=500)
        return JSON({"message":"ok"})
    except Exception as e:
        # 捕获其他异常并返回友好的错误信息
        raise ServerError(f"An error occurred: {str(e)}", status_code=500)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=9090)
        
