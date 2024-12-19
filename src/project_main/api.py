from sanic import Sanic
from sanic import response
from sanic.request import Request
import json
from sanic.exceptions import ServerError
from websockets.legacy.client import WebSocketClientProtocol
import asyncio
import aiomysql
from sanic.log import logger,error_logger
from snowflake import SnowflakeGenerator
import bcrypt

from Database_OP import DeviceOP,GroupOP,RelationOP
from Database_OP import DeviceOPError,GroupOPError,RelationOPError,DataBaseError

gen = SnowflakeGenerator(1) # 雪花ID生成器

# 全局连接池
pool:aiomysql.Pool = None

# 数据库操作对象
deviceOP = None
groupOP = None
relationOP = None

# 创建Sanic应用
app = Sanic("webSocketServer")

# 将异常反馈以json形式输出
app.config.FALLBACK_ERROR_FORMAT = "json"

# 配置Host，Port，数据库User和Password

Host="127.0.0.1"
Port=3306
User="root"
Password="root"

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



# 一些辅助函数
    # 封装参数检查辅助函数
def check_Required_params(request_dict:dict,checkList:list)->bool:
    for item in checkList:
        if item not in request_dict:
            return False
    return True

    # 封装将字典标准化为元组的辅助函数
def normalize_dict_to_tuple(request_dict:dict,reference_list:list)->tuple:
    result_list = []
    for item in reference_list:
        if item in request_dict:
            result_list.append(request_dict[item])
        else:
            result_list.append(None)
    result_tuple = tuple(result_list)
    return result_tuple

    # 封装通用前置入参检查,result是传出参数
def checkJsonParams(request:Request,required_fields:list,result:dict):
    if request.headers.get('Content-Type') != 'application/json':
        result["result"] = response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Content-Type must be application/json"}, status=400)
        return False
    dic = request.json
    if dic is None:
        result["result"] = response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "please provide legal json!"}, status=400)
        return False
    if check_Required_params(dic,required_fields) is False:
        result["result"] = response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Missing required parameters!"}, status=400)
        return False
    ###
    # 还可以加上更严格的类型检查逻辑...
    ###
    return True

# 封装异常处理辅助函数
def dealException(e:Exception):
    if isinstance(e,DeviceOPError):
        return response.json({"status": "fail", "type":"DEVICEOP_ERROR" , "message": str(e)}, status=e.Error_Code)
    elif isinstance(e,GroupOPError):
        return response.json({"status": "fail", "type":"GROUPOP_ERROR" , "message": str(e)}, status=e.Error_Code)
    elif isinstance(e,RelationOPError):
        return response.json({"status": "fail", "type":"RELATIONOP_ERROR" , "message": str(e)}, status=e.Error_Code)
    elif isinstance(e,DataBaseError):
        return response.json({"status": "fail", "type":"DATABASE_ERROR" , "message": "Maybe JSON parameter type incorrect(please check) or DataBase Inner Error"}, status=500)
    else:
        return response.json({"status": "fail", "type":"INNER_ERROR" , "message": "Server Inner Error"}, status=500)

async def connect_to_database():
    global pool,deviceOP,groupOP,relationOP
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
    
    # 为数据库基本操作配置上连接池
    deviceOP = DeviceOP(pool)
    groupOP = GroupOP(pool)
    relationOP = RelationOP(pool)
    
    
@app.listener("before_server_start")
async def setup_db(app,loop):
    # 服务正式启动前先连接数据库
    await connect_to_database()
    
@app.listener("after_server_stop")
async def setup_db(app,loop):
    # 服务正式启动前先连接数据库
    pool.close()
    await pool.wait_closed()
    
# 北向接口
    #设备注册
@app.post('/service/devices_manage/device_add')
async def device_add(request:Request):
    # 参数检验部分，要求必须提供密码
    result={} # 传出参数
    if checkJsonParams(request,device_required_fields,result) is False: # 检查出错误
        return result["result"]
    # 额外参数类型检验，这里检验password
    dic=request.json
    if type(dic["password"]) is not str:
        return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "password shoule be string!"}, status=400)
    
    #正式处理部分,id和state新增（或重置）
    try:
        dic["device_id"] = str(next(gen)) # 生成雪花id
        origin_password = dic["password"]
        hashed_password = bcrypt.hashpw(dic["password"].encode('utf-8'),bcrypt.gensalt()) #将用户密码加盐哈希
        dic["password"] = hashed_password.decode("utf-8")
        dic["dev_state"] = "offline" # 设备状态默认offline
        requestTuple = normalize_dict_to_tuple(dic,deviceFields) # 规范化为元组
        await deviceOP.create(requestTuple)
        return response.json({"status":"success","data":{"device_id":dic["device_id"],"password":str(origin_password)}},status=200)
    except Exception as e:
        return dealException(e)
    
    # 修改设备基础信息
@app.put('/service/devices_manage/device_basic_modify')
async def device_basic_modify(request:Request):
    # 参数检验部分，至少要有device_id
    result={} # 传出参数
    if checkJsonParams(request,["device_id"],result) is False: # 检查出错误
        return result["result"]

    #正式处理部分
    try:
        dic = request.json
        # 查询是否要修改密码
        if "password" in dic:
            hashed_password = bcrypt.hashpw(dic["password"].encode('utf-8'),bcrypt.gensalt()) #将用户密码加盐哈希
            dic["password"] = hashed_password.decode("utf-8")
        update_info = normalize_dict_to_tuple(dic,device_updated_fields)
        device_id = dic["device_id"]
        await deviceOP.update(device_id,update_info)
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=9090)