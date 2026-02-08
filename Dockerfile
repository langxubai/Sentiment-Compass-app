# 使用官方轻量级 Python 镜像 (基于 Debian)
# 3.10-slim 是目前平衡体积和兼容性的最佳选择
FROM python:3.10-slim

# 设置工作目录，类似于 cd /app
WORKDIR /app

# 1. 先拷贝依赖文件 (利用 Docker Layer 缓存机制)
# 如果 requirements.txt 没变，下次构建会直接跳过安装步骤，速度飞快
COPY requirements.txt .

# 2. 安装 Python 依赖
# --no-cache-dir 可以减少镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 3. [关键步骤] 下载 TextBlob 需要的 NLTK 语料库
# 如果不做这一步，容器运行时分析情绪会报错 "Missing NLTK corpora"
RUN python -m textblob.download_corpora

# 4. 拷贝所有代码到容器中
COPY . .

# 5. 暴露 Streamlit 的默认端口
EXPOSE 8501

# 6. 启动命令
# --server.address=0.0.0.0 是必须的，否则你在宿主机浏览器打不开
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]