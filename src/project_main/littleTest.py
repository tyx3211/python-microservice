# 这个小例子表明aiomysql默认AutoCommit模式为OFF

import aiomysql
import asyncio

pool:aiomysql.Pool = None

async def test():
    global pool
    pool = await aiomysql.create_pool(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='root',
        db='mytest',
        minsize=15, # 最小(基础)连接数
        maxsize=100,  # 可以设置最大连接数
    )

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT @@autocommit;")
            result = await cursor.fetchall()
            print("Autocommit mode:", result[0][0])  # 输出 1 表示启用，0 表示禁用

    pool.close()
    await pool.wait_closed()
         
asyncio.run(test())