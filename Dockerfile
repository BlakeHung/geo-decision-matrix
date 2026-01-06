# 基礎映像檔：NVIDIA Rapids (CUDA 11.8 + Python 3.10)
FROM rapidsai/base:23.10-cuda11.8-py3.10

# 切換為 Root 權限以安裝系統套件
USER root

# 1. 安裝系統層級依賴 (Redis 伺服器)
# - redis-server: 訊息佇列 Broker
# - libgl1: Streamlit/CV 相關依賴
RUN apt-get update && \
    apt-get install -y redis-server libgl1 && \
    rm -rf /var/lib/apt/lists/*

# 2. 安裝 Python 核心架構 (一次裝好，永不遺失)
# - celery[redis]: 非同步任務
# - watchdog: 監控檔案變動
# - torch/transformers: AI 核心
RUN pip install --no-cache-dir \
    torch transformers accelerate \
    fastapi uvicorn \
    streamlit plotly \
    celery[redis] redis flower watchdog

# 3. 設定工作目錄
WORKDIR /workspace

# 4. 預設啟動指令
CMD ["bash"]