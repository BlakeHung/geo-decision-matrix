import os
import time
import numpy as np
import pandas as pd
import warnings

# --- 🔥 [關鍵修正] WSL 2 雙卡救命丹 ---
# 這些設定告訴 Dask/NCCL：
# "我們在 WSL 虛擬機裡，不要嘗試 P2P，不要用 InfiniBand，全部走 TCP 慢車道！"

# 1. 核心變數：關閉 NCCL P2P (解決 Error 201)
os.environ["NCCL_P2P_DISABLE"] = "1"
os.environ["NCCL_IB_DISABLE"] = "1"  # 禁用 InfiniBand

# 2. Dask 通訊層：強制走 TCP
os.environ["DASK_DISTRIBUTED__COMM__DEFAULT_SCHEME"] = "tcp"
os.environ["DASK_DISTRIBUTED__COMM__TIMEOUTS__CONNECT"] = "100s" # 放寬連線超時
os.environ["DASK_CUDA_INTERFACE"] = "eth0" # 綁定 WSL 虛擬網卡

# 3. UCX 底層：封殺所有硬體加速，只留 socket
# 這是解決 "Segmentation Fault" 的絕對關鍵
os.environ["UCX_TLS"] = "tcp,cuda_copy,sockcm"
os.environ["UCX_SOCKADDR_TLS_PRIORITY"] = "sockcm"
os.environ["UCX_NET_DEVICES"] = "eth0" 

# 4. 關閉干擾項
os.environ["DASK_CUDA_LEAK_CHECK"] = "0"
os.environ["LIBCUDF_CUFILE_POLICY"] = "OFF" # 關閉 GDS (WSL 不支援)

try:
    import cudf
    import dask.dataframe as dd
    import dask_cudf
    from dask.distributed import Client
    from dask_cuda import LocalCUDACluster
    from cuml.dask.cluster import KMeans as DaskKMeans
    RAPIDS_AVAILABLE = True
    print("🚀 [System] RAPIDS 模組載入成功！")
except ImportError as e:
    print(f"❌ 缺少套件: {e}")
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
    print("⚡ 正在初始化 Dask CUDA Cluster (WSL 2 安全模式)...")
    try:
        # 這裡不傳任何 protocol 參數，完全依賴上面的 os.environ
        # 這是最乾淨的啟動方式
        cluster = LocalCUDACluster(
            rmm_managed_memory=True,   # 必開：WSL 記憶體管理
            threads_per_worker=1,
            jit_unspill=False,
            # 顯式關閉所有高階功能
            enable_tcp_over_ucx=False, 
            enable_infiniband=False,
            enable_nvlink=False,
            enable_rdmacm=False
        )
        client = Client(cluster)
        print(f"✅ 雙卡叢集啟動成功！")
        
        workers = client.scheduler_info()['workers']
        print(f"   Workers: {len(workers)} (目標: 2)")
        
    except Exception as e:
        print(f"❌ 雙卡啟動失敗: {e}")
        print("💡 建議：如果還是失敗，請先重啟 Docker 容器以清除殘留的 CUDA Context。")
        return

    # --- 2. 準備數據 ---
    start_time = time.time()
    pdf = generate_mock_data(50000) 
    
    # --- 3. 將數據分發給兩張顯卡 ---
    print("⚡ [GPU] 正在將數據切割並傳送至 GPU 0 和 GPU 1...")
    
    # Pandas (CPU) -> Dask (CPU) -> Dask cuDF (GPU)
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

    client.close()
    cluster.close()

if __name__ == "__main__":
    main()