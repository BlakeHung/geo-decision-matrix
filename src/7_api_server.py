import os
import json
import torch
import pandas as pd
from fastapi import FastAPI, HTTPException
from transformers import pipeline

# --- 🔥 環境與硬體配置 ---
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # 強制鎖定 x16 顯卡
DATA_FILE = 'data/clustered_result.json'

app = FastAPI(title="Geo-Decision AI Integrated System")

# --- 🚀 載入 GPU AI 模型 (NLP 顧問) ---
print("⏳ 正在加載 AI 決策模型至 RTX 3090 (GPU 0)...")
try:
    # 使用具備行為判斷能力的分析模型
    analyzer = pipeline(
        "sentiment-analysis", 
        model="distilbert-base-uncased-finetuned-sst-2-english",
        device=0 if torch.cuda.is_available() else -1
    )
    print("✅ GPU AI 模型載入成功！")
except Exception as e:
    print(f"⚠️ 模型載入失敗: {e}")
    analyzer = None

@app.get("/")
def home():
    return {
        "status": "online", 
        "engine": "FastAPI + Transformers (GPU)",
        "endpoints": ["/results", "/ai/analyze_risks"]
    }

@app.get("/results")
def get_all_results():
    """獲取分群 JSON 原始資料"""
    if not os.path.exists(DATA_FILE):
        raise HTTPException(status_code=404, detail="找不到數據，請先執行 6_ai_clustering.py")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.get("/ai/analyze_risks")
def analyze_risks():
    """使用 GPU 對高風險司機進行智慧化分析與建議"""
    if not os.path.exists(DATA_FILE):
        raise HTTPException(status_code=404, detail="資料不存在")
    
    df = pd.read_json(DATA_FILE)
    
    # --- 智慧篩選機制 ---
    # 優先抓取標籤包含 "Risk" 或 "紅色" 的司機
    risky_drivers = df[df['label'].str.contains("Risk|紅色", case=False, na=False)].head(5)
    
    # 如果標籤匹配不到，則自動抓取時速最低的前 3 名
    if risky_drivers.empty:
        print("⚠️ 標籤未匹配，改為抓取時速最低的司機進行分析...")
        risky_drivers = df.nsmallest(3, 'average_speed')

    results = []
    if analyzer:
        for _, driver in risky_drivers.iterrows():
            # 建立描述文本供 AI 分析
            status_text = f"Driver {driver['driver_id']} is traveling at {driver['average_speed']:.1f} km/h with {driver['stuck_count']} stops."
            
            # 執行 GPU 推論
            inference = analyzer(status_text)[0]
            sentiment = inference['label']
            
            # 將 AI 情感分析轉化為具體的管理建議
            management_advice = "🚨 建議立即進行安全面談，可能存在違規或疲勞駕駛。" if sentiment == "NEGATIVE" else "🟢 表現尚可，建議持續觀察路況影響。"
            
            results.append({
                "driver_id": driver['driver_id'],
                "label": driver['label'],
                "speed": f"{driver['average_speed']:.2f} km/h",
                "ai_sentiment": sentiment,
                "management_advice": management_advice
            })
    
    return {
        "status": "success",
        "processed_by": "NVIDIA RTX 3090",
        "analysis_count": len(results),
        "ai_insights": results
    }

if __name__ == "__main__":
    import uvicorn
    # 統一使用 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)