import os
import time
import numpy as np
import pandas as pd
import warnings

# --- 🔥 WSL 2 雙卡穩定性設定 ---
# 1. 關閉 P2P (避免 Error 201)
os.environ["NCCL_P2P_DISABLE"] = "1"

# 2. 強制 Dask 走 TCP (避免 Segmentation Fault)
os.environ["DASK_CUDA_INTERFACE"] = "eth0"
os.environ["DASK_DISTRIBUTED__COMM__TIMEOUTS__CONNECT"] = "60s"
# 確保 UCX 相關變數不會干擾 TCP 模式
os.environ["UCX_TLS"] = "tcp,cuda_copy,sockcm" 
os.environ["UCX_SOCKADDR_TLS_PRIORITY"] = "sockcm"

# 3. 關閉洩漏檢查警告
os.environ["DASK_CUDA_LEAK_CHECK"] = "0"

try:
    import cudf
    import dask.dataframe as dd
    import dask_cudf
    from dask.distributed import Client
    from dask_cuda import LocalCUDACluster
    from cuml.dask.cluster import KMeans as DaskKMeans
    RAPIDS_AVAILABLE = True
    print("🚀 [System] Dask-CUDA 模組載入成功！")
except ImportError as e:
    print(f"❌ 缺少 Dask 套件: {e}")
    exit(1)

# 設定檔案路徑
INPUT_FILE = 'data/decision_result.json'
OUTPUT_FILE = 'data/clustered_result.json'

def generate_mock_data(n_rows=10000):
    """生成模擬數據"""
    print(f"⚠️ 生成 {n_rows} 筆模擬數據...")
    df = pd.DataFrame({
        "driver_id": [f"D_{i}" for i in range(n_rows)],
        "total_km": np.random.uniform(5, 50, n_rows),
        "average_speed": np.random.uniform(10, 80, n_rows),
        "stuck_count": np.random.randint(0, 10, n_rows).astype(float)
    })
    return df

def main():
    if not RAPIDS_AVAILABLE: return

    # --- 1. 啟動雙卡指揮官 ---
    print("⚡ 正在初始化 Dask CUDA Cluster (純 TCP 模式)...")
    try:
        # [關鍵修正] 徹底關閉所有加速器，只留 TCP
        cluster = LocalCUDACluster(
            rmm_managed_memory=True,   # 必須開 (WSL 記憶體管理)
            threads_per_worker=1,
            protocol="tcp",            # 強制 TCP
            enable_tcp_over_ucx=False, # ❌ 關閉 UCX
            enable_infiniband=False,   # ❌ 關閉 InfiniBand
            enable_nvlink=False,       # ❌ 關閉 NVLink (WSL 不支援)
            jit_unspill=False
        )
        client = Client(cluster)
        print(f"✅ 雙卡叢集啟動成功！")
        
        workers = client.scheduler_info()['workers']
        print(f"   Workers: {len(workers)} (目標: 2)")
        
    except Exception as e:
        print(f"❌ 雙卡啟動失敗: {e}")
        return

    # --- 2. 準備數據 ---
    start_time = time.time()
    pdf = generate_mock_data(50000) # 5萬筆測試
    
    # --- 3. 將數據分發給兩張顯卡 ---
    print("⚡ [GPU] 正在將數據切割並傳送至 GPU 0 和 GPU 1...")
    
    # CPU Pandas -> Dask CPU -> Dask GPU
    ddf_cpu = dd.from_pandas(pdf, npartitions=2)
    ddf_gpu = ddf_cpu.map_partitions(cudf.DataFrame.from_pandas)

    features = ['total_km', 'average_speed', 'stuck_count']
    X_dask = ddf_gpu[features]

    # --- 4. 雙卡同步運算 ---
    print("⚡ [GPU] 開始並行 K-Means 聚類...")
    
    kmeans = DaskKMeans(n_clusters=3, random_state=42)
    kmeans.fit(X_dask)
    
    ddf_gpu['cluster'] = kmeans.predict(X_dask)

    # --- 5. 彙整結果 ---
    print("⚡ [Result] 正在彙整結果...")
    final_df = ddf_gpu.compute().to_pandas()
    
    duration = time.time() - start_time
    print(f"🚀 [Done] 雙卡運算完成！總耗時: {duration:.4f} 秒")
    print(f"📊 處理總筆數: {len(final_df)}")

    # 關閉連線
    client.close()
    cluster.close()

if __name__ == "__main__":
    main()