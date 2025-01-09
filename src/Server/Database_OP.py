"""
封装事务化数据库操作
数据库和相应表应预创建
详见pre_SQL.sql
"""

import aiomysql
from snowflake import SnowflakeGenerator
import bcrypt
from sanic.log import logger,error_logger
import time
import math
import json
import os

# gen = SnowflakeGenerator(1) # 雪花ID生成器


# 配置Host，Port，数据库User和Password

Host = ""
Port = None
User = ""
Password = ""

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建database_ini.json文件的绝对路径
file_path = os.path.join(current_dir, "database_ini.json")

with open(file_path, 'r') as file:
    Host, Port, User, Password = json.load(file).values()  # 解析 JSON 数据为字典 并解构

pool:aiomysql.Pool = None

async def connect_to_database():
    global pool
    # 初始化连接池
    pool = await aiomysql.create_pool(
        host=Host,
        port=Port,
        user=User,
        password=Password,
        db="device_management",
        minsize=15, # 最小(基础)连接数
        maxsize=100,  # 可以设置最大连接数
    )

async def close_database():
    pool.close()
    await pool.wait_closed()


# 设置预设列表
    # 各表创建时需要的字段(一些创建时不需要指定的如group_id,relation_id不需要记录)
deviceFields = ["device_id","device_name","device_type","hardware_sn","hardware_model","software_version","software_last_update","nic1_type","nic1_mac","nic1_ipv4","nic2_type","nic2_mac","nic2_ipv4","dev_description","dev_state","password"]
groupFields = ["group_name","group_description"]
relationFields = ["device_id","group_id"]
    # 用户创建设备/分组/关系必需提供的非NULL字段
device_required_fields = ["device_name","device_type","hardware_sn","hardware_model","software_version","software_last_update","password"]
group_required_fields = ["group_name"]
relation_required_fields = ["device_id","group_id"]
    # 用户update时最多能够指定更新的字段
device_updated_fields = ["device_name","device_type","software_version","software_last_update","nic1_type","nic1_mac","nic1_ipv4","nic2_type","nic2_mac","nic2_ipv4","dev_description","dev_state","password"]
group_updated_fields = ["group_description"]
        # 若更新某个关系下分组
relation_updated_group = ["group_id"]
        # 若更新某个关系下设备
relation_updated_device = ["device_id"]

# 构建数据库操作异常体系
class DataBaseError(Exception):
    def __init__(self,message):
        super().__init__(message)

class DeviceOPError(DataBaseError):
    def __init__(self,message,Error_Code):
        self.Error_Code = Error_Code
        super().__init__(message)

class GroupOPError(DataBaseError):
    def __init__(self,message,Error_Code):
        self.Error_Code = Error_Code
        super().__init__(message)
        
class RelationOPError(DataBaseError):
    def __init__(self,message,Error_Code):
        self.Error_Code = Error_Code
        super().__init__(message)
        
# 封装异常判断函数
def isOPError(e)->bool:
    if isinstance(e,DeviceOPError):
        return True
    if isinstance(e,GroupOPError):
        return True
    if isinstance(e,RelationOPError):
        return True
    return False

# 封装添加时间戳函数
def addTimestamp(info,isCreated=False):
    timestamp = math.floor(time.time()*1000)
    if isCreated:
        result = info + (timestamp,timestamp)
    else:
        result = info + (timestamp,)
    return result

