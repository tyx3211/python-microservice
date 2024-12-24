import pytest
import requests

# API URL
base_url = "http://127.0.0.1:9090"  # 根据实际 API 地址修改
group_id_query_url = f"{base_url}/service/devices_manage/group_id_query"


# 测试用例：成功查询分组信息
def test_group_id_query_valid():
    group_id = 1  # 假设 group_id 为 1，存在的有效分组 ID
    headers = {
        'Content-Type': 'application/json'  # 确保请求头包含正确的 Content-Type
    }

    response = requests.get(f"{group_id_query_url}/{group_id}", headers=headers)

    print("Test case: Query group with valid group_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：缺少 Content-Type
def test_group_id_query_missing_content_type():
    group_id = 1
    headers = {
        # 没有 Content-Type
    }

    response = requests.get(f"{group_id_query_url}/{group_id}", headers=headers)

    print("Test case: Query group with missing Content-Type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：Content-Type 错误
def test_group_id_query_invalid_content_type():
    group_id = 1
    headers = {
        'Content-Type': 'text/plain'  # 错误的 Content-Type，应该是 application/json
    }

    response = requests.get(f"{group_id_query_url}/{group_id}", headers=headers)

    print("Test case: Query group with invalid Content-Type")
    print("Status Code:", response.status_code)
    
    try:
        # 检查响应体是否为有效的 JSON
        response_json = response.json()
        print("Response JSON:", response_json)
    except ValueError:
        print("Response body is not a valid JSON:", response.text)
    print()


# 测试用例：缺少 group_id
def test_group_id_query_missing_group_id():
    headers = {
        'Content-Type': 'application/json'  # 合法的 Content-Type
    }

    response = requests.get(f"{group_id_query_url}/", headers=headers)

    print("Test case: Query group with missing group_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：无效的 group_id
def test_group_id_query_invalid_group_id():
    group_id = 9999  # 假设 9999 是无效的 group_id
    headers = {
        'Content-Type': 'application/json'  # 合法的 Content-Type
    }

    response = requests.get(f"{group_id_query_url}/{group_id}", headers=headers)

    print("Test case: Query group with invalid group_id")
    print("Status Code:", response.status_code)
    
    try:
        # 检查响应体是否为有效的 JSON
        response_json = response.json()
        print("Response JSON:", response_json)
    except ValueError:
        print("Response body is not a valid JSON:", response.text)
    print()


# 执行测试用例，串行执行
def run_tests():
    # 按顺序依次运行所有测试用例
    test_group_id_query_valid()
    test_group_id_query_missing_content_type()
    test_group_id_query_invalid_content_type()
    test_group_id_query_missing_group_id()
    test_group_id_query_invalid_group_id()


if __name__ == "__main__":
    # 执行所有测试
    run_tests()
