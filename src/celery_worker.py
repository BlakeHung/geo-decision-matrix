import os
import time
import torch
from celery import Celery
from transformers import pipeline

# ==========================================
# 1. 配置設定 (Configuration)
# ==========================================
# Redis 連線設定 (Docker 內部 localhost 即可，因為 Redis 與 Worker 在同個容器)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 初始化 Celery 應用
# 'geo_ai_worker' 是這個應用程式的名稱
app = Celery('geo_ai_worker', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# ==========================================
# 2. 模型熱啟動 (Global Model Loading)
# ==========================================
# 關鍵優化：在 Global Scope 載入模型，確保 Worker 啟動時只載入一次。
# 這避免了每次任務都重新讀取模型 (Cold Start) 的巨大開銷。

print("⏳ [System] 正在初始化 AI 模型 (Warm Start)...")

try:
    # 檢查 GPU 是否可用
    device_id = 0 if torch.cuda.is_available() else -1
    device_name = torch.cuda.get_device_name(0) if device_id != -1 else "CPU"
    
    # 使用 HuggingFace Pipeline 載入模型
    # 這裡使用 distilbert 做情感分析，模擬「駕駛行為風險評估」
    risk_analyzer = pipeline(
        "sentiment-analysis", 
        model="distilbert-base-uncased-finetuned-sst-2-english",
        device=device_id
    )
    print(f"✅ [System] 模型載入成功！")
    print(f"🚀 [Hardware] 運行裝置: {device_name}")

except Exception as e:
    print(f"❌ [System] 模型載入失敗: {e}")
    risk_analyzer = None

# ==========================================
# 3. 定義任務 (The Task)
# ==========================================
@app.task(bind=True)
def analyze_driver_risk(self, driver_id, speed, stuck_count):
    """
    這是一個被 Celery 管理的非同步任務。
    它接收駕駛數據，進行 AI 推論，並返回 JSON 結果。
    """
    start_time = time.time()
    
    # 1. 構建 Prompt (將數字轉為語意)
    # 假設：卡住次數多且速度慢 -> 負面 (High Risk)
    context_text = f"Driver {driver_id} is driving at {speed} km/h and got stuck {stuck_count} times."
    
    try:
        # 2. 執行 AI 推論 (Inference)
        if risk_analyzer:
            # 模型輸出範例: [{'label': 'NEGATIVE', 'score': 0.99}]
            result = risk_analyzer(context_text)[0]
            label = result['label']
            confidence = result['score']
            
            # 轉換為業務邏輯
            risk_level = "High Risk" if label == "NEGATIVE" else "Safe"
        else:
            # Fallback (如果模型沒載入成功)
            risk_level = "Unknown (Model Error)"
            confidence = 0.0

        # 3. 計算處理時間
        process_time = time.time() - start_time
        
        # 4. 回傳結構化資料 (這會被存回 Redis)
        return {
            "driver_id": driver_id,
            "risk_level": risk_level,
            "ai_confidence": round(confidence, 4),
            "process_time": f"{process_time:.4f}s",
            "processor": f"Celery Worker on {device_name}"
        }

    except Exception as e:
        return {
            "driver_id": driver_id,
            "error": str(e),
            "status": "Failed"
        }