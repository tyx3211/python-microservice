import requests

# 1. 创建分组
def create_group():
    url = "http://127.0.0.1:9090/service/devices_manage/group_add"
    group_data = {
        "group_name": "TestGroup_1",  # 确保group_name唯一
        "group_description": "This is Test Group 1"
    }
    response = requests.post(url, json=group_data)
    print("Group Creation Response:", response.json())
    return response.json()

# 2. 创建设备
def create_device(device_data):
    url = "http://127.0.0.1:9090/service/devices_manage/device_add"
    response = requests.post(url, json=device_data)
    print(f"Device Creation Response for {device_data['device_name']}:", response.json())
    return response.json()

# 3. 关联设备和分组
def create_relation(device_id, group_id):
    url = "http://127.0.0.1:9090/service/devices_manage/relation_add"
    relation_data = {
        "device_id": device_id,
        "group_id": group_id
    }
    response = requests.post(url, json=relation_data)
    print(f"Relation Creation for device {device_id} and group {group_id}:", response.json())
    return response.json()

# 4. 修改分组下所有设备的信息
def modify_group_devices(group_id):
    url = "http://127.0.0.1:9090/service/devices_manage/group_all_devices_modify"
    modify_data = {
        "group_id": group_id,
        "dev_description": "Updated description for all devices in the group",
        "password": "newpassword123"  # 注意密码字段会被加盐处理
    }
    modify_response = requests.put(url, json=modify_data)
    print("Group All Devices Modify Response:", modify_response.json())
    return modify_response.json()

# 5. 查询设备信息
def query_device(device_id):
    url = f"http://127.0.0.1:9090/service/devices_manage/device_basic_id_query/{device_id}"
    response = requests.get(url, headers={"Content-Type": "application/json"})
    print(f"Device {device_id} Information:", response.json())
    return response.json()

# 主流程执行
def main():
    # 1. 创建分组
    group_response = create_group()
    group_id = group_response['data']['group_id']  # 获取创建的group_id

    # 2. 创建多个设备
    device_data_1 = {
        "device_name": "Device_1",
        "device_type": "Type_A",
        "hardware_sn": "SN_001",
        "hardware_model": "Model_001",
        "software_version": "1.0.0",
        "software_last_update": "2024-01-01",
        "dev_description": "Test1",
        "password": "password123"
    }
    device_data_2 = {
        "device_name": "Device_2",
        "device_type": "Type_B",
        "hardware_sn": "SN_002",
        "hardware_model": "Model_002",
        "software_version": "1.1.0",
        "software_last_update": "2024-01-01",
        "dev_description": "Test2",
        "password": "password456"
    }

    device_response_1 = create_device(device_data_1)
    device_response_2 = create_device(device_data_2)

    # 3. 设备和分组关联
    create_relation(device_response_1['data']['device_id'], group_id)
    create_relation(device_response_2['data']['device_id'], group_id)

    # 4. 修改分组下所有设备信息
    modify_group_devices(group_id)

    # 5. 查询设备信息
    query_device(device_response_1['data']['device_id'])
    query_device(device_response_2['data']['device_id'])

# 执行主流程
if __name__ == "__main__":
    main()
