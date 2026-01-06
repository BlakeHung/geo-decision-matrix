import os
# 強制隔離 GPU 1，只看 GPU 0 (x16)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["NCCL_P2P_DISABLE"] = "1"

import json
import pandas as pd
import numpy as np
import time

# 全域變數初始化
GPU_AVAILABLE = False

# --- 🔥 NVIDIA RAPIDS 初始化 ---
try:
    import rmm
    rmm.reinitialize(managed_memory=True)
    print("✅ [RMM] Managed Memory 啟動")
except:
    pass 

try:
    import cudf
    from cuml.cluster import KMeans as cuKMeans
    from cuml.preprocessing import StandardScaler as cuStandardScaler
    GPU_AVAILABLE = True
    print("🚀 [System] RAPIDS 準備就緒 (RTX 3090)")
except Exception as e:
    GPU_AVAILABLE = False
    print(f"⚠️ GPU 不可用，將使用 CPU 模式")

INPUT_FILE = 'data/decision_result.json'
OUTPUT_FILE = 'data/clustered_result.json'

def generate_mock_data():
    print("⚠️ 正在生成測試數據...")
    data = []
    for i in range(5000): 
        data.append({
            "driver_id": f"D_{np.random.randint(1000,9999)}",
            "total_km": np.random.uniform(5, 50),
            "average_speed": np.random.uniform(10, 80),
            "stuck_count": np.random.randint(0, 10)
        })
    return pd.DataFrame(data)

def perform_clustering(df):
    global GPU_AVAILABLE  # 👈 修正關鍵：宣告全域變數
    
    print(f"📊 處理數據量: {len(df)} 筆")
    features = ['total_km', 'average_speed', 'stuck_count']
    
    # 檢查欄位是否存在
    for col in features:
        if col not in df.columns:
            print(f"❌ 缺少欄位 {col}，使用模擬數據")
            return perform_clustering(generate_mock_data())

    if GPU_AVAILABLE:
        try:
            print("⚡ [GPU Mode] 嘗試進行分群...")
            start_time = time.time()
            gdf = cudf.DataFrame.from_pandas(df[features])
            
            scaler = cuStandardScaler()
            X_scaled = scaler.fit_transform(gdf)
            
            kmeans = cuKMeans(n_clusters=3, random_state=42)
            df['cluster'] = kmeans.fit_predict(X_scaled).to_pandas()
            
            print(f"⚡ [GPU Done] 耗時: {time.time() - start_time:.4f}s")
        except Exception as e:
            print(f"⚠️ GPU 運算失敗 ({e})，自動切換至 CPU...")
            GPU_AVAILABLE = False
            return perform_clustering(df) # 重新嘗試 CPU 模式
    else:
        print("🐢 [CPU Mode] 執行中...")
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        start_time = time.time()
        X = df[features]
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        kmeans = KMeans(n_clusters=3, n_init='auto', random_state=42)
        df['cluster'] = kmeans.fit_predict(X_scaled)
        print(f"🐢 [CPU Done] 耗時: {time.time() - start_time:.4f}s")

    # 標籤賦予
    avg_speeds = df.groupby('cluster')['average_speed'].mean()
    labels = {avg_speeds.idxmin(): "Risk: Congested", 
              avg_speeds.idxmax(): "Good: Efficient"}
    
    df['label'] = df['cluster'].map(lambda x: labels.get(x, "Normal: Average"))
    return df

def main():
    # 讀取或生成資料
    if os.path.exists(INPUT_FILE):
        try:
            with open(INPUT_FILE, 'r') as f:
                df = pd.DataFrame(json.load(f))
        except:
            df = generate_mock_data()
    else:
        df = generate_mock_data()

    # 執行分群
    df_result = perform_clustering(df)
    
    # 儲存
    os.makedirs('data', exist_ok=True)
    df_result.to_json(OUTPUT_FILE, orient='records', force_ascii=False, indent=2)
    print(f"💾 結果已儲存: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()