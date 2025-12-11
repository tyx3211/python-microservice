# 云边端设备管理微服务系统 (Cloud-Edge Device Management Microservice)

基于 Python Sanic 和 Asyncio 构建的高性能云边端设备管理系统，支持云端微服务管理与边端设备控制。包含设备全生命周期管理、实时状态监控、远程指令下发以及自动化 CI/CD 部署。

## 🌟 项目亮点

*   **异步高性能架构设计**: 基于 **Sanic + Asyncio** 构建高并发微服务，利用 **Python 协程** 与 **单线程非阻塞 I/O** 模型，解决了传统同步框架在 I/O 密集型场景下的性能瓶颈，实现了单节点对海量边端设备长连接的高效处理。
*   **自研云边协同通信协议**: 设计并实现基于 **WebSockets** 的南向通信协议（JSON PDU），不仅支持由云端主动发起的 **RPC 风格指令下发**（如重启、日志拉取），还内建了应用层 **心跳保活**、**指数退避重连** 及 **状态差异同步** 机制，确保了弱网环境下的链路稳定性。
*   **全流程 DevOps 落地**: 编写 **Dockerfile** 实现服务的容器化封装，并基于阿里云 CodeUp 搭建 **CI/CD 流水线**。实现了代码提交自动触发镜像构建、打标（Time-Tag）及推送到阿里云容器镜像服务（ACR）的全自动化交付流程。
*   **健壮的后端工程实践**: 集成 **Snowflake** 算法生成全局唯一设备 ID，使用 **bcrypt** 加盐哈希保障存储安全；封装统一的 **异常处理装饰器** 与 **JSON 响应规范**，显著提升了系统的可维护性与鲁棒性。

## 📂 项目目录结构

```text
.
├── Dockerfile                  # Docker 容器构建文件
├── README.md                   # 项目文档
├── requirements.txt            # 项目依赖列表
├── docs/                       # 项目文档与报告
│   └── report.md               # 详细设计报告
└── src/                        # 源代码目录
    ├── Server/                 # 云端微服务模块
    │   ├── api.py              # 服务入口，定义北向 REST API 与南向 WebSocket 路由
    │   ├── south_api_core.py   # 南向接口核心逻辑（心跳管理、指令路由、状态同步）
    │   ├── Database_OP.py      # 异步数据库操作封装（基于 aiomysql）
    │   ├── database_ini.json   # 数据库连接配置
    │   ├── pre_SQL.sql         # 数据库初始化 SQL 脚本
    │   └── start.sh            # 服务启动脚本
    └── controller_part/        # 边端控制器模块
        ├── User.py             # 用户配置示例
        └── controller/         # 边端核心包
            ├── controller_main.py # 边端入口，负责连接管理、事件分发与主协程调度
            ├── execorder.py       # 指令执行模块（本地指令与自定义指令）
            ├── getStatusInfo.py   # 系统状态采集模块（CPU/内存/磁盘）
            ├── logger.py          # 本地日志轮转记录配置
            ├── sftp_upload.py     # SFTP 日志异步上传模块
            └── config.py          # 边端全局配置管理
```

## 🏗️ 架构概览

### 技术栈

*   **Core**: Python 3.9+, Asyncio
*   **Web Framework**: Sanic (High performance async framework)
*   **Communication**: WebSockets (Southbound), HTTP/REST (Northbound)
*   **Database**: MySQL (Storage), aiomysql (Async Driver)
*   **Security**: bcrypt (Salted Hashing)
*   **DevOps**: Docker, Aliyun CodeUp (CI/CD)

### 核心模块

*   **Server (Cloud)**:
    *   **Northbound API**: RESTful 接口，供上层业务系统调用（设备增删改查、分组管理、指令下发）。
    *   **Southbound API**: WebSocket 服务，处理边缘设备接入、鉴权、心跳维护及数据上报。
*   **Controller (Edge)**:
    *   **Connection Mgr**: 负责与云端建立长连接，维护心跳，处理断线重连 (Exponential Backoff)。
    *   **Order Exec**: 接收并执行云端下发的指令（如重启、日志上传、自定义脚本）。
    *   **Status Reporter**: 周期性采集本地系统信息（CPU/Mem/Disk）并上报云端。

## 🚀 快速开始

### 1. 环境准备

*   Python 3.8+
*   MySQL 8.0+

### 2. 数据库设置

创建数据库并初始化表结构：

```sql
CREATE DATABASE devices_management;
USE devices_management;
-- 运行 src/Server/pre_SQL.sql 中的 SQL 语句
```

### 3. 启动云端服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python src/Server/api.py
```
服务默认运行在 `0.0.0.0:9090`。

### 4. 启动边端模拟器

```bash
# 修改测试脚本中的配置信息
vim src/controller_part/controller/test_start_1.py

# 运行模拟设备
python src/controller_part/controller/test_start_1.py
```

## 📜 接口文档

### 北向接口 (Northbound API)

*   `POST /service/devices_manage/device_add`: 注册新设备
*   `GET /service/devices_manage/device_statusInfo_query/<device_id>`: 查询设备实时状态
*   `POST /service/devices_manage/give_order`: 向设备下发指令

### 南向接口 (Southbound API)

*   `ws://<host>:9090/ws`: WebSocket 连接端点
    *   **Auth**: 登录鉴权
    *   **Ping/Pong**: 心跳保活
    *   **Upload**: 状态上报

更多信息可以查看[项目报告文档](./docs/report.md)

## 📦 部署 (Docker)

```bash
docker build -t device-server:latest .
docker run -d -p 9090:9090 device-server:latest
```

## 📄 License

MIT License
