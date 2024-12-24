import requests
from datetime import datetime

base_url = "http://127.0.0.1:9090"

# 1. 创建设备
def create_device():
    url = f"{base_url}/service/devices_manage/device_add"
    payload = {
        "device_name": "Test DeviceYeah",  # 设备名称
        "device_type": "Sensor",       # 设备类型
        "hardware_sn": "SN123456789",  # 硬件序列号
        "hardware_model": "ModelX",    # 硬件型号
        "software_version": "1.0.0",   # 软件版本
        "software_last_update": "2024-12-22",  # 软件最后更新日期
        "password": "testpassword123"  # 设备密码
    }
    response = requests.post(url, json=payload)
    return response.json()

# 2. 创建分组
def create_group(group_name):
    url = f"{base_url}/service/devices_manage/group_add"
    payload = {
        "group_name": group_name  # 创建分组时传递分组名称
    }
    response = requests.post(url, json=payload)
    return response.json()

# 3. 添加设备与分组关系
def add_device_to_group(device_id, group_id):
    url = f"{base_url}/service/devices_manage/relation_add"
    payload = {
        "device_id": device_id,
        "group_id": group_id
    }
    response = requests.post(url, json=payload)
    return response.json()

# 4. 修改设备的分组
def modify_device_group(device_id, group_id, new_group_id):
    url = f"{base_url}/service/devices_manage/relation_group_modify"
    payload = {
        "device_id": device_id,
        "group_id": group_id,
        "new_group_id": new_group_id
    }
    response = requests.put(url, json=payload)
    return response.json()

# 5. 综合测试
def test_relation_group_modify():
    # Step 1: Create Device
    device_response = create_device()
    device_id = device_response['data']['device_id']
    print(f"Created device with ID: {device_id}")

    # Step 2: Create Group 1
    group_response_1 = create_group("group_1")
    group_id_1 = group_response_1['data']['group_id']
    print(f"Created group 1 with ID: {group_id_1}")

    # Step 3: Create Group 2 (for modification)
    group_response_2 = create_group("group_2")
    group_id_2 = group_response_2['data']['group_id']
    print(f"Created group 2 with ID: {group_id_2}")

    # Step 4: Add device to group 1
    relation_response = add_device_to_group(device_id, group_id_1)
    print(f"Added device {device_id} to group {group_id_1}")

    # Step 5: Modify device's group from group_1 to group_2
    modify_response = modify_device_group(device_id, group_id_1, group_id_2)
    print(f"Modification response: {modify_response}")

# Execute the test
test_relation_group_modify()
