# 1\. 略

# 2\. 对可复用架构的探索

### 概要图

![云边端协同架构](./概要.png)

上图展示了云端与边端协同架构：云端微服务通过北向接口服务于顶层业务，通过南向接口管理边端设备；边端控制器负责维持连接、执行指令与上报状态。

### 2.1 需求分析

#### 1.1 云端

**1.1.1 顶层业务**

  * **定位**：其实并非我们云边端协同架构中的内容，而是使用这一套云边端协同架构来更方便的统筹管理边端设备的客户服务。
  * **简述**：使用我们云边端协同架构中设备管理微服务提供的北向接口，获取边端设备信息并对其进行统筹管理，必要的时候借由北向接口对边端设备下达指令的业务服务。

**1.1.2 设备管理微服务**

  * **定位**：是我们云边端协同架构中云端微服务的部分，也是需要重点设计的内容。
  * **简述**：云边端协同架构中的云端微服务方，即要暴露北向接口供顶层业务使用（如查询设备信息等），又要暴露南向接口供边端设备汇报信息（如一小时内使用次数信息）和向边端设备下达指令，并且需要维护数据库存储设备当前设备状态信息，并创建记录设备信息改变的日志。

#### 1.2 边端

  * **概念**：是我们云边端协同架构中边缘实体设备的部分，受控于设备管理微服务，通过微服务的南向接口定期向设备管理微服务汇报信息，并且接受来自微服务方的指令，因此可以为其设计一套和南向接口配套的专门用来请求南向接口的可复用依赖。

#### 1.3 云边端协同架构的设计目标

  * **目标**：开发出一套可供他人（顶层业务）使用来更好更方便的对边端设备进行统筹管理的可复用架构，包括含有供他人（顶层业务）使用的北向接口以及供边端设备使用的南向接口的设备管理微服务，以及在边端设备上部署使用的和南向接口配套的专门用来请求南向接口的可复用依赖。

### 2\. 边端实体定义

#### 2.1 边端设备

  * **基本信息**：如设备编号，设备名称，设备分组，设备状态等。
  * **硬件信息**：如硬件序列号SN，网卡地址等。

#### 2.2 设备分组

  * **基本属性**：表设计：分组编号，分组名称，创建时间，更新时间等。

#### 2.3 设备与分组关系

  * **基本属性**：表设计：设备编号，分组编号，创建时间，更新时间等。
  * **设备分组的目的**：便于批量管理，可以对同一组设备下发统一的配置指令、更新固件、或进行监控和数据采集。分组还可以方便在云端系统中，控制边端设备的权限。
  * **设备分组进行单独建表**：由于设备和其分组可能是多对多的关系，利用关联表更好管理。

### 2.4 微服务端接口分类

#### 2.5 北向接口

暴露给顶层业务，供顶层业务统筹管理边端设备的接口。

#### 2.6 南向接口

暴露给边端设备，供边端设备上报信息，和直接管理并向边端设备下达指令的接口。

### 2.7 微服务端接口设计

#### 2.8 微服务端前置条件

维护了记录设备信息的数据库表和记录各设备状态信息改变的设备日志。

#### 2.9 北向接口的设计

  * **设计理念**：根据设备编号和设备信息在数据库中对相应的设备进行增删改查。
  * **暴露对象**：顶层业务。
  * **接口风格**：REST-LIKE API。
  * **接口应用层协议**：http/https。
  * **具体接口**：
    1.  基于设备编号查询、删除设备。（params: device\_id）
    2.  基于设备编号更新设备信息 (需要结合南向接口实现对于设备状态的实际调整)
    3.  根据设备信息创建(注册)设备。（params: device (or device\_message)）
    4.  根据设备编号查询设备日志。
    5.  根据设备编号查询、修改、删除设备关联的分组信息。
    6.  根据分组编号查询、修改、删除相应分组。（params: group\_id）
    7.  创建设备分组。（params: group\_name, group\_information）
    8.  根据分组编号查询、删除分组内全部设备。
    9.  查询设备是否在分组内。
    10. 添加、删除 [设备-设备分组] 关系。（params: device\_id, group\_id）

#### 2.11 南向接口的设计

  * **设计理念**：为设备周期上报数据提供接口，并且对设备进行指令下达。
  * **接口应用层协议**：webSocket，便于微服务端向设备下达指令。
  * **具体接口**：
    1.  **设备登录验证接口**：方便设备通过该登录鉴权接口登录到微服务端，以实现后续的数据上传和接受指令。
    2.  **设备数据上传接口**：根据设备编号和上传的设备信息，来更新相应的设备信息数据库表和设备日志。（params: device\_id, device\_data）
    3.  **设备指令下达**：通过 webSocket，在微服务端向边端设备发送指令请求（下达指令）。

### 2.12 边端基础应用功能(依赖级)

  * **设计理念**：在边端通过微服务南向接口实现登录微服务，周期性上报数据，执行微服务下发指令，记录本地操作日志，保存登录凭证等等。
  * **具体功能**：
    1.  **远程登录微服务**：与微服务的 webSocket 连接建立后就访问南向接口中登录鉴权接口，登录成功后保存并更新登录凭证 (例如token)，以便设备进行数据上传和指令执行操作。
    2.  **定时上报设备状态数据**：通过 webSocket，周期性的通过南向接口中设备数据上传接口上传设备状态。
    3.  **执行微服务下发指令**：利用 webSocket，处理来自云端微服务的指令请求，执行相应操作，并响应给微服务操作结果。
    4.  **在本地记录操作日志**：将相应登录操作，数据上报操作，指令执行操作都记录在本地操作日志中。

-----

# 3\. 系统架构、核心流程与关键技术

### 3.1 架构设计

(云端服务包括业务服务、日志记录、用户管理、设备管理、消息通告、客服服务；边端服务包括边端设备、外围设备、用户终端)

### 3.2 接口交互设计

#### 3.2.1 北向接口设计

