from fastapi import FastAPI, HTTPException
from transformers import pipeline
import pandas as pd
import torch
import os
import json

app = FastAPI(title="Logistics AI Decision Support")

# --- 🔥 GPU 配置 ---
# 強制 PyTorch 使用 GPU 0 (x16 通道那張)
DEVICE = 0 if torch.cuda.is_available() else -1
print(f"🚀 AI 顧問引擎啟動中... 使用裝置: {'RTX 3090 (GPU 0)' if DEVICE == 0 else 'CPU'}")

# 載入一個適合分析情緒與行為的分類模型 (或是更強大的文本生成模型)
# 這裡先使用一個快速的 Sentiment 模型作為示範，你也可以換成 Llama-3-8B
analyzer = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english", device=DEVICE)

DATA_FILE = 'data/clustered_result.json'

@app.get("/ai/analyze_risks")
def analyze_risks():
    if not os.path.exists(DATA_FILE):
        raise HTTPException(status_code=404, detail="請先執行分群腳本產生資料")

    df = pd.read_json(DATA_FILE)
    # 只針對「紅色警戒」的司機進行深度分析
    risky_drivers = df[df['label'].str.contains("紅色警戒")].head(5) # 先取前 5 位測試

    results = []
    for _, driver in risky_drivers.iterrows():
        # 建立分析文本
        prompt = f"Driver {driver['driver_id']} is driving at {driver['average_speed']:.1f} km/h with {driver['stuck_count']} congestion events."
        
        # GPU 推論
        ai_output = analyzer(prompt)
        
        # 根據 AI 結果給予建議
        sentiment = ai_output[0]['label']
        recommendation = "建議安排安全教育面談" if sentiment == "NEGATIVE" else "觀察其塞車情況是否緩解"
        
        results.append({
            "driver_id": driver['driver_id'],
            "status": driver['label'],
            "ai_sentiment": sentiment,
            "management_action": recommendation
        })

    return {
        "status": "success",
        "ai_insights": results
    }

if __name__ == "__main__":
    import uvicorn
    # 改用 8001 端口，避免與之前的 API 伺服器衝突
    uvicorn.run(app, host="0.0.0.0", port=8001)