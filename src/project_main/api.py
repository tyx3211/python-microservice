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
from urllib.parse import unquote

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

def isAllNone(checkTuple:tuple)->bool:
    for item in checkTuple:
        if item is not None:
            return False
    return True

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

#############################################################
    
# 北向接口

# 设备基础信息CRUD

##############################################################
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
    # 参数检验部分，至少要有device_id和其余一项修改的
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
        if isAllNone(update_info):
            return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Missing required parameters!"}, status=400)
        device_id = dic["device_id"]
        await deviceOP.update(device_id,update_info)
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)
    
    # 查询设备基础信息
        # 根据设备id查询
@app.get('/service/devices_manage/device_basic_id_query/<device_id>')
async def device_id_query(request:Request,device_id):  
    if request.headers.get('Content-Type') != 'application/json':
        return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Content-Type must be application/json"}, status=400)
    #正式处理部分
    try:
        device_id = unquote(device_id) # 去除URL转义
        result = await deviceOP.query(device_id=device_id)
        return response.json({"status":"success","data":result},status=200)
    except Exception as e:
        return dealException(e)
        
        # 根据设备Sn_Model对查询
@app.get('/service/devices_manage/device_basic_SnModel_query/<device_sn>/<device_model>')
async def device_SnModel_query(request:Request,device_sn,device_model):  
    if request.headers.get('Content-Type') != 'application/json':
        return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Content-Type must be application/json"}, status=400)
    #正式处理部分
    try:
        device_sn = unquote(device_sn) # 去除URL转义
        device_model = unquote(device_model) # 去除URL转义
        result = await deviceOP.query(SN_Model=(device_sn,device_model))
        return response.json({"status":"success","data":result},status=200)
    except Exception as e:
        return dealException(e)
    
    # 删除设备(连带删除设备关联的所有设备分组关系)
@app.delete('/service/devices_manage/device_delete',ignore_body=False)
async def device_delete(request):
    # 需要提供device_id
    result={}
    if checkJsonParams(request,["device_id"],result) is False: # 检查出错误
        return result["result"]
    
    # 正式处理部分
    try:
        dic = request.json 
        await deviceOP.delete(dic["device_id"])
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)

################################################################
    
# 分组基础信息CRUD
    # 创建分组
@app.post('/service/devices_manage/group_add')
async def group_add(request):
    result={} # 传出参数
    if checkJsonParams(request,group_required_fields,result) is False: # 检查出错误
        return result["result"]
    
    #正式处理部分
    try:
        dic = request.json
        requestTuple = normalize_dict_to_tuple(dic,groupFields) # 规范化为元组
        group_id = await groupOP.create(requestTuple)
        return response.json({"status":"success","data":{"group_id":group_id}},status=200)
    except Exception as e:
        return dealException(e)

    # 修改分组信息
@app.put('/service/devices_manage/group_modify')
async def group_modify(request):
    # 参数检验部分，至少要有group_id
    result={} # 传出参数
    if checkJsonParams(request,["group_id"],result) is False: # 检查出错误
        return result["result"]

    #正式处理部分
    try:
        dic = request.json
        update_info = normalize_dict_to_tuple(dic,group_updated_fields)
        if isAllNone(update_info):
            return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Missing required parameters!"}, status=400)
        group_id = dic["group_id"]
        await groupOP.update(group_id,update_info)
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)

    # 查询分组信息
        # 根据分组ID查询
@app.get('/service/devices_manage/group_id_query/<group_id>')
async def group_id_query(request,group_id):
    if request.headers.get('Content-Type') != 'application/json':
        return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Content-Type must be application/json"}, status=400)
    #正式处理部分
    try:
        group_id = unquote(group_id) # 去除URL转义
        group_id = int(group_id)
        result = await groupOP.query(group_id=group_id)
        return response.json({"status":"success","data":result},status=200)
    except Exception as e:
        return dealException(e)
    
        # 根据分组name查询
@app.get('/service/devices_manage/group_name_query/<group_name>')
async def group_name_query(request,group_name):
    if request.headers.get('Content-Type') != 'application/json':
        return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Content-Type must be application/json"}, status=400)
    #正式处理部分
    try:
        group_name = unquote(group_name) # 去除URL转义
        result = await groupOP.query(group_name=group_name)
        return response.json({"status":"success","data":result},status=200)
    except Exception as e:
        return dealException(e)
    

    # 删除分组(也要删除分组关联的设备-分组关系)
@app.delete('/service/devices_manage/group_delete',ignore_body=False)
async def group_delete(request):
    # 需要提供group_id
    result={}
    if checkJsonParams(request,["group_id"],result) is False: # 检查出错误
        return result["result"]
    
    # 正式处理部分
    try:
        dic = request.json 
        await groupOP.delete(dic["group_id"])
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)

###############################################################

# 设备-分组关系基础信息CRUD
    # 新建设备-分组关系
@app.post('/service/devices_manage/relation_add')
async def relation_add(request):
    result={} # 传出参数
    if checkJsonParams(request,relation_required_fields,result) is False: # 检查出错误
        return result["result"]
    
    #正式处理部分
    try:
        dic = request.json 
        await relationOP.create(dic["device_id"],dic["group_id"])
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)
    
    # 删除设备-分组关系
