import cudf
from cuml.cluster import KMeans
from cuml.preprocessing import StandardScaler
import time
import os

# 強制只使用 GPU 0 (EVGA)，避免 NCCL 找麻煩
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

INPUT_PARQUET = 'data/cleaned_data.parquet'
OUTPUT_JSON = 'data/clustered_result.json'

def run_gpu_clustering():
    print("🚀 [Stage 2] RAPIDS GPU 加速啟動...")
    print(f"🖥️  鎖定 GPU: Device 0 (Single GPU Mode)")
    
    overall_start = time.time()

    # 1. 極速讀取 Parquet (Zero-Copy)
    # 這就是為什麼我們要用 Parquet：GPU 讀取它是「整塊吞進去」的
    print(f"📥 正在讀取 Parquet: {INPUT_PARQUET}")
    load_start = time.time()
    
    gdf = cudf.read_parquet(INPUT_PARQUET)
    
    load_time = time.time() - load_start
    print(f"⚡ 資料載入完成！筆數: {len(gdf):,} | 耗時: {load_time:.4f} 秒")

    # 2. 準備特徵 (Feature Engineering)
    # 挑選這三個特徵來決定這是不是一個「高風險」區域
    features = ['step_distance_km', 'is_stuck']
    
    # 3. GPU 標準化 (StandardScaler)
    print("⚙️ 正在進行數據標準化 (GPU)...")
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(gdf[features])

    # 4. GPU K-Means 聚類
    print("🧠 正在執行 K-Means 分群 (GPU)...")
    kmeans_start = time.time()
    
    # 分成 3 類：正常移動、異常停滯(風險)、高速移動
    kmeans = KMeans(n_clusters=3, random_state=42)
    gdf['cluster'] = kmeans.fit_predict(data_scaled)
    
    kmeans_time = time.time() - kmeans_start
    print(f"⚡ K-Means 運算完成！耗時: {kmeans_time:.4f} 秒")

    # 5. 簡單統計結果 (看看分群有沒有意義)
    print("\n📊 分群結果統計:")
    print(gdf['cluster'].value_counts())

    # 總結
    total_time = time.time() - overall_start
    print(f"\n✅ [Stage 2] 全程耗時: {total_time:.4f} 秒")
    print("-" * 50)
    print(f"🏆 效能對比：")
    print(f"   - Spark ETL (CPU): ~11.50 秒")
    print(f"   - RAPIDS (GPU):    {total_time:.4f} 秒")

if __name__ == "__main__":
    run_gpu_clustering()