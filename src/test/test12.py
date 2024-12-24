import requests
import json

# API URL
group_name_query_url = "http://127.0.0.1:9090/service/devices_manage/group_name_query"

# 模拟添加分组的辅助函数
def add_group(group_name, group_description):
    payload = {
        "group_name": group_name,
        "group_description": group_description,
        "created_time": 1672531199,
        "updated_time": 1672531199
    }
    response = requests.post("http://127.0.0.1:9090/service/devices_manage/group_add", json=payload, headers={'Content-Type': 'application/json'})
    group_data = response.json()
    print(f"Group '{group_name}' add response:", group_data)
    return group_data["data"]

# 测试用例：合法查询分组
def test_valid_group_name_query():
    # 先添加一个具有高难度名称的分组
    group_data = add_group("Quasi-Imperial Coalition", "A confederation formed to bridge the divides between the material and immaterial realms.")

    # 根据分组名查询
    response = requests.get(f"{group_name_query_url}/Quasi-Imperial Coalition", headers={'Content-Type': 'application/json'})
    
    print("Test case: Valid group name query")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 测试用例：Content-Type 错误
def test_invalid_group_name_query_wrong_content_type():
    # 尝试使用错误的 Content-Type
    response = requests.get(f"{group_name_query_url}/Quasi-Imperial Coalition", headers={'Content-Type': 'text/plain'})
    
    print("Test case: Invalid group name query (wrong Content-Type)")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 测试用例：查询不存在的分组
def test_invalid_group_name_query_group_not_found():
    # 查询一个不存在的分组
    response = requests.get(f"{group_name_query_url}/Nonexistent Group", headers={'Content-Type': 'application/json'})
    
    print("Test case: Invalid group name query (group not found)")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

# 执行所有测试用例
def run_tests():
    test_valid_group_name_query()
    test_invalid_group_name_query_wrong_content_type()
    test_invalid_group_name_query_group_not_found()

if __name__ == "__main__":
    run_tests()