@app.delete('/service/devices_manage/relation_del',ignore_body=False)
async def relation_del(request):
    result={}
    if checkJsonParams(request,["device_id","group_id"],result) is False: # 检查出错误
        return result["result"]
    
    # 正式处理部分
    try:
        dic = request.json 
        await relationOP.deleteRelation(dic["device_id"],dic["group_id"])
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)
    
    # 修改设备-分组关系
        # 修改某个设备-分组关系中的分组
@app.put('/service/devices_manage/relation_group_modify')
async def relation_group_modify(request):
    # 参数检验部分，至少要有device_id,group_id,new_group_id
    result={} # 传出参数
    if checkJsonParams(request,["device_id","group_id","new_group_id"],result) is False: # 检查出错误
        return result["result"]

    #正式处理部分
    try:
        dic = request.json
        device_id = dic["device_id"]
        group_id = dic["group_id"]
        new_group_id = dic["new_group_id"]
        await relationOP.updateGroupInRelation(device_id,group_id,new_group_id)
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)
    
        # 修改某个设备-分组关系中的设备
@app.put('/service/devices_manage/relation_device_modify')
async def relation_device_modify(request):
    # 参数检验部分，至少要有device_id,group_id,new_device_id
    result={} # 传出参数
    if checkJsonParams(request,["device_id","group_id","new_device_id"],result) is False: # 检查出错误
        return result["result"]

    #正式处理部分
    try:
        dic = request.json
        device_id = dic["device_id"]
        group_id = dic["group_id"]
        new_device_id = dic["new_device_id"]
        await relationOP.updateDeviceInRelation(device_id,group_id,new_device_id)
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)

###########################################################

# 基于设备-分组关系的二层增删改查
    # 修改分组下所有设备信息
@app.put('/service/devices_manage/group_all_devices_modify')
async def group_all_devices_modify(request):
    # 参数检验部分，至少要有group_id和其余一项修改的
    result={} # 传出参数
    if checkJsonParams(request,["group_id"],result) is False: # 检查出错误
        return result["result"]

    #正式处理部分
    try:
        dic = request.json
        # 查询是否要修改密码
        if "password" in dic:
            hashed_password = bcrypt.hashpw(dic["password"].encode('utf-8'),bcrypt.gensalt()) #将用户密码加盐哈希
            dic["password"] = hashed_password.decode("utf-8")
        update_info = normalize_dict_to_tuple(dic,device_updated_fields)
        if isAllNone(update_info):
            return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Missing required parameters!"}, status=400)
        group_id = dic["group_id"]
        await relationOP.updateAllDevice(group_id,update_info)
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)
    

    # 根据设备id查询其所有所属分组信息
@app.get('/service/devices_manage/device_query_all_group/<device_id>')
async def device_query_all_group(request,device_id):
    if request.headers.get('Content-Type') != 'application/json':
        return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Content-Type must be application/json"}, status=400)
    #正式处理部分
    try:
        device_id = unquote(device_id) # 去除URL转义
        result = await relationOP.queryAllGroupByDevice(device_id)
        return response.json({"status":"success","data":result},status=200)
    except Exception as e:
        return dealException(e)
    
    # 根据分组id查询其所有设备信息
@app.get('/service/devices_manage/group_query_all_device/<group_id>')
async def group_query_all_device(request,group_id):
    if request.headers.get('Content-Type') != 'application/json':
        return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Content-Type must be application/json"}, status=400)
    #正式处理部分
    try:
        group_id = unquote(group_id) # 去除URL转义
        group_id = int(group_id)
        result = await relationOP.queryAllDeviceByGroup(group_id)
        return response.json({"status":"success","data":result},status=200)
    except Exception as e:
        return dealException(e)
    
    # 根据设备id删除某个设备的所有设备-分组关系
@app.delete('/service/devices_manage/delete_device_all_relation',ignore_body=False)
async def delete_device_all_relation(request):
    result={}
    if checkJsonParams(request,["device_id"],result) is False: # 至少需要提供device_id
        return result["result"]
    
    # 正式处理部分
    try:
        dic = request.json 
        await relationOP.deleteAllRelationByDevice(dic["device_id"])
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)
    
    # 根据分组id删除某个分组的所有设备-分组关系
@app.delete('/service/devices_manage/delete_group_all_relation',ignore_body=False)
async def delete_group_all_relation(request):
    result={}
    if checkJsonParams(request,["group_id"],result) is False: # 至少需要提供group_id
        return result["result"]
    
    # 正式处理部分
    try:
        dic = request.json 
        await relationOP.deleteAllRelationByGroup(dic["group_id"])
        return response.json({"status":"success","data":{}},status=200)
    except Exception as e:
        return dealException(e)
    
#     # 根据分组id删除某个分组下的所有设备
# @app.delete('/service/devices_manage/delete_group_all_devices',ignore_body=False)
# async def delete_group_all_relation(request):
#     result={}
#     if checkJsonParams(request,["group_id"],result) is False: # 至少需要提供group_id
#         return result["result"]
    
#     # 正式处理部分
#     try:
#         dic = request.json 
#         await relationOP.deleteAllRelatedDeviceByGroup(dic["group_id"])
#         return response.json({"status":"success","data":{}},status=200)
#     except Exception as e:
#         return dealException(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=9090)