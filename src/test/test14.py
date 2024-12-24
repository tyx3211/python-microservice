import requests
from datetime import datetime

base_url = "http://127.0.0.1:9090"

# 1. 创建设备
def create_device(device_name, hardware_sn, hardware_model):
    url = f"{base_url}/service/devices_manage/device_add"
    payload = {
        "device_name": device_name,  # 设备名称
        "device_type": "Sensor",     # 设备类型
        "hardware_sn": hardware_sn,  # 硬件序列号，确保唯一
        "hardware_model": hardware_model,  # 硬件型号，确保唯一
        "software_version": "1.0.0",  # 软件版本
        "software_last_update": "2024-12-11",  # 软件最后更新日期
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
def modify_device_in_group(device_id, group_id, new_device_id):
    url = f"{base_url}/service/devices_manage/relation_device_modify"
    payload = {
        "device_id": device_id,
        "group_id": group_id,
        "new_device_id": new_device_id
    }
    response = requests.put(url, json=payload)
    return response.json()

# 5. 综合测试
def test_relation_device_modify():
    # Step 1: Create Device 1 (with unique name, SN, and Model)
    device_response_1 = create_device(device_name="Device One", hardware_sn="SN123456789", hardware_model="ModelA")
    device_id_1 = device_response_1['data']['device_id']
    print(f"Created device 1 with ID: {device_id_1}")

    # Step 2: Create Device 2 (with unique name, SN, and Model)
    device_response_2 = create_device(device_name="Device Two", hardware_sn="SN987654321", hardware_model="ModelB")
    device_id_2 = device_response_2['data']['device_id']
    print(f"Created device 2 with ID: {device_id_2}")

    # Ensure that device_id_1 and device_id_2 are different
    assert device_id_1 != device_id_2, "Device IDs should be different!"

    # Step 3: Create Group
    group_response = create_group("Test Group")
    group_id = group_response['data']['group_id']
    print(f"Created group with ID: {group_id}")

    # Step 4: Add device 1 to the group
    relation_response = add_device_to_group(device_id_1, group_id)
    print(f"Added device {device_id_1} to group {group_id}")

    # Step 5: Modify device in the group (replace device 1 with device 2)
    modify_response = modify_device_in_group(device_id_1, group_id, device_id_2)
    print(f"Modification response: {modify_response}")

# Execute the test
test_relation_device_modify()

