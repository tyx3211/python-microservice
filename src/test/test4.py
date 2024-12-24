import requests
import json

# API URL
base_url = "http://127.0.0.1:9090"  # 根据实际 API 地址修改
device_query_url = f"{base_url}/service/devices_manage/device_basic_SnModel_query"


# 测试用例：成功查询设备
def test_device_basic_query_valid():
    device_sn = "123"  # 假设这是一个有效的设备 SN
    device_model = "ModelX"  # 假设这是一个有效的设备 Model

    headers = {
        'Content-Type': 'application/json'  # 确保请求头包含正确的 Content-Type
    }

    response = requests.get(f"{device_query_url}/{device_sn}/{device_model}", headers=headers)

    print("Test case: Query device with valid device_sn and device_model")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()  # 空行，方便区分不同测试用例


# 测试用例：设备 SN 和 Model 不存在
def test_device_basic_query_not_found():
    device_sn = "non_existent_sn"  # 假设这是一个不存在的设备 SN
    device_model = "NonModel"  # 假设这是一个不存在的设备 Model

    headers = {
        'Content-Type': 'application/json'  # 确保请求头包含正确的 Content-Type
    }

    response = requests.get(f"{device_query_url}/{device_sn}/{device_model}", headers=headers)

    print("Test case: Query device with non-existent device_sn and device_model")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：设备 SN 或 Model 为空
def test_device_basic_query_empty_device_id_or_model():
    device_sn = "SN12345"
    device_model = ""  # 空设备Model

    headers = {
        'Content-Type': 'application/json'  # 确保请求头包含正确的 Content-Type
    }

    response = requests.get(f"{device_query_url}/{device_sn}/{device_model}", headers=headers)

    print("Test case: Query device with empty device_sn")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：Content-Type 错误
def test_device_basic_query_invalid_content_type():
    device_sn = "valid_sn_123"  # 假设这是一个有效的设备 SN
    device_model = "ModelX"  # 假设这是一个有效的设备 Model

    headers = {
        'Content-Type': 'text/plain'  # 错误的 Content-Type，应该是 application/json
    }

    response = requests.get(f"{device_query_url}/{device_sn}/{device_model}", headers=headers)

    print("Test case: Query device with invalid Content-Type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 执行所有测试用例
def run_tests():
    test_device_basic_query_valid()
    test_device_basic_query_not_found()
    test_device_basic_query_empty_device_id_or_model()
    test_device_basic_query_invalid_content_type()

if __name__ == "__main__":
    run_tests()
