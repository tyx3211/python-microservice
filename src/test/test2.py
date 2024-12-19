import requests
import json

# API URL
device_add_url = "http://127.0.0.1:9090/service/devices_manage/device_add"  # 设备添加接口的 URL
device_modify_url = "http://127.0.0.1:9090/service/devices_manage/device_basic_modify"  # 设备修改接口的 URL

# 1. 设备添加的辅助函数
def add_device():
    payload = {
        "device_name": "Test Device",
        "device_type": "Smartphone",
        "hardware_sn": "SN12345",
        "hardware_model": "ModelX",
        "software_version": "1.0.0",
        "software_last_update": "2024-12-01",
        "nic1_type": "Ethernet",
        "nic1_mac": "00:1A:2B:3C:4D:5E",
        "nic1_ipv4": "192.168.1.1",
        "nic2_type": "WiFi",
        "nic2_mac": "00:1A:2B:3C:4D:5F",
        "nic2_ipv4": "192.168.1.2",
        "dev_description": "A sample device for testing.",
        "password": "testpassword123"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 发送设备添加请求
    response = requests.post(device_add_url, json=payload, headers=headers)
    
    # 打印响应并返回生成的 device_id 供后续测试使用
    print("Device Add Response:")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    
    # 从响应中提取 device_id
    if response.status_code == 200:
        return response.json()["data"]["device_id"]
    else:
        return None

# 2. 测试用例：正常请求
def test_valid_request(device_id):
    payload = {
        "device_id": device_id,
        "device_name": "Device A",
        "device_type": "Smartphone",
        "hardware_sn": "SN12345",
        "hardware_model": "ModelX",
        "software_version": "1.0.0",
        "software_last_update": "2024-12-01",
        "nic1_type": "Ethernet",
        "nic1_mac": "00:1A:2B:3C:4D:5E",
        "nic1_ipv4": "192.168.1.1",
        "nic2_type": "WiFi",
        "nic2_mac": "00:1A:2B:3C:4D:5F",
        "nic2_ipv4": "192.168.1.2",
        "dev_description": "A sample device for testing.",
        "password": "newpassword123"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.put(device_modify_url, json=payload, headers=headers)
    
    print("Test case: Valid request")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 3. 测试用例：Content-Type 错误
def test_invalid_content_type(device_id):
    payload = {
        "device_id": device_id,
        "device_name": "Device A",
        "device_type": "Smartphone",
        "hardware_sn": "SN12345",
        "hardware_model": "ModelX",
        "software_version": "1.0.0",
        "software_last_update": "2024-12-01",
        "nic1_type": "Ethernet",
        "nic1_mac": "00:1A:2B:3C:4D:5E",
        "nic1_ipv4": "192.168.1.1",
        "nic2_type": "WiFi",
        "nic2_mac": "00:1A:2B:3C:4D:5F",
        "nic2_ipv4": "192.168.1.2",
        "dev_description": "A sample device for testing.",
        "password": "newpassword123"
    }
    
    headers = {
        'Content-Type': 'text/plain'  # 错误的 Content-Type
    }
    
    response = requests.put(device_modify_url, json=payload, headers=headers)
    
    print("Test case: Invalid Content-Type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 4. 测试用例：缺少必需的字段
def test_missing_required_param(device_id):
    payload = {
        "device_name": "Device A",
        "device_type": "Smartphone",
        "hardware_sn": "SN12345",
        "hardware_model": "ModelX",
        "software_version": "1.0.0",
        "software_last_update": "2024-12-01",
        # "device_id" 字段缺失
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.put(device_modify_url, json=payload, headers=headers)
    
    print("Test case: Missing required parameter")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 5. 测试用例：字段类型错误
def test_invalid_field_type(device_id):
    payload = {
        "device_id": device_id,
        "device_name": "Device A",
        "device_type": "Smartphone",
        "hardware_sn": "SN12345",
        "hardware_model": "ModelX",
        "software_version": "1.0.0",
        "software_last_update": "2024-12-01",
        "nic1_type": "Ethernet",
        "nic1_mac": "00:1A:2B:3C:4D:5E",
        "nic1_ipv4": "192.168.1.1",
        "nic2_type": "WiFi",
        "nic2_mac": "00:1A:2B:3C:4D:5F",
        "nic2_ipv4": "192.168.1.2",
        "dev_description": "A sample device for testing.",
        "password": 123456  # 错误的类型，应该是字符串
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.put(device_modify_url, json=payload, headers=headers)
    
    print("Test case: Invalid field type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 6. 测试用例：空的请求体
def test_empty_request_body(device_id):
    payload = {}

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.put(device_modify_url, json=payload, headers=headers)

    print("Test case: Empty request body")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 7. 测试用例：密码修改测试
def test_password_change(device_id):
    payload = {
        "device_id": device_id,
        "password": "new_secure_password"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.put(device_modify_url, json=payload, headers=headers)

    print("Test case: Password change")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 执行所有测试用例
def run_tests():
    # 先添加设备
    device_id = add_device()
    if device_id:
        # 设备添加成功，执行修改设备的相关测试
        test_valid_request(device_id)
        test_invalid_content_type(device_id)
        test_missing_required_param(device_id)
        test_invalid_field_type(device_id)
        test_empty_request_body(device_id)
        test_password_change(device_id)
    else:
        print("Failed to add device. Skipping tests.")

if __name__ == "__main__":
    run_tests()
