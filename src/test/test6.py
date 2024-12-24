import requests

base_url = "http://127.0.0.1:9090"  # 根据实际 API 地址修改
group_modify_url = f"{base_url}/service/devices_manage/group_modify"

# 测试用例：成功修改分组信息
def test_group_modify_valid():
    data = {
        "group_id": 1,
        "group_description": "Updated group description"
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.put(group_modify_url, json=data, headers=headers)
    print("Test case: Modify group with valid data")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：缺少 group_id
def test_group_modify_missing_group_id():
    data = {
        "group_name": "Updated Group Name",
        "group_description": "Updated group description"
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.put(group_modify_url, json=data, headers=headers)
    print("Test case: Modify group with missing group_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：字段无效（例如 group_id 不存在）
def test_group_modify_invalid_group_id():
    data = {
        "group_id": 9999,  # 假设 9999 是无效的 group_id
        "group_name": "Updated Group Name",
        "group_description": "Updated group description"
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.put(group_modify_url, json=data, headers=headers)
    print("Test case: Modify group with invalid group_id")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：Content-Type 错误
def test_group_modify_invalid_content_type():
    data = {
        "group_id": 1,
        "group_name": "Updated Group Name",
        "group_description": "Updated group description"
    }

    headers = {
        'Content-Type': 'text/plain'  # 错误的 Content-Type
    }

    response = requests.put(group_modify_url, json=data, headers=headers)
    print("Test case: Modify group with invalid Content-Type")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


# 测试用例：部分字段无效（缺少 group_name）
def test_group_modify_missing_required_fields():
    data = {
        "group_id": 1,
        "group_description": "Updated group description"
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.put(group_modify_url, json=data, headers=headers)
    print("Test case: Modify group with missing required fields")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    print()


if __name__ == "__main__":
    test_group_modify_valid()
    test_group_modify_missing_group_id()
    test_group_modify_invalid_group_id()
    test_group_modify_invalid_content_type()
    test_group_modify_missing_required_fields()

