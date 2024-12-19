import requests
import json

# API URL
url = "http://127.0.0.1:9090/service/devices_manage/device_add"  # 根据实际 API 地址修改

# 测试用例：正常请求
def test_valid_request():
    payload = {
        "device_name": "Test Device",
        "device_type": "Smartphone",
        "hardware_sn": "123",
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
    
    response = requests.post(url, json=payload, headers=headers)
    
    print("Test case: Valid request")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 测试用例：Content-Type 错误
def test_invalid_content_type():
    payload = {
        "device_name": "Test Device",
        "device_type": "Smartphone",
        "hardware_sn": "123456",
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
        'Content-Type': 'text/plain'  # 错误的 Content-Type
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    print("Test case: Invalid Content-Type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 测试用例：缺少必需的字段
def test_missing_required_param():
    payload = {
        "device_name": "Test Device",
        "device_type": "Smartphone",
        "hardware_sn": "12345",
        "hardware_model": "ModelX",
        # "password" 字段缺失
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    print("Test case: Missing required parameter")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 测试用例：字段类型错误
def test_invalid_field_type():
    payload = {
        "device_name": "Test Device",
        "device_type": "Smartphone",
        "hardware_sn": "1234",
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
    
    response = requests.post(url, json=payload, headers=headers)
    
    print("Test case: Invalid field type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 测试用例：空的请求体
def test_empty_request_body():
    payload = {}

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)

    print("Test case: Empty request body")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 执行所有测试用例
def run_tests():
    test_valid_request()
    test_invalid_content_type()
    test_missing_required_param()
    test_invalid_field_type()
    test_empty_request_body()

if __name__ == "__main__":
    run_tests()
