import requests
import json

# API URL
base_url = "http://127.0.0.1:9090/service/devices_manage"
device_add_url = f"{base_url}/device_add"
group_add_url = f"{base_url}/group_add"
relation_add_url = f"{base_url}/relation_add"
relation_del_url = f"{base_url}/relation_del"

# 请求头
headers = {
    'Content-Type': 'application/json'
}

# 1. 创建设备
def create_device(device_name, device_type, hardware_sn, hardware_model, software_version, software_last_update, password):
    payload = {
        "device_name": device_name,
        "device_type": device_type,
        "hardware_sn": hardware_sn,
        "hardware_model": hardware_model,
        "software_version": software_version,
        "software_last_update": software_last_update,
        "password": password
    }
    response = requests.post(device_add_url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['device_id']
    else:
        raise Exception(f"Failed to create device: {response.text}")

# 2. 创建分组
def create_group(group_name, group_description):
    payload = {
        "group_name": group_name,
        "group_description": group_description
    }
    response = requests.post(group_add_url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['group_id']
    else:
        raise Exception(f"Failed to create group: {response.text}")

# 3. 创建设备-分组关系
def create_relation(device_id, group_id):
    payload = {
        "device_id": device_id,
        "group_id": group_id
    }
    response = requests.post(relation_add_url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to create relation: {response.text}")

# 4. 删除设备-分组关系
def delete_relation(device_id, group_id):
    payload = {
        "device_id": device_id,
        "group_id": group_id
    }
    response = requests.delete(relation_del_url, json=payload, headers=headers)
    return response

# 5. 初始化：添加两个设备和两个分组
def initialize_data():
    # 创建设备
    device1_id = create_device("Test Device 1", "Smartphone3", "12345", "ModelX", "1.0.0", "2024-12-01", "testpassword")
    device2_id = create_device("Test Device 2", "Smartphone2", "67890", "ModelY", "1.0.1", "2024-12-02", "testpassword")

    # 创建分组
    group1_id = create_group("Test Group 1", "Group for test purposes")
    group2_id = create_group("Test Group 2", "Another group for test purposes")

    # 创建设备-分组关系
    create_relation(device1_id, group1_id)
    create_relation(device2_id, group2_id)

    return device1_id, device2_id, group1_id, group2_id

# 6. 测试用例：成功删除设备-分组关系
def test_valid_relation_delete(device1_id, device2_id, group1_id, group2_id):
    # 删除设备1和分组1的关系
    response = delete_relation(device1_id, group1_id)
    print("Test case: Valid request (delete relation)")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 7. 测试用例：缺少 device_id 字段
def test_missing_device_id(device1_id, device2_id, group1_id, group2_id):
    payload = {
        "group_id": group2_id
    }
    response = requests.delete(relation_del_url, json=payload, headers=headers)
    print("Test case: Missing device_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 8. 测试用例：缺少 group_id 字段
def test_missing_group_id(device1_id, device2_id, group1_id, group2_id):
    payload = {
        "device_id": device2_id
    }
    response = requests.delete(relation_del_url, json=payload, headers=headers)
    print("Test case: Missing group_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 9. 测试用例：无效的设备-分组关系（设备或分组不存在）
def test_invalid_relation():
    device_id = "invalid_device_id"
    group_id = 9999  # 假设这个分组ID不存在

    payload = {
        "device_id": device_id,
        "group_id": group_id
    }
    response = requests.delete(relation_del_url, json=payload, headers=headers)
    print("Test case: Invalid relation (device or group does not exist)")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 10. 测试用例：Content-Type 错误（非 application/json）
def test_invalid_content_type(device1_id, device2_id, group1_id, group2_id):
    payload = {
        "device_id": device2_id,
        "group_id": group2_id
    }
    response = requests.delete(relation_del_url, json=payload, headers={"Content-Type": "text/plain"})
    print("Test case: Invalid Content-Type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 执行所有测试用例
def run_tests():
    # 初始化数据：创建设备和分组
    device1_id, device2_id, group1_id, group2_id = initialize_data()

    # 执行所有测试用例
    # 测试合法删除：device_1 和 group_1
    test_valid_relation_delete(device1_id, device2_id, group1_id, group2_id)

    # 后续测试使用 device_2 和 group_2
    test_missing_device_id(device1_id, device2_id, group1_id, group2_id)  # 测试缺少 device_id
    test_missing_group_id(device1_id, device2_id, group1_id, group2_id)  # 测试缺少 group_id
    test_invalid_relation()  # 测试无效的设备或分组
    test_invalid_content_type(device1_id, device2_id, group1_id, group2_id)  # 测试 Content-Type 错误

if __name__ == "__main__":
    run_tests()
