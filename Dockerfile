# 使用 Ubuntu 22.04 作为基础镜像
FROM ubuntu:22.04

# 切换到 root 用户
USER root

# 更新包管理器并安装 Python 和相关工具
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 设置默认的 Python 版本为 Python 3
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app
COPY . .
# 指示该服务使用的端口为 8000
EXPOSE 9090
RUN ["python","-m","pip","install","--upgrade","pip","-i","https://pypi.doubanio.com/simple"]
RUN ["pip3","install","-r","requirement.txt","-i","https://pypi.doubanio.com/simple"]

CMD ["python3","/app/src/Server/api.py"] 
