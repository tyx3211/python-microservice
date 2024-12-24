import requests
import json

# API URL
base_url = "http://127.0.0.1:9090"  # 根据实际 API 地址修改
relation_add_url = f"{base_url}/service/devices_manage/relation_add"

# 设备 ID 和 分组 ID 常量定义
exist_device_id = "7276171445909065728"  # 已存在的设备ID
exist_group_ids = [1, 2, 3]  # 已存在的分组ID

# 测试用例：成功新增设备-分组关系
def test_relation_add_valid():
    relation_data = {
        "device_id": exist_device_id,  # 已存在的设备ID
        "group_id": exist_group_ids[0]  # 已存在的分组ID
    }

    headers = {
        'Content-Type': 'application/json'  # 确保请求头包含正确的 Content-Type
    }

    response = requests.post(relation_add_url, json=relation_data, headers=headers)

    print("Test case: Add valid device-group relation")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：缺少 device_id
def test_relation_add_missing_device_id():
    relation_data = {
        "group_id": exist_group_ids[0]  # 只提供group_id，没有device_id
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(relation_add_url, json=relation_data, headers=headers)

    print("Test case: Add relation missing device_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：缺少 group_id
def test_relation_add_missing_group_id():
    relation_data = {
        "device_id": exist_device_id  # 只提供device_id，没有group_id
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(relation_add_url, json=relation_data, headers=headers)

    print("Test case: Add relation missing group_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：设备与分组的关系已存在
def test_relation_add_already_exists():
    # 假设设备ID为"7276171445909065728"和分组ID为1的关系已经存在
    relation_data = {
        "device_id": exist_device_id,  # 已存在的设备ID
        "group_id": exist_group_ids[0]  # 已存在的分组ID
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(relation_add_url, json=relation_data, headers=headers)

    print("Test case: Add relation that already exists")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：无效的 device_id 或 group_id
def test_relation_add_invalid_device_id_or_group_id():
    # 假设 device_id 为 "invalid_device" 和 group_id 为 "9999" 不存在
    relation_data = {
        "device_id": "invalid_device",  # 无效的设备ID
        "group_id": 9999  # 无效的分组ID
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(relation_add_url, json=relation_data, headers=headers)

    print("Test case: Add relation with invalid device_id or group_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：Content-Type 错误
def test_relation_add_invalid_content_type():
    relation_data = {
        "device_id": exist_device_id,  # 已存在的设备ID
        "group_id": exist_group_ids[0]  # 已存在的分组ID
    }

    headers = {
        'Content-Type': 'text/plain'  # 错误的 Content-Type，应该是 application/json
    }

    response = requests.post(relation_add_url, json=relation_data, headers=headers)

    print("Test case: Add relation with invalid Content-Type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：请求体为空
def test_relation_add_empty_body():
    relation_data = {}

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(relation_add_url, json=relation_data, headers=headers)

    print("Test case: Add relation with empty body")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 执行所有测试用例
def run_tests():
    test_relation_add_valid()
    test_relation_add_missing_device_id()
    test_relation_add_missing_group_id()
    test_relation_add_already_exists()
    test_relation_add_invalid_device_id_or_group_id()
    test_relation_add_invalid_content_type()
    test_relation_add_empty_body()


if __name__ == "__main__":
    run_tests()