def WrapperToJson(OriginDict:dict,isDevice=False,isGroup=False,isRelation=False)->dict:
    if isDevice:
        result = {}
        result["device_id"] = OriginDict["device_id"]
        result["device_name"] = OriginDict["device_name"]
        result["device_type"] = OriginDict["device_type"]
        result["hardware"] = {}
        result["hardware"]["sn"] = OriginDict["hardware_sn"]
        result["hardware"]["model"] = OriginDict["hardware_model"]
        result["software"] = {}
        result["software"]["version"] = OriginDict["software_version"]
        result["software"]["last_update"] = OriginDict["software_last_update"].strftime("%Y-%m-%d") # 额外转化Date对象
        result["nic"] = [{},{}]
        result["nic"][0]["type"] = OriginDict["nic1_type"]
        result["nic"][0]["mac"] = OriginDict["nic1_mac"]
        result["nic"][0]["ipv4"] = OriginDict["nic1_ipv4"]
        result["nic"][1]["type"] = OriginDict["nic2_type"]
        result["nic"][1]["mac"] = OriginDict["nic2_mac"]
        result["nic"][1]["ipv4"] = OriginDict["nic2_ipv4"]
        result["dev_description"] = OriginDict["dev_description"]
        result["dev_state"] = OriginDict["dev_state"]
        result["password"] = OriginDict["password"]
        result["created_time"] = OriginDict["created_time"]
        result["updated_time"] = OriginDict["updated_time"]
    elif isGroup:
        result = {}
        result["group_id"] = OriginDict["group_id"]
        result["group_name"] = OriginDict["group_name"]
        result["group_description"] = OriginDict["group_description"]
        result["created_time"] = OriginDict["created_time"]
        result["updated_time"] = OriginDict["updated_time"]
    else:
        result = None
    return result


# 封装update_sql生成函数
def getUpdateSQL(sqlPartBefore:str,update_info,referece_list:list,sqlPartAfter:str)->str:
    Part_str=""
    index = 0
    for item in update_info:
        if item is not None:
            Part_str+=referece_list[index]+"=%s,"
        index+=1
    Part_str+="updated_time=%s "
    result_str = sqlPartBefore + Part_str + sqlPartAfter
    return result_str

def clearInfoNoneColumn(info:tuple)->tuple:
    result = []
    for item in info:
        if item is not None:
            result.append(item)
    return tuple(result)

# 再封装一些常用子操作(多为查询)
async def isDeviceExist(cursor,device_id=None,SN_Model=None): # SN_Model是(hardware_sn,hardware_model)元组
    if device_id is not None:
        sql1="""SELECT device_id FROM devices WHERE device_id=%s;"""
        await cursor.execute(sql1,(device_id,))
    elif SN_Model is not None:
        sql2="""SELECT device_id FROM devices WHERE (hardware_sn=%s AND hardware_model=%s);"""
        await cursor.execute(sql2,SN_Model)
    else:
        raise DeviceOPError("Missing required parameters!",400)
    result = await cursor.fetchall()
    return None if len(result)==0 else result

async def isGroupExist(cursor,group_id=None,group_name=None):
    if group_id is not None:
        sql1="""SELECT group_id FROM group_info WHERE group_id=%s;"""
        await cursor.execute(sql1,(group_id,))
    elif group_name is not None:
        sql2="""SELECT group_id FROM group_info WHERE group_name=%s;"""
        await cursor.execute(sql2,(group_name,))
    else:
        raise GroupOPError("Missing required parameters!",400)
    result = await cursor.fetchall()
    return None if len(result)==0 else result

async def isRelationExist(cursor,device_id,group_id):
    sql="""SELECT device_id FROM relations WHERE (device_id=%s AND group_id=%s);"""
    await cursor.execute(sql,(device_id,group_id))
    result = await cursor.fetchall()
    return None if len(result)==0 else result

