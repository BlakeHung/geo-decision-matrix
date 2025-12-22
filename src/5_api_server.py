from fastapi import FastAPI, HTTPException
import json
import os
from typing import List, Dict
from datetime import datetime

# 初始化 FastAPI 應用
app = FastAPI(
    title="Geo Decision Matrix API",
    description="提供城市運營決策數據的微服務",
    version="1.0.0"
)

# 指定資料來源 (剛剛 Spark 跑出來的結果)
DATA_FILE = "data/decision_result.json"

@app.get("/")
def read_root():
    """ 系統健康檢查 """
    return {
        "system": "Geo Decision Matrix",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/report", response_model=List[Dict])
def get_decision_matrix():
    """
    回傳最新的城市運營評分報告
    """
    if not os.path.exists(DATA_FILE):
        raise HTTPException(status_code=404, detail="報告尚未生成，請先執行 Spark 運算任務。")
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取資料失敗: {str(e)}")

@app.get("/status")
def get_data_status():
    """ 檢查資料檔案的最後更新時間 """
    if not os.path.exists(DATA_FILE):
        return {"data_ready": False, "message": "File not found"}
    
    timestamp = os.path.getmtime(DATA_FILE)
    last_modified = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        "data_ready": True,
        "last_update": last_modified,
        "source": DATA_FILE
    }

if __name__ == "__main__":
    import uvicorn
    # 啟動 Web Server，監聽所有 IP (0.0.0.0) 以便 Windows 存取
    print(">>> 啟動 API 伺服器...")
    print(">>> 請在 Windows 瀏覽器開啟: http://localhost:8000/report")
    uvicorn.run(app, host="0.0.0.0", port=8080)