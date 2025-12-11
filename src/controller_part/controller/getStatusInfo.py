import psutil
import json
import asyncio
import websockets
import random


def get_cpu_info():
    """
    获取CPU信息
    返回的键及其含义：
    - user_cpu_time: 用户态CPU时间
    - system_cpu_time: 内核态CPU时间
    - idle_cpu_time: 空闲CPU时间
    - io_wait_cpu_time: IO等待CPU时间
    """
    cpu_times = psutil.cpu_times()
    return {
        "user_cpu_time": cpu_times.user,
        "system_cpu_time": cpu_times.system,
        "idle_cpu_time": cpu_times.idle,
        "io_wait_cpu_time": getattr(cpu_times, "iowait", 0),  # 部分平台可能没有 iowait
    }


def get_memory_info():
    """
    获取内存信息
    返回的键及其含义：
    - total_memory_mb: 内存总量（单位：MB）
    - free_memory_mb: 空闲内存（单位：MB）
    - buff_cache_mb: 缓冲/缓存总量（单位：MB）
    """
    memory_info = psutil.virtual_memory()
    return {
        "total_memory_mb": memory_info.total // 1024 // 1024,  # 转换为 MB
        "free_memory_mb": memory_info.free // 1024 // 1024,  # 转换为 MB
        "buff_cache_mb": (memory_info.buffers + memory_info.cached)
        // 1024
        // 1024,  # 转换为 MB
    }


def get_disk_info():
    """
    获取磁盘信息（仅获取根目录信息）
    返回的键及其含义：
    - root_total_size_mb: 根目录总大小（单位：MB）
    - root_used_size_mb: 根目录已使用大小（单位：MB）
    - root_used_percent: 根目录使用百分比
    """
    root_disk = psutil.disk_usage("/")
    return {
        "root_total_size_mb": root_disk.total // 1024 // 1024,  # 转换为 MB
        "root_used_size_mb": root_disk.used // 1024 // 1024,  # 转换为 MB
        "root_used_percent": root_disk.percent,  # 使用百分比
    }


def collect_status_info():
    """
    收集设备所有状态信息
    返回的键及其含义：
    - CPU_info: CPU信息（包含user_cpu_time, system_cpu_time等）
    - Memory_info: 内存信息（包含total_memory_mb, free_memory_mb等）
    - Disk_info: 根目录磁盘信息（仅包含根目录总大小、已使用大小和所占空间比）
    """
    return {
        "CPU_info": get_cpu_info(),
        "Memory_info": get_memory_info(),
        "Disk_info": get_disk_info(),
    }


def easyTest():
    return {"position": random.randint(1, 100)}
