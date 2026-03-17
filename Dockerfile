# 使用官方轻量级 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，防止 Python 产生 .pyc 缓存文件，并确保日志实时输出
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安装系统依赖（如果你的算法用到了一些编译库，可以在这添加）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件以利用 Docker 缓存机制
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目代码到容器中
COPY . .

# 暴露比赛要求的 8080 端口
EXPOSE 8080

# 运行你的服务（假设 main.py 是你的启动入口）
# 这里确保绑定到 0.0.0.0，否则外部无法连接
CMD ["python", "main.py"]