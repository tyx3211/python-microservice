import requests
import json

# API URL
device_add_url = "http://127.0.0.1:9090/service/devices_manage/device_add"
group_add_url = "http://127.0.0.1:9090/service/devices_manage/group_add"
relation_add_url = "http://127.0.0.1:9090/service/devices_manage/relation_add"
device_delete_url = "http://127.0.0.1:9090/service/devices_manage/device_delete"

device_2 = None

# 测试用例：合法删除设备
def test_valid_device_delete():
    # 添加设备和分组前置步骤
    global device_2
    device_1 = add_device("Device 1", "Type 1", "SN1234", "ModelX", "password1")
    device_2 = add_device("Device 2", "Type 2", "SN5678", "ModelY", "password2")
    group_1 = add_group("Group 1", "Test group 1")
    group_2 = add_group("Group 2", "Test group 2")
    
    # 设备 1 和 分组 1、2 关联
    add_relation(device_1["device_id"], group_1["group_id"])
    add_relation(device_1["device_id"], group_2["group_id"])
    
    # 删除设备 1
    payload = {"device_id": device_1["device_id"]}
    response = requests.delete(device_delete_url, json=payload, headers={'Content-Type': 'application/json'})
    
    print("Test case: Valid device delete")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 测试用例：设备不存在，删除失败
def test_invalid_device_delete_device_not_found():
    payload = {"device_id": "9999999999"}  # 一个不存在的设备ID
    response = requests.delete(device_delete_url, json=payload, headers={'Content-Type': 'application/json'})
    
    print("Test case: Invalid device delete (device not found)")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 测试用例：Content-Type 错误
def test_invalid_device_delete_wrong_content_type():
    global device_2
    payload = {"device_id": device_2["device_id"]}  # 假设设备2的ID
    response = requests.delete(device_delete_url, json=payload, headers={'Content-Type': 'text/plain'})
    
    print("Test case: Invalid device delete (wrong Content-Type)")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 模拟添加设备的辅助函数
def add_device(device_name, device_type, hardware_sn, hardware_model, password):
    payload = {
        "device_name": device_name,
        "device_type": device_type,
        "hardware_sn": hardware_sn,
        "hardware_model": hardware_model,
        "software_version": "1.0.0",
        "software_last_update": "2024-12-01",
        "nic1_type": "Ethernet",
        "nic1_mac": "00:1A:2B:3C:4D:5E",
        "nic1_ipv4": "192.168.1.1",
        "nic2_type": "WiFi",
        "nic2_mac": "00:1A:2B:3C:4D:5F",
        "nic2_ipv4": "192.168.1.2",
        "dev_description": device_name + " for testing",
        "password": password
    }
    response = requests.post(device_add_url, json=payload, headers={'Content-Type': 'application/json'})
    device_data = response.json()
    print(f"Device '{device_name}' add response:", device_data)
    return device_data["data"]

# 模拟添加分组的辅助函数
def add_group(group_name, group_description):
    payload = {
        "group_name": group_name,
        "group_description": group_description,
        "created_time": 1672531199,
        "updated_time": 1672531199
    }
    response = requests.post(group_add_url, json=payload, headers={'Content-Type': 'application/json'})
    group_data = response.json()
    print(f"Group '{group_name}' add response:", group_data)
    return group_data["data"]

# 模拟添加设备-分组关系的辅助函数
def add_relation(device_id, group_id):
    payload = {
        "device_id": device_id,
        "group_id": group_id
    }
    response = requests.post(relation_add_url, json=payload, headers={'Content-Type': 'application/json'})
    print(f"Relation between device {device_id} and group {group_id} add response:", response.json())

# 执行所有测试用例
def run_tests():
    test_valid_device_delete()
    test_invalid_device_delete_device_not_found()
    test_invalid_device_delete_wrong_content_type()

if __name__ == "__main__":
    run_tests()
