import os
import time
import numpy as np
import pandas as pd

# --- 🔥 [核心配置] 針對無 NVLink 的雙卡環境 ---
# 既然沒有 NVLink，我們必須徹底切斷所有顯卡間的直接通訊
os.environ["NCCL_P2P_DISABLE"] = "1"
os.environ["NCCL_P2P_LEVEL"] = "0"    # 強制不使用 P2P
os.environ["NCCL_IB_DISABLE"] = "1"

# 徹底禁用 UCX，改用 Dask 內建的 Tornado TCP
# 這是避開 Segmentation Fault (UCX 崩潰) 的最終手段
os.environ["DASK_UCX__CUDA_COPY"] = "False"
os.environ["DASK_UCX__TCP"] = "False"

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

def main():
    # --- 1. 啟動雙卡指揮官 (不使用 UCX) ---
    print("⚡ 正在初始化 Dask CUDA Cluster (No-NVLink 安全模式)...")
    try:
        # protocol="tcp" 配合 enable_tcp_over_ucx=False 
        # 會強制讓 Dask 走最穩定的 Python TCP 通訊
        cluster = LocalCUDACluster(
            rmm_managed_memory=True,   # WSL 2 必開
            threads_per_worker=1,
            protocol="tcp",            # 走 TCP 通訊
            enable_tcp_over_ucx=False, # 禁用 UCX
            enable_nvlink=False,       # 禁用 NVLink (您已確認沒有)
            enable_infiniband=False    # 禁用 InfiniBand
        )
        client = Client(cluster)
        print(f"✅ 雙卡叢集啟動成功！")
        
        workers = client.scheduler_info()['workers']
        print(f"   Workers: {len(workers)} (應該是 2)")
    except Exception as e:
        print(f"❌ 雙卡啟動失敗: {e}")
        return

    # --- 2. 準備數據 ---
    start_time = time.time()
    # 既然有兩張 3090 (48GB VRAM)，我們把數據量開大到 10 萬筆測試
    print("⚠️ 生成 100,000 筆模擬數據以測試雙卡算力...")
    pdf = pd.DataFrame({
        "driver_id": [f"D_{i}" for i in range(100000)],
        "total_km": np.random.uniform(5, 50, 100000),
        "average_speed": np.random.uniform(10, 80, 100000),
        "stuck_count": np.random.randint(0, 10, 100000).astype(float)
    })
    
    # --- 3. 將數據分發給兩張顯卡 ---
    print("⚡ [GPU] 正在將數據切割並分發至兩張 3090...")
    
    # 將數據切成兩份，Dask 會自動把其中一份丟到 GPU 0，另一份丟到 GPU 1
    ddf_cpu = dd.from_pandas(pdf, npartitions=2)
    ddf_gpu = ddf_cpu.map_partitions(cudf.DataFrame.from_pandas)

    features = ['total_km', 'average_speed', 'stuck_count']
    X_dask = ddf_gpu[features]

    # --- 4. 雙卡同步運算 ---
    print("⚡ [GPU] 開始並行 K-Means 聚類運算...")
    
    # 這裡 cuML 會在背景同步兩個 GPU 的聚類中心點
    kmeans = DaskKMeans(n_clusters=3, random_state=42)
    kmeans.fit(X_dask)
    
    ddf_gpu['cluster'] = kmeans.predict(X_dask)

    # --- 5. 彙整結果 ---
    print("⚡ [Result] 正在從顯卡回收結果...")
    final_df = ddf_gpu.compute().to_pandas()
    
    duration = time.time() - start_time
    print(f"🚀 [Done] 雙卡運算完成！總耗時: {duration:.4f} 秒")
    print(f"📊 總處理筆數: {len(final_df)}")

    client.close()
    cluster.close()

if __name__ == "__main__":
    main()