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

# gen = SnowflakeGenerator(1) # 雪花ID生成器


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
device_updated_fields = ["device_name","device_type","software_version","software_last_update","nic1_type","nic1_mac","nic1_ipv4","nic2_type","nic2_mac","nic2_ipv4","dev_description","password"]
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

# 封装update_sql生成函数
def getUpdateSQL(sqlPartBefore:str,update_info,referece_list:list,sqlPartAfter:str)->str:
    Part_str=""
    index = 0
    for item in update_info:
        if item is not None:
            Part_str+=referece_list[index]+"=%s,"
            index+=1
    result_str = sqlPartBefore + Part_str[:-1] + sqlPartAfter
    return result_str

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
    # print(result)
    return None if len(result)==0 else result

# 设备相关操作
class DeviceOP:
    # 构造函数，用于使用连接池
    def __init__(self,Pool:aiomysql.Pool):
        self.pool:aiomysql.Pool = Pool
    
    # 设备注册(创建设备)
    async def create(self,device_info:tuple):
        try:
            async with self.pool.acquire() as conn:
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
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询设备是否已经存在
                    if (await isDeviceExist(cursor,device_id) is None):
                        raise DeviceOPError("Device NOT FOUND.",404) # Conflict错误码，资源已存在
                    # 再生成update_sql
                    sql = getUpdateSQL("UPDATE devices SET ",update_info,device_updated_fields,"WHERE device_id = %s")
                    await cursor.execute(sql,update_info + (device_id,))
                    await conn.commit()
        except Exception as e:
            await conn.rollback()
            # print(e)
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")
            
    
    # 查询设备信息
    async def query(self,device_id=None,SN_Model=None):
        pass
    
    #删除设备（设备分组关系表也要一起删）
    async def delete(self,device_info):
        pass
    
#分组相关操作
class GroupOP:
    # 构造函数，用于使用连接池
    def __init__(self,Pool:aiomysql.Pool):
        self.pool:aiomysql.Pool = Pool

    # 创建分组
    async def create(self,group_info):
        pass
    
    # 修改分组信息
    async def update(self,group_id,group_info):
        pass
    
    # 查询分组信息
    async def query(self,group_id:None,group_Name:None):
        pass
    
    #删除分组（设备分组关系表也要一起删）
    async def delete(self,group_id):
        pass

# 设备-分组关系相关操作
class RelationOP:
    # 构造函数，用于使用连接池
    def __init__(self,Pool:aiomysql.Pool):
        self.pool:aiomysql.Pool = Pool

    # 新建设备-分组关系
    async def create(self,device_id,group_id):
        pass
    
    # 修改设备-分组关系，或利用关系修改涉笔
        # 修改某设备-分组关系中设备
    async def updateDeviceInRelation(self,device_id,origin_group_id,new_group_id):
        pass
        # 修改某设备-分组关系中分组
    async def updateGroupInRelation(self,device_id,origin_group_id,new_group_id):
        pass
    
        # 修改分组下所有设备信息
    async def updateAllDevice(self,group_id,devices_info):
        pass
    
    # 查询设备-分组关系
        # 根据设备id查询所有所属分组信息
    async def queryAllGroupByDevice(self,device_id):
        pass
    
        # 根据分组id查询所有下属设备信息
    async def queryAllDeviceByGroup(self,group_id):
        pass
    
        # 根据设备id查询设备信息和所有分组信息
    async def queryAllInfoByDevice(self,device_id):
        pass
    
    # 删除设备-分组关系，或根据关系删除相应设备或分组
        # 删除设备-分组关系
    async def deleteRelation(self,device_id,group_id):
        pass
    
        # 删除某个设备的所有设备-分组关系
    async def deleteAllRelationByDevice(self,device_id):
        pass
    
        # 删除某个分组下所有的设备-分组关系
    async def deleteAllRelationByGroup(self,group_id):
        pass
    
        # 删除某个分组下所属的所有设备
    async def deleteAllrelatedDeviceByGroup(self,group_id):
        pass