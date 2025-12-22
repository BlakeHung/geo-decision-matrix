# 使用基於 Debian Bookworm 的穩定版 (這才會有 Java 17)
FROM python:3.10-slim-bookworm

# 安裝 Java (Spark 需要) 與基本工具
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless procps && \
    apt-get clean

# 設定 JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

WORKDIR /app

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 預設指令
CMD ["tail", "-f", "/dev/null"]