# 设备相关操作
class DeviceOP:
    # 设备注册(创建设备)
    async def create(self,device_info:tuple):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询设备是否已经存在,且假定上层已经处理好了device_info(即已经处理好了雪花ID生成，和密码创建)
                    sn_model = (device_info[3],device_info[4])
                    if (await isDeviceExist(cursor,SN_Model=sn_model) is not None):
                        raise DeviceOPError("Device already exists.",409) # Conflict错误码，资源已存在
                    # 再正式注册设备
                    sql = """INSERT INTO devices(device_id,device_name,device_type,hardware_sn,hardware_model,software_version,software_last_update,nic1_type,nic1_mac,nic1_ipv4,nic2_type,nic2_mac,nic2_ipv4,dev_description,dev_state,password,created_time,updated_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
                    device_info = addTimestamp(device_info,isCreated=True) # 包装created_time和updated_time
                    await cursor.execute(sql,device_info)
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")

    # 修改设备信息
    async def update(self,device_id,update_info):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询设备是否已经存在
                    if (await isDeviceExist(cursor,device_id) is None):
                        raise DeviceOPError("Device NOT FOUND.",404) # Conflict错误码，资源已存在
                    # 再生成update_sql
                    sql = getUpdateSQL("UPDATE devices SET ",update_info,device_updated_fields,"WHERE device_id = %s;")
                    update_info = clearInfoNoneColumn(update_info)
                    update_info = addTimestamp(update_info)
                    await cursor.execute(sql,update_info + (device_id,))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
            
    
    # 查询设备信息
    async def query(self,device_id=None,SN_Model=None):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if device_id is not None:
                        sql1="""SELECT device_id,device_name,device_type,hardware_sn,hardware_model,software_version,software_last_update,nic1_type,nic1_mac,nic1_ipv4,nic2_type,nic2_mac,nic2_ipv4,dev_description,dev_state,password,created_time,updated_time FROM devices WHERE device_id=%s;"""
                        await cursor.execute(sql1,(device_id,))
                    elif SN_Model is not None:
                        sql2="""SELECT device_id,device_name,device_type,hardware_sn,hardware_model,software_version,software_last_update,nic1_type,nic1_mac,nic1_ipv4,nic2_type,nic2_mac,nic2_ipv4,dev_description,dev_state,password,created_time,updated_time FROM devices WHERE (hardware_sn=%s AND hardware_model=%s);"""
                        await cursor.execute(sql2,SN_Model)
                    result = await cursor.fetchone()
                    await conn.commit()
                    if result is None:
                        raise DeviceOPError("Device NOT FOUND.",404)
                    else:
                        result = WrapperToJson(result,isDevice=True)
                        return result
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
    #删除设备（设备分组关系也要一起删）
    async def delete(self,device_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询是否有该设备
                    if (await isDeviceExist(cursor,device_id=device_id) is None):
                        raise DeviceOPError("Device NOT FOUND",404)
                    # 再正式删除设备
                        # 先删除-设备分组关系
                    sql1 = """DELETE FROM relations WHERE device_id=%s"""
                    await cursor.execute(sql1,(device_id,))
                        # 再删除设备
                    sql2 = """DELETE FROM devices WHERE device_id=%s"""
                    await cursor.execute(sql2,(device_id,))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
            
    # 修改多个设备状态为离线
    async def update_state_to_offline(self,device_ids:tuple):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 修改设备状态
                    timestamp = math.floor(time.time()*1000)
                    sql = f"UPDATE devices SET dev_state='offline',updated_time={timestamp} WHERE device_id IN " + "(" + ("%s," * (len(device_ids)-1)) + "%s);"
                    await cursor.execute(sql,device_ids)
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
#分组相关操作
class GroupOP:
    # 创建分组
    async def create(self,group_info):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询分组是否存在
                    group_name=group_info[0]
                    if (await isGroupExist(cursor,group_name=group_name) is not None):
                        raise GroupOPError("Group already exists.",409) # Conflict错误码，资源已存在
                    # 再正式注册分组
                    sql = """INSERT INTO group_info(group_id,group_name,group_description,created_time,updated_time) VALUES(DEFAULT,%s,%s,%s,%s);"""
                    group_info = addTimestamp(group_info,isCreated=True) # 包装created_time和updated_time
                    await cursor.execute(sql,group_info)
                    # 查看分组ID
                    sql2 = """SELECT group_id from group_info WHERE group_name=%s"""
                    await cursor.execute(sql2,(group_name,))
                    result = await cursor.fetchone()
                    await conn.commit()
                    return result[0]
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
    # 修改分组信息
    async def update(self,group_id,update_info):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询分组是否已经存在
                    if (await isGroupExist(cursor,group_id) is None):
                        raise GroupOPError("Group NOT FOUND.",404)
                    # 再生成update_sql
                    sql = getUpdateSQL("UPDATE group_info SET ",update_info,group_updated_fields,"WHERE group_id = %s;")
                    update_info = clearInfoNoneColumn(update_info)
                    update_info = addTimestamp(update_info)
                    await cursor.execute(sql,update_info + (group_id,))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
    # 查询分组信息
    async def query(self,group_id=None,group_name=None):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if group_id is not None:
                        sql1="""SELECT group_id,group_name,group_description,created_time,updated_time FROM group_info WHERE group_id=%s;"""
                        await cursor.execute(sql1,(group_id,))
                    elif group_name is not None:
                        sql2="""SELECT group_id,group_name,group_description,created_time,updated_time FROM _info WHERE group_name=%s;"""
                        await cursor.execute(sql2,(group_name,))
                    result = await cursor.fetchone()
                    await conn.commit()
                    if result is None:
                        raise GroupOPError("Group NOT FOUND.",404)
                    else:
                        result = WrapperToJson(result,isGroup=True)
                        return result
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
    #删除分组（设备分组关系表也要一起删）
    async def delete(self,group_id=None,group_name=None):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询是否有该分组
                    if (await isGroupExist(cursor,group_id=group_id) is None):
                        raise GroupOPError("Group NOT FOUND",404)
                    # 再正式删除分组
                        # 先删除-设备分组关系
                    sql1 = """DELETE FROM relations WHERE group_id=%s"""
                    await cursor.execute(sql1,(group_id,))
                        # 再删除分组
                    sql2 = """DELETE FROM group_info WHERE group_id=%s"""
                    await cursor.execute(sql2,(group_id,))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")

# 设备-分组关系相关操作
class RelationOP:
    # 新建设备-分组关系
    async def create(self,device_id,group_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 查询创建设备-分组关系操作是否合法
                    if (await isDeviceExist(cursor,device_id) is None):
                        raise DeviceOPError("Device NOT FOUND.",404)
                    if (await isGroupExist(cursor,group_id) is None):
                        raise GroupOPError("Group NOT FOUND.",404)
                    if (await isRelationExist(cursor,device_id,group_id) is not None):
                        raise RelationOPError("Relation already exists",409)
                    # 再正式注册分组
                    sql = """INSERT INTO relations(relation_id,device_id,group_id) VALUES(DEFAULT,%s,%s);"""
                    await cursor.execute(sql,(device_id,group_id))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
    # 修改设备-分组关系，或利用关系修改设备
        # 修改某设备-分组关系中分组
    async def updateGroupInRelation(self,device_id,group_id,new_group_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询设备-分组关系是否已经存在
                    if (await isRelationExist(cursor,device_id,group_id) is None):
                        raise RelationOPError("Relation NOT FOUND.",404)
                    sql="""UPDATE relations SET group_id=%s WHERE (device_id=%s AND group_id=%s)"""
                    await cursor.execute(sql,(new_group_id,device_id,group_id))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")

        # 修改某设备-分组关系中设备
    async def updateDeviceInRelation(self,device_id,group_id,new_device_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询设备-分组关系是否已经存在
                    if (await isRelationExist(cursor,device_id,group_id) is None):
                        raise RelationOPError("Relation NOT FOUND.",404)
                    sql="""UPDATE relations SET device_id=%s WHERE (device_id=%s AND group_id=%s)"""
                    await cursor.execute(sql,(new_device_id,device_id,group_id))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
        # 修改分组下所有设备信息
    async def updateAllDevice(self,group_id,devices_update_info):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询分组是否已经存在
                    if (await isGroupExist(cursor,group_id) is None):
                        raise GroupOPError("Group NOT FOUND.",404)
                    # 再查询分组下是否有设备
                    sqlTest = """SELECT device_id FROM relations WHERE group_id=%s LIMIT 1;"""
                    await cursor.execute(sqlTest,(group_id,))
                    TestResult = await cursor.fetchone()
                    if TestResult is None:
                        raise RelationOPError("No Devices in this Group.",404)
                    # 使用子查询
                    sql = getUpdateSQL("UPDATE devices SET ",devices_update_info,device_updated_fields,"WHERE device_id IN (SELECT device_id FROM relations WHERE group_id=%s);")
                    devices_update_info = clearInfoNoneColumn(devices_update_info)
                    devices_update_info = addTimestamp(devices_update_info)
                    await cursor.execute(sql,devices_update_info + (group_id,))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
    # 查询设备-分组关系
        # 根据设备id查询所有所属分组信息
    async def queryAllGroupByDevice(self,device_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if (await isDeviceExist(cursor,device_id=device_id) is None):
                        raise DeviceOPError("Device NOT FOUND",404)
                    sql="""SELECT group_id,group_name,group_description,created_time,updated_time FROM group_info WHERE group_id IN (SELECT group_id FROM relations WHERE device_id=%s);"""
                    await cursor.execute(sql,(device_id,))
                    result = await cursor.fetchall()
                    await conn.commit()
                    if len(result)==0:
                        raise RelationOPError("Devices not in any Group.",404)
                    else:
                        return result
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
        # 根据分组id查询所有下属设备信息
    async def queryAllDeviceByGroup(self,group_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if (await isGroupExist(cursor,group_id=group_id) is None):
                        raise GroupOPError("Group NOT FOUND",404)
                    sql="""SELECT device_id,device_name,device_type,hardware_sn,hardware_model,software_version,software_last_update,nic1_type,nic1_mac,nic1_ipv4,nic2_type,nic2_mac,nic2_ipv4,dev_description,dev_state,password,created_time,updated_time FROM devices WHERE device_id IN (SELECT device_id FROM relations WHERE group_id=%s);"""
                    await cursor.execute(sql,(group_id,))
                    result = await cursor.fetchall()
                    await conn.commit()
                    if len(result)==0:
                        raise RelationOPError("No Devices in this Group.",404)
                    else:
                        for i in range(len(result)):
                            result[i] = WrapperToJson(result[i],isDevice=True)
                        return result
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
    # 删除设备-分组关系，或根据关系删除相应设备或分组
        # 删除设备-分组关系
    async def deleteRelation(self,device_id,group_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询是否有该设备-分组关系
                    if (await isRelationExist(cursor,device_id,group_id) is None):
                        raise RelationOPError("Relation NOT FOUND",404)
                    # 再正式删除设备-分组关系
                    sql = """DELETE FROM relations WHERE device_id=%s AND group_id=%s"""
                    await cursor.execute(sql,(device_id,group_id))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
        # 删除某个设备的所有设备-分组关系
    async def deleteAllRelationByDevice(self,device_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询是否有该设备
                    if (await isDeviceExist(cursor,device_id=device_id) is None):
                        raise DeviceOPError("Device NOT FOUND",404)
                    # 再查询设备是否在分组下
                    sqlTest = """SELECT group_id FROM relations WHERE device_id=%s LIMIT 1;"""
                    await cursor.execute(sqlTest,(device_id,))
                    TestResult = await cursor.fetchone()
                    if TestResult is None:
                        raise RelationOPError("Devices not in any Group.",404)
                    # 再正式删除设备-分组关系
                    sql = """DELETE FROM relations WHERE device_id=%s;"""
                    await cursor.execute(sql,(device_id,))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
        # 删除某个分组下所有的设备-分组关系
    async def deleteAllRelationByGroup(self,group_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询是否有该分组
                    if (await isGroupExist(cursor,group_id=group_id) is None):
                        raise GroupOPError("Group NOT FOUND",404)
                    # 再查询分组下是否有设备
                    sqlTest = """SELECT device_id FROM relations WHERE group_id=%s LIMIT 1;"""
                    await cursor.execute(sqlTest,(group_id,))
                    TestResult = await cursor.fetchone()
                    if TestResult is None:
                        raise RelationOPError("No Devices in this Group.",404)
                    # 再正式删除设备-分组关系
                    sql = """DELETE FROM relations WHERE group_id=%s;"""
                    await cursor.execute(sql,(group_id,))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
    
        # 删除某个分组下所属的所有设备
    async def deleteAllRelatedDeviceByGroup(self,group_id):
        pass
    
    
# 构造暴露单例对象
deviceOP = DeviceOP()
groupOP = GroupOP()
relationOP = RelationOP()