**北向接口交互协议设计：**

  * **JSON URI**：HTTP方法（如，POST） `/service/devices_manage/<服务名称>/<参数>`

  * **Request Headers**:

    ```json
    {
        "content-type": "application/json"
        // "cookie": "string", // 可以免登录
    }
    ```

  * **Request Body**:

    ```json
    {
        // 除查询相关API使用GET方法将参数使用 /<参数> 置于URL中外，
        // POST、PUT、DELETE方法均在请求体中使用JSON格式传递,
    }
    ```

  * **Response Headers**:

    ```json
    {
        "content-type": "application/json"
    }
    ```

  * **Response Body**:

    ```json
    {
        "status": "string", // 状态码，返回操作状态信息（操作成功或失败）
        "data": {
            // 数据信息
        }
    }
    ```

  * 上层应用对北向API基于http协议，使用 `<主机IP>:<端口>` (本组使用阿里云ECS，服务器公网地址112.124.43.208:9090) `/service/devices_manage/<服务名称>` 进行调用。

  * 请求的回复仍然使用JSON格式来表达信息。

  * 如请求URL使用正确，参数有效，并成功调用API。所有API回复体均返回JSON格式 `{"status":"success"，"data":"<数据>"}`，以及http协议中相应的状态码（部分接口data项为空）。

  * 如请求URL使用错误，基于http协议进行报错，由Sanic框架自动管理。

  * 如请求URL使用正确，参数使用出现错误(如key单词拼写有误，亦或查询设备不存在)，本协议有两套方案：

    1.  所有API回复体均返回JSON格式 `{"status":"fail", "type":"<调用的操作类型，如GENERALOP>", "message": "An Error Has Occurred"}`，以及http协议中状态码(视情况定，可能是400或500）。
          * 例子：`{"status": "fail", "type":"DEVICEOP_ERROR", "message": str(e)}`，status=e.Error\_Code
          * 例子：`{"status": "fail", "type":"GENERAL_ERROR", "message": "Content-Type must be application/json"}`，status=400
    2.  基于Python sanic框架进行报错 `{"description":"Internal Server Error", "status":500, "message":"The server encountered an internal error and cannot complete your request."}`

#### 3.2.2 南向接口设计

**1. 心跳协议和交互设计**

**Request PDU (Ping):**

```json
{
    "type": "ping_pong",
    "Headers": {},
    "data": "ping"
}
```

**Response PDU (Pong):**

```json
{
    "type": "ping_pong",
    "Headers": {},
    "data": "pong"
}
```

  * **交互设计**:
      * 客户端先与服务端建立心跳连接，待服务端鉴权完成后，客户端正式启动心跳协程，状态报文上传等协程，与服务端开始交互。
      * 如果一次ping接收到了pong，下次ping和这次ping发送时间间隔 5s（一次心跳间隔，相当于业务数据发送替代了一次心跳）。（发送ping后最多等3s pong）
      * 如果这次ping未接收到pong，不延时直接发送下一次ping。
      * 状态报文每 15s 上传一次，上传状态报文时就不发送心跳ping帧，心跳下次发送业务报文的时间戳延迟到 latestBusinessTimeStamp后的5s。
      * 对于客户端，业务数据（比如固定发送的状态信息）和心跳数据如果发送后未接收到回应，都会增加failureCount的失败计数，在心跳协程中如果检测到失败计数达到3，就会断开连接，启动重连。
      * 重连间隔为10s，而默认最大重连次数是5次，用户应可以自行配置重连次数。
      * 服务端总是应该在5s左右接收到客户端的一条信息（不论是心跳信息还是状态信息）。由于网络延迟，将服务端接收客户端信息的容忍延时定为 (7.5, 5.5\~)，其中当该设备的failureCount为0时，可以接受7.5s内才信息，但是如果超时就会增加failure计数，failure为大于0时容忍时间缩减到5.5s，如果失败计数达到3就断开和该边端设备连接，并析构相应资源（如该边端设备的信息字典）。

**2. 登录鉴权设计**

**Request PDU:**

```json
{
    "device_id": "string",
    "password": "string"
}
// 或
{
    "device_sn": "string",
    "device_model": "string",
    "password": "string"
}
```

**Response PDU:**

```json
// 成功时：
{
    "status": "success",
    "data": {
        "device_id": "string"
    }
}
// 失败时：
{
    "status": "fail",
    "message": "string"
}
```

  * **交互设计**：
      * 边端和云端连接建立后首先登录鉴权。
      * 边端向云端发送id和password（或者SN\_Model对和password），云端接收到后查数据库检验密码，正确就保持连接，回信 `{"status":"success","data":{"device_id":"string"}}`，否则回信status置为fail，并关闭连接。
      * 云端如果发现登录请求PDU缺少参数，直接回信连接失败（status置为fail）再直接切断连接。
      * 边端如果接收到登录成功信息，那么边端就会继续和云端开展心跳交互、状态报文上传等交互过程，否则就会等待10s发起重连。

**3. 状态报文上传设计**

**Request PDU:**

```json
{
    "type": "upload_status_info", // 发送报文类型
    "Headers": {},
    "data": { // 具体状态信息数据
        "device_id": "string",
        "CPU_info": {
            "user_cpu_time": 4112.78, // 示例数据
            "system_cpu_time": 923.85, // 示例数据
            "idle_cpu_time": 179258.0, // 示例数据
            "io_wait_cpu_time": 120.6 // 示例数据
        },
        "Memory_info": {
            "total_memory_mb": 1673, // 示例数据
            "free_memory_mb": 91,    // 示例数据
            "buff_cache_mb": 258     // 示例数据
        },
        "Disk_info": {
            "root_total_size_mb": 39942, // 示例数据
            "root_used_size_mb": 10509,  // 示例数据
            "root_used_percent": 27.6    // 示例数据
        },
        "dev_state": "string" // 设备在线信息，"online"或"offline"
    }
}
```

**Response PDU:**

```json
{
    "type": "send_statusInfo_response",
    "Headers": {},
    "data": {}
}
```

  * **交互设计**：
      * 边端每15s进行一次状态报文的上传，上传后最多等待3s云端回应，否则记为超时，贡献failureCount。
      * 边端如果成功接收云端回应，下次边端状态报文上传和这次边端状态报文上传就相隔15s，否则立即重新发送状态数据。
      * 云端接收到相应边端设备的状态报文上传信息后，就会更新全局设备状态字典下该设备的状态数据。

**4. 指令执行设计**

**Request PDU (这里是云端请求):**

```json
{
    "type": "give_order", // 发送报文的类型
    "Headers": {
        "isInner": true, // 此为示例数据，表示其为bool类型
        "order_type": "string" // 指令类型
    },
    "data": {
        "device_id": "string",
        "params": "", // 仅框架外指令有，对于框架外指令必填
        "remote_dir": "/var/log/devices_management" // 仅框架内状态日志上传指令有，本服务日志默认存储在该位置
    }
}
```

**Response PDU (这里是边端响应):**

```json
{
    "type": "upload_instruction_result", // 发送报文的类型
    "status": "string", // 指令执行结果
    "Headers": {
        "message": "string"
    },
    "data": {}
}
```

  * **交互设计**:
      * 一般指令执行流程：
        1.  顶层业务通过相应北向接口请求微服务向相应设备下达指令。
        2.  微服务经消息透传将请求发送给边端处理。
        3.  边端接收到指令下达消息后交给指令执行模块处理。
        4.  若处理成功，回信成功信息；若失败，回信失败信息。
        5.  云端接收到相应指令执行结果后返回给顶层业务，如果10s内未接收到指令执行结果，返回给顶层业务指令执行失败。
      * 对于框架内重启指令的特殊执行流程：
          * 注：因为重启指令会重启进程，为了防止云端还未收到指令执行信息Ws连接已被断开，我们额外加入了确认机制。

**重启确认报文设计 (Request PDU - 边端请求云端确认重启):**

```json
{
    "type": "upload_instruction_result", // 发送报文的类型
    "status": "success",
    "Headers": {
        "message": "wait Server Confirm"
    },
    "data": {}
}
```

**重启确认报文设计 (Response PDU - 云端对确认重启请求的响应):**

```json
{
    "type": "restart_confirm", // 发送报文的类型
    "Headers": {},
    "data": {}
}
```

  * **特殊执行流程**：
    1.  顶层业务通过相应北向接口请求微服务向相应设备重启指令。
    2.  微服务经消息透传将重启请求发送给边端处理。
    3.  边端接收到重启请求后，发送“是否确认重启”的请求给微服务。
    4.  微服务接收到该请求后，发送“重启确认响应”，然后返回给顶层业务“设备成功重启的信息”，如果10s内未接收到这条请求，返回给顶层业务“重启失败”。
    5.  边端发送“是否确认重启”的请求后，最多等待3s云端的重启确认，如果3s内接收到了“重启确认”，边端执行重启；否则边端也直接重启。

### 3.3 持久化存储设计

#### 3.3.1 实体定义

1.  **边端设备**
      * 基本信息：设备编号、设备名称、设备描述、创建时间、更新时间。
      * 硬件信息：硬件序列号、硬件型号、以太网卡MAC地址、WiFi网卡MAC地址、LTE IMEI编码（SIM卡唯一标识）。
      * 认证信息：Salt、Secret（Password & Salt 散列）。
      * 软件信息：基础程序版本号、基础程序上次更新时间、基础程序状态、业务程序版本号、业务程序上次更新时间、业务程序状态。
2.  **设备分组**
      * 基本属性：分组编号、分组名称、分组描述、创建时间、更新时间。
3.  **设备与分组关系**
      * 基本信息：设备编号、分组编号。
4.  **设备密码**
      * 基本信息：设备编号、密码。

#### 3.3.2 Mysql数据库的设计

  * **基础表**
      * 设备表 devices
      * 设备分组表 group\_info
      * 设备与分组关系表 relations

#### 3.3.3 即时存储信息（存储在python字典中）

  * **CPU信息**：user cpu time、system cpu time、idle cpu time、io wait cpu time
  * **内存信息**：内存总量、空闲内存、buff/cache总量
  * **硬盘信息**：分区磁盘大小、根目录所占空间比

#### 3.3.4 设备日志

保存各种关键事件的执行时间和执行结果，如：发起连接、登录鉴权、指令下达、状态信息上传。

### 3.4 接口详细设计

#### 3.4.1 北向接口

接口设计概况一览（详情见[北向接口协议设计之PDU、API设计](https://uestc.feishu.cn/docx/X704dwOZfoZ0VvxKawrcapoan1g)）

#### 3.4.2 南向接口

南向接口主要面向边端设备提供边端设备对接服务相关接口，以 Web Socket 作为通信协议，以函数接口形式暴露服务。要求采用JSON-RPC构建应用层通信协议。

**接口需求：**

| 功能要求 | 功能备注 |
| :--- | :--- |
| 实现设备的登陆验证和鉴权 | 发起连接后首先登录鉴权，鉴权不成功连接会被断开 |
| 实现设备状态信息的接收和处理 | 利用状态报文中上传的状态信息，实时保存在python字典中并更新 |
| 实现设备指令的下发 | 实现相关接口接收相关指令信息，以json-rpc通信协议向目标边端设备透传相关的指令信息。 |
| 实现心跳包的处理和响应 | 实现对心跳信息进行处理并发送pong帧，若未接收到边端请求次数过多（超过3），断开连接 |

**接口实现：**

  * URI制定为 `/ws`，边端只和云端维持这一个websocket长连接。
  * 各功能模块和报文信息的处理采用**异步协程的方式进行并发处理**。
  * 详见下文 南向接口核心代码逻辑。

### 3.5 边端设备基础进程

边端设备基于 `asyncio` 实现单线程内的多协程并发处理，主要包含以下核心协程任务：

| 协程/任务名称 | 对应函数 | 功能说明 | 触发/运行机制 |
| :--- | :--- | :--- | :--- |
| **主连接协程** | `connect()` | 负责建立与云端的 WebSocket 连接，执行登录鉴权，并调度其他子协程。 | 程序启动时运行，支持断线自动重连。 |
| **心跳保活协程** | `ping_pong()` | 周期性发送 Ping 帧，监测连接健康状态。若超时未收到 Pong 或失败次数过多，触发重连。 | 连接建立后启动，默认 5s 周期。 |
| **状态上报协程** | `uploadStatusInfo()` | 周期性采集本地 CPU/内存/磁盘信息并上报云端。 | 连接建立后启动，默认 15s 周期。 |
| **公共接收协程** | `public_recv()` | 监听 WebSocket 消息，分发 Pong 响应、状态确认及指令请求。 | 连接建立后启动，持续监听。 |
| **指令执行任务** | `execOrder()` | 处理云端下发的指令（如重启、日志上传、自定义业务指令）。 | 由 `public_recv` 收到 `give_order` 消息后异步 `create_task` 触发。 |


### 3.6 核心代码逻辑设计

#### 3.6.1 项目代码层次结构设计

| 目录/文件 | 说明 |
| :--- | :--- |
| `.git/` | Git版本控制文件夹 |
| `.venv/` | Python虚拟环境文件夹 |
| `src/` | 项目主代码目录 |
| `src/controller_part/` | **边端controller部分** |
| `src/controller_part/controller/` | 边端基础依赖库：controller包 |
| `src/controller_part/controller/__init__.py` | 包初始化文件 |
| `src/controller_part/controller/config.py` | 配置模块 |
| `src/controller_part/controller/controller_main.py` | 边端核心逻辑模块 |
| `src/controller_part/controller/execorder.py` | 指令执行模块 |
| `src/controller_part/controller/getStatusInfo.py` | 获取状态信息模块 |
| `src/controller_part/controller/logger.py` | 日志记录模块 |
| `src/controller_part/controller/sftp_upload.py` | SFTP文件上传模块 |
| `src/controller_part/controller/test_start_1.py` | 测试脚本1 |
| `src/controller_part/controller/test_start_2.py` | 测试脚本2 |
| `src/controller_part/controller/User.py` | 用户配置 |
| `src/Server/` | **服务端相关部分** |
| `src/Server/api.py` | API 接口逻辑 |
| `src/Server/database_ini.json` | 数据库初始化配置文件 |
| `src/Server/Database_OP.py` | 数据库操作模块 |
| `src/Server/pre_SQL.sql` | 数据库预定义SQL脚本 |
| `src/Server/south_api_core.py` | 南向接口核心逻辑实现 |
| `src/Server/start.sh` | 启动服务的Shell脚本 |
| `.gitignore` | Git忽略规则文件 |
| `README.md` | 项目说明文档 |
| `requirements.txt` | Python依赖库清单 |

**3.6.1.1 项目模块间依赖关系阐明：**

  * `controller_part`下：启动脚本 -\> `controller.controller_main` -\> ...(其它各个模块）
  * `Server` 下：
      * `api` -\> `Database_OP`
      * `api` -\> `south_api_core`
      * `south_api_core` -\> `Database_OP`

**3.6.1.2 项目技术栈：**

  * Python Sanic
  * 异步mysql操作库 aiomysql
  * 用于sftp上传的异步库 asyncssh
  * 用于哈希加盐加密的加密库 bcrypt
  * 雪花id生成库 snowflake-id

#### 3.6.2 北向接口核心代码逻辑设计

**3.6.2.1 普通北向接口**

`DataBase_OP` 和 `api` 下配合形成异常处理体系。

**DataBase\_OP (异常定义):**

```python
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
```

**api (异常处理):**

```python
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
```

**api (辅助函数):**

```python
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

# 封装将输入的json展平的函数
def flatten_json(nested_json, parent_key='', sep='_'):
    items = []
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                items.extend(flatten_json(item, f"{new_key}{i+1}", sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# 封装通用前置入参检查,result是传出参数
def checkJsonParams(request:Request,required_fields:list,result:dict):
    if request.headers.get('Content-Type') != 'application/json':
        result["result"] = response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Content-Type must be application/json"}, status=400)
        return False
    if request.json is None:
        result["result"] = response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "please provide legal json!"}, status=400)
        return False
    if check_Required_params(flatten_json(request.json),required_fields) is False:
        result["result"] = response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "Missing required parameters!"}, status=400)
        return False
    ###
    # 还可以加上更严格的类型检查逻辑...
    ###
    return True
```

**DataBase\_OP (常用操作封装):**

```python
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
        sql1="SELECT device_id FROM devices WHERE device_id=%s;"
        await cursor.execute(sql1,(device_id,))
    elif SN_Model is not None:
        sql2="SELECT device_id FROM devices WHERE (hardware_sn=%s AND hardware_model=%s);"
        await cursor.execute(sql2,SN_Model)
    else:
        raise DeviceOPError("Missing required parameters!",400)
    result = await cursor.fetchall()
    return None if len(result)==0 else result

async def isGroupExist(cursor,group_id=None,group_name=None):
    if group_id is not None:
        sql1="SELECT group_id FROM group_info WHERE group_id=%s;"
        await cursor.execute(sql1,(group_id,))
    elif group_name is not None:
        sql2="SELECT group_id FROM group_info WHERE group_name=%s;"
        await cursor.execute(sql2,(group_name,))
    else:
        raise GroupOPError("Missing required parameters!",400)
    result = await cursor.fetchall()
    return None if len(result)==0 else result

async def isRelationExist(cursor,device_id,group_id):
    sql="SELECT device_id FROM relations WHERE (device_id=%s AND group_id=%s);"
    await cursor.execute(sql,(device_id,group_id))
    result = await cursor.fetchall()
    return None if len(result)==0 else result
```

**DataBase\_OP (事务化操作封装 - 以DeviceOP为例):**

```python
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
                    sql = "INSERT INTO devices(device_id,device_name,device_type,hardware_sn,hardware_model,software_version,software_last_update,nic1_type,nic1_mac,nic1_ipv4,nic2_type,nic2_mac,nic2_ipv4,dev_description,dev_state,password,created_time,updated_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
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
                        sql1="SELECT device_id,device_name,device_type,hardware_sn,hardware_model,software_version,software_last_update,nic1_type,nic1_mac,nic1_ipv4,nic2_type,nic2_mac,nic2_ipv4,dev_description,dev_state,password,created_time,updated_time FROM devices WHERE device_id=%s;"
                        await cursor.execute(sql1,(device_id,))
                    elif SN_Model is not None:
                        sql2="SELECT device_id,device_name,device_type,hardware_sn,hardware_model,software_version,software_last_update,nic1_type,nic1_mac,nic1_ipv4,nic2_type,nic2_mac,nic2_ipv4,dev_description,dev_state,password,created_time,updated_time FROM devices WHERE (hardware_sn=%s AND hardware_model=%s);"
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

    # 查询所有设备信息
    async def query_all(self):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    sql = "SELECT device_id,device_name,device_type,hardware_sn,hardware_model,software_version,software_last_update,nic1_type,nic1_mac,nic1_ipv4,nic2_type,nic2_mac,nic2_ipv4,dev_description,dev_state,password,created_time,updated_time FROM devices;"
                    await cursor.execute(sql)
                    result = await cursor.fetchall()
                    await conn.commit()
                    result = [WrapperToJson(item,isDevice=True) for item in result]
                    return result
        except Exception as e:
            await conn.rollback()
            if isOPError(e):
                raise
            else:
                raise DataBaseError(f"A database error occurred: {e}")

    # 删除设备（设备分组关系也要一起删）
    async def delete(self,device_id):
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 先查询是否有该设备
                    if (await isDeviceExist(cursor,device_id=device_id) is None):
                        raise DeviceOPError("Device NOT FOUND",404)
                    # 再正式删除设备
                    # 先删除-设备分组关系
                    sql1 = "DELETE FROM relations WHERE device_id=%s"
                    await cursor.execute(sql1,(device_id,))
                    # 再删除设备
                    sql2 = "DELETE FROM devices WHERE device_id=%s"
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
                
# ............ # ............ # ............
deviceOP = DeviceOP() # 暴露单例对象
```

**api (设备注册接口实现):**

```python
# 设备注册
@app.post('/service/devices_manage/device_add')
async def device_add(request:Request):
    # 参数检验部分，要求必须提供密码
    result={} # 传出参数
    if checkJsonParams(request,device_required_fields,result) is False: # 检查出错误
        return result["result"]
    # 额外参数类型检验，这里检验password
    dic = flatten_json(request.json)
    if type(dic["password"]) is not str:
        return response.json({"status": "fail", "type":"GENERAL_ERROR" , "message": "password shoule be string!"}, status=400)
    
    # 正式处理部分,id和state新增（或重置）
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
```

**3.6.2.2 和南向接口配合的北向接口（api模块下）**

**获取设备状态信息:**

```python
# 查询设备状态信息
@app.get("/service/devices_manage/device_statusInfo_query/<device_id>")
async def device_statusInfo_query(request,device_id):
    result = queryDeviceStatusInfo(device_id)
    if result is None:
        return response.json({"status":"fail","message":"wrong device_id OR offline device."})
    else:
        # print(result)
        return response.json({"status":"success","data":result})
```

**下达指令:**

```python
# 下发指令
@app.post("/service/devices_manage/give_order")
async def give_order(request):
    result={}
    if checkJsonParams(request,["device_id","order"],result) is False: # 至少需要提供device_id和order
        return result["result"]
    try:
        dic = request.json
        device_id = dic["device_id"]
        if type(dic["order"]) is not str:
            return response.json({"status":"fail","message":"order must be string."})
            
        # print(dic)
        deal_dic = {"type":"give_order","Headers":{"order_type":dic["order"]},"data":{"device_id":dic["device_id"]}}
        # print(deal_dic)
        if dic["order"] in ("restart","upload_log"):
            deal_dic["Headers"]["isInner"] = True
            if dic["order"] == "upload_log":
                deal_dic["data"]["remote_dir"] = "/var/log/devices_management"
        else:
            deal_dic["Headers"]["isInner"] = False
            if ("params" not in dic) or (isinstance(dic["params"],dict) is False):
                return response.json({"status":"fail","message":"invalid JSON."})
            else:
                deal_dic["data"]["params"] = dic["params"]
        deviceResponse = await giveOrder(device_id,deal_dic)
        return deviceResponse
    except Exception as e:
        # print(e)
        return response.json({"status":"fail","message":"Server unknown error."})
```

#### 3.6.3 南向接口核心代码逻辑设计（south\_api\_core)

**api模块下南向接口处理总入口:**

```python
# 南向接口
@app.websocket("/ws")
async def Ws_Serve(request,ws:WebSocketClientProtocol):
    # print("hhh")
    await Ws_Serve_Core(ws)
```

**核心启动函数:**

```python
async def Ws_Serve_Core(ws:WebSocketClientProtocol):
    # 先登录鉴权
    result = {} #传出参数
    if await loginCheck(ws,result) is False:
        return
        
    # 登录成功后，做准备工作
    Events = get_events()
    device_id = result["device_id"]
    await TransDeviceState(device_id,"online")
    device_websocket_map[device_id] = {"ws":ws,"receiveOrderResultEvent":Events["receive_instruction_result"]}
    DeviceFailureCount[device_id] = 0 # 初始化心跳失败计数
    
    # 再正式启动南向接口服务
    await public_recv(ws,Events,device_id) # 启动心跳、状态报文、以及指令下达的公共处理模块
```

**登录鉴权函数:**

```python
# 1.登录鉴权，可基于ID或SN_MODEL对或密码鉴权
async def loginCheck(ws:WebSocketClientProtocol,result):
    try:
        loginInfo = await asyncio.wait_for(ws.recv(),timeout=5)
        loginInfo = safe_json_loads(loginInfo)
        if loginInfo is False:
            await ws.send(json.dumps({"status":"fail","message":"Invalid Json"}))
            return False
        if "password" not in loginInfo:
            await ws.send(json.dumps({"status":"fail","message":"Not provide password"}))
            return False
        if "device_id" in loginInfo:
            try:
                queryResult = await deviceOP.query(device_id=loginInfo["device_id"])
            except Exception as e:
                await ws.send(json.dumps({"status":"fail","message":str(e)}))
                return False
            if bcrypt.checkpw(loginInfo["password"].encode("utf-8"),queryResult["password"].encode("utf-8")) is False:
                await ws.send(json.dumps({"status":"fail","message":"password Not Correct"}))
                return False
            else:
                await ws.send(json.dumps({"status":"success","data":{"device_id":queryResult["device_id"]}}))
                result["device_id"] = queryResult["device_id"]
                return True
        elif ("device_sn" in loginInfo) and ("device_model" in loginInfo):
            try:
                queryResult = await deviceOP.query(SN_Model=(loginInfo["device_sn"],loginInfo["device_model"]))
                # print(queryResult)
            except Exception as e:
                await ws.send(json.dumps({"status":"fail","message":str(e)}))
                return False
            if bcrypt.checkpw(loginInfo["password"].encode("utf-8"),queryResult["password"].encode("utf-8")) is False:
                await ws.send(json.dumps({"status":"fail","message":"password Not Correct"}))
                return False
            else:
                await ws.send(json.dumps({"status":"success","data":{"device_id":queryResult["device_id"]}}))
                result["device_id"] = queryResult["device_id"]
                return True
        else:
            await ws.send(json.dumps({"status":"fail","message":"Missing required Parameters!"}))
            return False
    except asyncio.TimeoutError:
        await ws.send(json.dumps({"status":"fail","message":"TimeOut."}))
        return False
    except Exception as e:
        # print(e)
        await ws.send(json.dumps({"status":"fail","message":"Unknown Error"}))
        return False
```

**设备即时信息保存字典:**

```python
DevicesOnlineState = {} # 设备是否在线信息
DevicesStatusInfo = {} # 全局在线设备的状态信息字典
DeviceFailureCount = {} # 心跳失败计数统计字典

def queryDeviceStatusInfo(device_id):
    if (device_id not in DevicesStatusInfo) or (device_id not in DevicesOnlineState):
        return None
    Result =  {"device_id":device_id}
    Result.update(DevicesStatusInfo[device_id])
    Result.update({"dev_state":DevicesOnlineState[device_id]})
    return Result
```

**公共接受点函数 (public\_recv):**

```python
# 获取各任务分派事件列表
def get_events():
    Events = {
        # "ping_pong":{"event":asyncio.Event(),"data":None},
        # "receive_status_info":{"event":asyncio.Event(),"data":None},
        "receive_instruction_result":{"event":asyncio.Event(),"data":None}
    }
    return Events

# 定义公共接收入口和分派函数
async def public_recv(ws:WebSocketClientProtocol,Events,device_id):
    while True:
        try:
            if DeviceFailureCount[device_id] == 0:
                t = (5 + 2.5)
            else:
                t = 5.5
              
            response = await asyncio.wait_for(ws.recv(),timeout=10)
            response_data = safe_json_loads(response)
            print(response_data) # 打印接收到的报文，仅用于调试
            if response_data is None:
                continue
            
            ##########考虑状态转换
            if DevicesOnlineState[device_id]!= "online":
                await TransDeviceState(device_id,"online")
            #####################
            
            # 启动分发
            if response_data.get("type") == "ping_pong":
                await ws.send(json.dumps({"type":"ping_pong","Headers":{},"data":"pong"})) # 处理心跳
            elif response_data.get("type") == "upload_status_info":
                DevicesStatusInfo[device_id] = response_data["data"]
                await ws.send(json.dumps({"type":"send_statusInfo_response","Headers":{},"data":{}})) # 处理状态报文回信
            # 指令下达回信处理
            elif response_data.get("type") == "upload_instruction_result":
                Events["receive_instruction_result"]["data"] = response_data
                Events["receive_instruction_result"]["event"].set()
            else:
                pass
        except asyncio.TimeoutError:
            if DevicesOnlineState[device_id]!= "Unknown":
                await TransDeviceState(device_id,"Unknown")
            DeviceFailureCount[device_id] += 1 # 失败次数递增
            if DeviceFailureCount[device_id] >= 3: # 失败三次断开连接
                print(f"Timeout! No ping received within 5 seconds.")
                freeResource(device_id)
                await TransDeviceState(device_id,"offline")
                break  # 退出业务发送
            continue #超时，开始下次等待
        except (websockets.exceptions.ConnectionClosed,asyncio.CancelledError): # 处理连接关闭异常
            freeResource(device_id)
            await TransDeviceState(device_id,"offline")
            break
        except Exception: #处理其它异常
            freeResource(device_id)
            await TransDeviceState(device_id,"offline")
            break
```

**指令下发函数 (giveOrder):**

```python
# 定义指令下发函数
devices_instruction_dealing = {} # 记录哪个设备正在处理指令的字典
async def giveOrder(device_id,order):
    if (device_id not in DevicesOnlineState) or (DevicesOnlineState[device_id] == "offline"):
        return response.json({"status":"fail","message":"Device is offline!"})
    if DevicesOnlineState[device_id] == "Unknown":
        return response.json({"status":"fail","message":"Device state is Unknown!"})
        
    if ((device_id in devices_instruction_dealing) and devices_instruction_dealing.get(device_id) == True): # 对单设备的并发控制
        return response.json({"status":"fail","message":"Device busy!"})
    devices_instruction_dealing[device_id] = True
    
    # print(device_websocket_map)
    Ws = device_websocket_map[device_id]["ws"]
    ReceiveResultEvent = device_websocket_map[device_id]["receiveOrderResultEvent"]
    
    # 下达指令
    try:
        await Ws.send(json.dumps(order))
        await asyncio.wait_for(ReceiveResultEvent["event"].wait(),timeout=10) # 当边端回应时可继续，但不能超过10s
        ReceiveResultEvent["event"].clear()
        
        if order["Headers"]["order_type"] == "restart": # 对于重启，额外确认
            try:
                await Ws.send(json.dumps({"type":"restart_confirm","Headers":{},"data":{}}))
            except Exception as e:
                pass
                
        result = ReceiveResultEvent["data"]
        if result["status"] == "success":
            devices_instruction_dealing[device_id] = False
            return response.json({"status":"success","data":{}})
        else:
            devices_instruction_dealing[device_id] = False
            # print(result)
            return response.json({"status":"fail","message":result["Headers"]["message"]})
    except Exception:
        devices_instruction_dealing[device_id] = False
        return response.json({"status":"fail","message":"Unknown Error!"})
```

#### 3.6.4 边端控制器核心代码逻辑设计

**封装全局配置对象模块 (controller.config):**

```python
# 配置对象，用于初始化时指定配置参数
import os
current_dir = os.path.dirname(os.path.abspath(__file__))

class Config:
    def __init__(self, host=None, port=None, sftp_host=None, sftp_port=None, sftp_username=None, sftp_password=None, device_id=None, device_password=None, device_hardware_sn=None, device_hardware_model=None, device_log_dir=current_dir, device_log_name="device.log", max_retries=5, outer_order_dict={}):
        # ...... 略
        
    def Set(self, host=None, port=None, sftp_host=None, sftp_port=None, sftp_username=None, sftp_password=None, device_id=None, device_password=None, device_hardware_sn=None, device_hardware_model=None, device_log_dir=None, device_log_name=None, max_retries=None, outer_order_dict={}):
        # ...... 略

# 暴露单例对象
config:Config = Config()
```

**封装本地日志记录模块 (controller.logger):**

```python
import logging
from logging.handlers import TimedRotatingFileHandler
import os
# from controller.config import config

# 暴露日志单例对象
myLogger = logging.getLogger("ThreeDayRotatingLogger")

def SetLogMessage(logger_object, log_dir, log_path):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    # 配置日志处理器
    handler = TimedRotatingFileHandler(
        log_path, when="D", interval=3, backupCount=0, encoding="utf-8"
    )
    # 设置日志格式
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    # 配置日志对象
    logger_object.setLevel(logging.DEBUG)  # 日志级别
    logger_object.addHandler(handler)

# 测试日志
if __name__ == "__main__":
    SetLogMessage(myLogger, "./test_log_dir")
    myLogger.info("This is a test log.")
    myLogger.info("Logs will rotate every 3 days.")
```

**封装SFTP日志上传模块 (controller.sftp\_upload):**

```python
import asyncio
import asyncssh
import os
from controller.logger import myLogger

async def sftp_upload_log(device_id: str, log_file: str, remote_dir: str, sftp_host: str, sftp_port: int, sftp_username: str, sftp_password: str):
    """
    上传日志到远程 SFTP 服务器。
    """
    # 确保日志目录和文件存在，不存在就创建
    if not os.path.exists(log_file):
        with open(log_file, 'w') as file:
            pass
    remote_file = os.path.join(remote_dir, f"{device_id}.log")
    
    # 使用 asyncssh 执行 SFTP 上传操作
    try:
        myLogger.info("try to upload log.")
        async with asyncssh.connect(sftp_host, port=sftp_port, username=sftp_username, password=sftp_password,known_hosts=None) as conn:
            # print("uchhhhhhhheueuuuuuuuu")
            sftp = await conn.start_sftp_client()
            # 上传文件
            # print(log_file)
            # print(remote_file)
            await sftp.put(log_file, remote_file)
            myLogger.info(f"Successfully uploaded {log_file} to {remote_file}")
            return True
    except Exception as e:
        myLogger.error(f"Failed to upload log file {log_file}: {e}")
        return False
```

**封装状态信息获取模块 (controller.get\_StatusInfo):**

```python
import psutil
import json
import asyncio
import websockets
import random

def get_cpu_info():
    """获取CPU信息"""
    cpu_times = psutil.cpu_times()
    return {
        "user_cpu_time": cpu_times.user,
        "system_cpu_time": cpu_times.system,
        "idle_cpu_time": cpu_times.idle,
        "io_wait_cpu_time": getattr(cpu_times, "iowait", 0)
    }

def get_memory_info():
    """获取内存信息"""
    memory_info = psutil.virtual_memory()
    return {
        "total_memory_mb": memory_info.total // 1024 // 1024,
        "free_memory_mb": memory_info.free // 1024 // 1024,
        "buff_cache_mb": (memory_info.buffers + memory_info.cached) // 1024 // 1024
    }

def get_disk_info():
    """获取磁盘信息（仅获取根目录信息）"""
    root_disk = psutil.disk_usage('/')
    return {
        "root_total_size_mb": root_disk.total // 1024 // 1024,
        "root_used_size_mb": root_disk.used // 1024 // 1024,
        "root_used_percent": root_disk.percent
    }

def collect_status_info():
    """收集设备所有状态信息"""
    return {
        "CPU_info": get_cpu_info(),
        "Memory_info": get_memory_info(),
        "Disk_info": get_disk_info()
    }

def easyTest():
    return {
        "position":random.randint(1,100)
    }
```

**边端基础依赖库的接口暴露函数 (controller.controller\_main):**

```python
def startControllerBasicApp(host=None, port=None, sftp_host=None, sftp_port=None, sftp_username=None, sftp_password=None, device_id=None, device_password=None, device_hardware_sn=None, device_hardware_model=None, device_log_dir=None, device_log_name=None, max_retries=None, outer_order_dict={}):
    """
    边端基础应用启动函数
    """
    global config
    config.Set(host=host, port=port, sftp_host=sftp_host, sftp_port=sftp_port, sftp_username=sftp_username, sftp_password=sftp_password, device_id=device_id, device_password=device_password, device_hardware_sn=device_hardware_sn, device_hardware_model=device_hardware_model, device_log_dir=device_log_dir, device_log_name=device_log_name, max_retries=max_retries, outer_order_dict=outer_order_dict)
    SetLogMessage(myLogger,config.device_log_dir,config.device_log_local_path) # 配置完config后再配置日志
    asyncio.run(connect()) # 启动连接
```

**边端基础依赖主协程和事件分派机制 (controller.controller\_main):**

```python
# 6.发起连接
async def connect():
    global failureCount,Ws,Flag
    retries = 0
    while retries < config.max_retries:
        try:
            myLogger.info("Ready to connect to Server.")
            async with websockets.connect(config.server_url) as ws: # 发起webSocket连接
                myLogger.info("successfully connect to Server.")
                Ws = ws # 保存最新连接
                failureCount = 0 # 重置失败次数
                Flag = 0 # 重置Flag
                
                # 先鉴权
                if await Login(ws) is False:
                    continue
                # 写事件分派
                events = get_events()
                asyncio.create_task(public_recv(ws,events)) # 异步添加公共接受点任务
                asyncio.create_task(uploadStatusInfo(ws,events["receive_statusSend_response"])) # 异步添加上传状态信息任务
                await ping_pong(ws,events["ping_pong"]) # 开始ping-pong 心跳
                
        except Exception as e:
            myLogger.error(f"Error: {e},disconnect to Server.")
        myLogger.info("Server Offline. try-reconnect 10s later.")
        retries += 1
        await asyncio.sleep(10) # 重连间隔10s

def get_events():
    Events = {
        "ping_pong":{"event":asyncio.Event(),"data":None},
        "receive_statusSend_response":{"event":asyncio.Event(),"data":None},
        # "receive_sendInstruction":{"event":asyncio.Event(),"data":None}
        "restart_confirm":{"event":asyncio.Event(),"data":None} # 这个Event仅用来针对重启指令
    }
    return Events

# 2.定义公共接收入口和分派函数
async def public_recv(ws:WebSocketClientProtocol,Events):
    while True:
        try:
            response = await ws.recv()
            response_data = safe_json_loads(response)
            print(response_data) # 打印接收到的消息，用于调试
            
            if response_data.get("type") == "ping_pong": # 接收到pong帧
                Events["ping_pong"]["data"] = response_data
                Events["ping_pong"]["event"].set()
            elif response_data.get("type") == "send_statusInfo_response": # 接收到对状态上传的回应
                Events["receive_statusSend_response"]["data"] = response_data
                Events["receive_statusSend_response"]["event"].set()
            elif response_data.get("type") == "give_order":
                # 接收到下达指令
                asyncio.create_task(execOrder(ws,response_data,Events["restart_confirm"]))
            elif response_data.get("type") == "restart_confirm":
                Events["restart_confirm"]["data"] = response_data
                Events["restart_confirm"]["event"].set()
            else:
                pass
        except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError): # 处理连接关闭异常
            break
        except Exception: #处理其它异常
            break
```

**心跳处理协程 (controller.controller\_main):**

```python
# 3.定义心跳处理函数
async def ping_pong(ws:WebSocketClientProtocol,event:asyncio.Event):
    global failureCount,Flag
    while True:
        try:
            while Flag == 1:
                Flag = 0
                await asyncio.sleep(wait_time_from(latestBussinessTimeStamp,5))
            
            # 因为网络波动客观存在，因此总是设置 “发起ping请求间隔” 为5s
            await ws.send(json.dumps({"type":"ping_pong","Headers":{},"data":"ping"}))
            last_send_ping = time.time()
            myLogger.info(f"send ping")
            
            await asyncio.wait_for(event["event"].wait(),timeout=3) # 发出ping到接收pong最多等3秒
            event["event"].clear()
            failureCount = 0 # 成功一次后失败次数就清零
            Flag = 0 # 观察后5s内是否有别的业务报文上传
            myLogger.info(f"successfully receive pong")
            await asyncio.sleep(wait_time_from(last_send_ping,5)) # 等到了pong，就有5s的容许期
        except asyncio.TimeoutError:
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接
                myLogger.info(f"Timeout! No pong received within 5 seconds.")
                failureCount = 0
                break  # 退出业务发送，准备重连
            continue #超时，直接开始下次心跳发送
        except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError): # 处理连接关闭异常
            break # 退出循环，停止业务
        except Exception as e:
            myLogger.error(f"Error during business: {e}")
            break  # 发生错误退出循环，停止业务
```

**状态报文上传协程 (controller.controller\_main):**

```python
# 4.定义状态上传函数
async def uploadStatusInfo(ws:WebSocketClientProtocol,event:asyncio.Event):
    # 发起请求间隔为15s
    global failureCount,Flag,latestBussinessTimeStamp,Ws
    while True:
        try:
            StatusInfo = getStatusInfo.collect_status_info()
            await ws.send(json.dumps({"type":"upload_status_info","Headers":{},"data":StatusInfo}))
            myLogger.info(f"Send StatusInfo")
            Flag = 1
            last_send_status = latestBussinessTimeStamp = time.time()
            await asyncio.wait_for(event["event"].wait(),timeout=3) # 一样最多等3秒
            event["event"].clear()
            failureCount = 0 # 成功一次后失败次数就清零
            myLogger.info(f"successfully receive response of statusSend")
            await asyncio.sleep(wait_time_from(last_send_status,15)) # 每隔15s发送状态报文
        except asyncio.TimeoutError:
            if ws != Ws: # 若连接断开，则不再发送状态报文
                break
            myLogger.info(f"Timeout! Failed to send StatusInfo.")
            failureCount += 1 # 失败次数递增
            if failureCount >= 3: # 失败三次断开连接
                failureCount = 0
                break  # 退出业务发送，准备重连
            continue #超时，直接开始下次状态报文发送
        except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError): # 处理连接关闭异常
            break # 退出循环，停止业务
        except Exception as e:
            myLogger.error(f"Error during business: {e}")
            break  # 发生错误退出循环，停止业务
```

**封装指令执行模块 (controller.execOrder):**

**框架内指令:**

```python
async def inner_order_exec(ws:WebSocketClientProtocol, order_request, restartConfirmEvent:asyncio.Event):
    if order_request["Headers"]["order_type"] == "restart":
        myLogger.info("request Server Restart Confirm.")
        await ws.send(json.dumps({"type":"upload_instruction_result","status":"success","Headers":{"message":"wait Server Confirm"},"data":{}}))
        try:
            await asyncio.wait_for(restartConfirmEvent["event"].wait(),timeout = 20) # 对于重启指令，额外有一个确认步骤
            myLogger.info("Receive Restart Confirm:start to Restart.")
        except Exception:
            myLogger.info("start Restart but failed to receive Server Confirm.")
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    elif order_request["Headers"]["order_type"] == "upload_log":
        device_id = order_request["data"]["device_id"]
        remote_dir = order_request["data"]["remote_dir"]
        try:
            # print(config.host,config.port,config.sftp_host,config.sftp_port,config.sftp_username,config.sftp_password) # 测试用
            if await sftp_upload_log(device_id, config.device_log_local_path, remote_dir,config.sftp_host, config.sftp_port, config.sftp_username, config.sftp_password) is False:
                await ws.send(json.dumps({"type":"upload_instruction_result","status":"fail","Headers":{"message":"fail to upload log."},"data":{}}))
            else:
                await ws.send(json.dumps({"type":"upload_instruction_result","status":"success","Headers":{"message":"successfully upload log."},"data":{}}))
        except Exception:
            pass
```

**框架外自定义指令:**

```python
async def outer_order_exec(ws:WebSocketClientProtocol, order_request):
    if order_request["Headers"]["order_type"] not in config.outer_order_dict:
        await ws.send(json.dumps({"type":"upload_instruction_result","status":"fail","Headers":{"message":"order not in config"},"data":{}}))
    try:
        execFunc = config.outer_order_dict[order_request["Headers"]["order_type"]]
        if "params" not in order_request["data"] or (not isinstance(order_request["data"]["params"],dict)):
            execFunc()
        elif len(order_request["data"]["params"]) == 0:
            execFunc()
        else:
            execFunc(**order_request["data"]["params"])
            myLogger.info("successfully exec order.")
        await ws.send(json.dumps({"type":"upload_instruction_result","status":"success","Headers":{"message":"successfully exec order."},"data":{}}))
    except Exception as e:
        await ws.send(json.dumps({"type":"upload_instruction_result","status":"fail","Headers":{"message":f"Error in exec order: {e}"},"data":{}}))
```

**启动脚本示例:**

```python
import os
from controller.controller_main import startControllerBasicApp
from User import user,password # 这个实际不需要

Host = "112.124.43.208"
Port = 9090
sftp_user = user # 这里替换为实际的云服务器sftp用户名
sftp_password = password # 这里替换为实际的云服务器sftp用户密码

# 自定义指令中执行函数要求使用关键字参数
# 指令：test_order
def test_order_exec(SomethingToPrint="Hello World"):
    print(SomethingToPrint)

startControllerBasicApp(
    host=Host,
    port=Port,
    sftp_host=Host,
    sftp_port=22,
    sftp_username=sftp_user,
    sftp_password=sftp_password,
    device_id=None,
    device_password="testpassword",
    device_hardware_sn="SN123",
    device_hardware_model="ModelB",
    device_log_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..","device2_log"),
    device_log_name="device2.log",
    max_retries=5,
    outer_order_dict={"test_order":test_order_exec} # 暴露给用户的可配置自定义指令字典
)
```

-----

### 4\. 系统开发DevOps实践

  * **版本控制**：选择阿里云CodeUp作为git远程仓库，并使用ssh协议进行通信。
  * **部署主机**：选择免费试用阿里云ECS作为部署主机（公网IP为112.124.43.208）。

**流水线配置:**

**DockerFile编撰:**

```dockerfile
# 使用 Ubuntu 22.04 作为基础镜像
FROM ubuntu:22.04

# 切换到 root 用户
USER root

# 更新包管理器并安装 Python 和相关工具
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 设置默认的 Python 版本为 Python 3
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app
COPY . .
# 指示该服务使用的端口为 9090
EXPOSE 9090
RUN ["python", "-m", "pip", "install", "--upgrade", "pip", "-i", "https://pypi.doubanio.com/simple"]
RUN ["pip3", "install", "-r", "requirements.txt", "-i", "https://pypi.doubanio.com/simple"]

CMD ["python3", "/app/src/Server/api.py"]
```

**流水线触发**: 流水线由CodeUp仓库docker分支代码提交触发，依据代码库中Dockerfile文件，将生成的镜像上传至阿里云容器镜像服务中的镜像仓库，并带上时间标签。

-----