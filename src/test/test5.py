import requests
import json

# API URL
base_url = "http://127.0.0.1:9090"  # 根据实际 API 地址修改
group_add_url = f"{base_url}/service/devices_manage/group_add"


# 测试用例：成功创建分组
def test_group_add_valid():
    group_data = {
        "group_name": "group_test_1",
        "group_description": "This is a test group",
        "created_time": 1234567890,
        "updated_time": 1234567890
    }

    headers = {
        'Content-Type': 'application/json'  # 确保请求头包含正确的 Content-Type
    }

    response = requests.post(group_add_url, json=group_data, headers=headers)

    print("Test case: Create group with valid data")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：创建分组时缺少 group_name
def test_group_add_missing_name():
    group_data = {
        "group_description": "This group is missing a name",
        "created_time": 1234567890,
        "updated_time": 1234567890
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(group_add_url, json=group_data, headers=headers)

    print("Test case: Create group missing group_name")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：创建分组时提供重复的 group_name
def test_group_add_duplicate_name():
    # 先创建一个分组
    group_data = {
        "group_name": "group_test_2",
        "group_description": "This is a test group",
        "created_time": 1234567890,
        "updated_time": 1234567890
    }

    headers = {
        'Content-Type': 'application/json'
    }

    # 创建第一个分组
    requests.post(group_add_url, json=group_data, headers=headers)

    # 再创建一个重复的 group_name
    group_data_duplicate = {
        "group_name": "group_test_2",  # 和上面创建的 group_name 一致
        "group_description": "This is a duplicate group",
        "created_time": 1234567891,
        "updated_time": 1234567891
    }

    response = requests.post(group_add_url, json=group_data_duplicate, headers=headers)

    print("Test case: Create group with duplicate group_name")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：创建分组时缺少 created_time 和 updated_time
def test_group_add_missing_time():
    group_data = {
        "group_name": "group_test_3",
        "group_description": "Missing time fields"
        # 没有提供 created_time 和 updated_time
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(group_add_url, json=group_data, headers=headers)

    print("Test case: Create group missing created_time and updated_time")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：创建分组时内容为空
def test_group_add_empty_data():
    group_data = {}

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(group_add_url, json=group_data, headers=headers)

    print("Test case: Create group with empty data")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：Content-Type 错误
def test_group_add_invalid_content_type():
    group_data = {
        "group_name": "group_test_4",
        "group_description": "This group has invalid Content-Type",
        "created_time": 1234567892,
        "updated_time": 1234567892
    }

    headers = {
        'Content-Type': 'text/plain'  # 错误的 Content-Type，应该是 application/json
    }

    response = requests.post(group_add_url, json=group_data, headers=headers)

    print("Test case: Create group with invalid Content-Type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 执行所有测试用例
def run_tests():
    test_group_add_valid()
    test_group_add_missing_name()
    test_group_add_duplicate_name()
    test_group_add_missing_time()
    test_group_add_empty_data()
    test_group_add_invalid_content_type()


if __name__ == "__main__":
    run_tests()
