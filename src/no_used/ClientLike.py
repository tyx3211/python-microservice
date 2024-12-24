import threading
import requests

def test(i):

    for i in range(100):
        # isQuery = input("Query?\n")
        # sql = input("请输入SQL\n")
        isQuery = 0

        url = ["http://127.0.0.1:9090/URD","http://127.0.0.1:9090/query"]
        data = {"sql":f"UPDATE test SET num = {100*i} WHERE id = 1;"}  # POST 请求体数据
        headers = {"Content-Type": "application/json"}  # 请求头

        # 发送 POST 请求
        response = requests.post(url[int(isQuery)], json=data, headers=headers)

        # 打印响应内容
        print(response.status_code)  # HTTP 状态码
        print(response.json())       # JSON 响应数据

for i in range(10):
    thread = [None] * 10
    thread[i] = threading.Thread(target=test,args=(i,))
    thread[i].start()
    