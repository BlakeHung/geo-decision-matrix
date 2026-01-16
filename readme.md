# Geo Decision Matrix

**混合架構實戰：Spark (CPU) + RAPIDS (GPU) 的地理決策支援系統**

## 📖 專案簡介

這是一個展示「**CPU + GPU 混合架構**」的真實工程案例，用於解決地圖 API 供應商遷移評估問題。

**核心理念**：
- **CPU (Apache Spark)** 處理邏輯複雜的 ETL 清洗
- **Parquet** 作為零拷貝的高速傳輸橋樑
- **GPU (NVIDIA RAPIDS)** 專注純粹的矩陣運算

**效能對比**：
- ❌ Node.js 單機：數小時 / OOM
- ❌ Dask Multi-GPU（雙卡）：420 秒（通訊 overhead）
- ✅ Spark + RAPIDS（單卡）：**150 秒**（2.8x 加速）

---

## 🏗️ 技術架構

\`\`\`
Raw Data (500K GPS)
    ↓
┌─────────────────────────────────┐
│ Stage 1: Apache Spark (CPU)    │
│ - ETL 清洗                       │
│ - Window Function               │
│ - Haversine 距離計算             │
│ 執行時間: ~145 秒                │
└─────────────────────────────────┘
    ↓ (Parquet 零拷貝)
┌─────────────────────────────────┐
│ Stage 2: NVIDIA RAPIDS (GPU)   │
│ - K-Means 聚類                   │
│ - 標準化 (StandardScaler)        │
│ 執行時間: ~5 秒                  │
└─────────────────────────────────┘
    ↓
Decision Matrix API
\`\`\`

---

## 🚀 快速開始

### 前置需求

- Docker + Docker Compose
- NVIDIA GPU（支援 CUDA 11.8+）
- NVIDIA Container Toolkit

### 方法 1：使用 Docker（推薦）

\`\`\`bash
# 1. Clone 專案
git clone https://github.com/your-username/geo-decision-matrix.git
cd geo-decision-matrix

# 2. 啟動 Docker 容器
docker-compose up -d

# 3. 進入容器
docker exec -it geo_decision_matrix bash

# 4. 執行完整 Pipeline
./run_pipeline.sh
\`\`\`

### 方法 2：本地環境

\`\`\`bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 安裝 RAPIDS（需要 CUDA 環境）
conda install -c rapidsai -c nvidia -c conda-forge \
    rapids=23.10 python=3.10 cudatoolkit=11.8

# 3. 執行 Pipeline
./run_pipeline.sh
\`\`\`

---

## 📊 執行流程詳解

### Step 1: 資料生成

\`\`\`bash
python src/1_data_gen.py
\`\`\`

生成 50 萬筆模擬 GPS 軌跡數據（26 MB CSV）。

**關鍵特色**：
- 定向注入髒數據（重疊座標、瞬間移動）
- 測試系統對 Edge Case 的穩健性

### Step 2: Spark ETL 清洗

\`\`\`bash
python src/4_decision_matrix.py
\`\`\`

使用 Apache Spark 進行 CPU 密集型處理：
- **Window Function**：計算每一步的 GPS 距離
- **Haversine UDF**：地球表面兩點距離公式
- **異常檢測**：標記停滯點（倖存者偏差指標）

**輸出**：
- \`data/decision_result.parquet\`（GPU 最佳化格式）
- \`data/decision_result.json\`（API 相容格式）

**技術亮點**：
\`\`\`python
# Parquet 輸出（Snappy 壓縮）
decision_matrix.write.parquet(
    "data/decision_result.parquet",
    mode="overwrite",
    compression="snappy"  # GPU 友善的壓縮格式
)
\`\`\`

**為何使用 Parquet？**
- ✅ **Coalesced Memory Access**（合併記憶體存取）
- ✅ **零解析成本**（二進制直讀，無需字串轉換）
- ✅ **Memory Mapping**（mmap + CUDA Unified Memory）

### Step 3: RAPIDS GPU 聚類

\`\`\`bash
python src/6_ai_clustering.py
\`\`\`

使用 NVIDIA RAPIDS 進行 GPU 加速：
- **cuDF**：GPU DataFrame（類似 Pandas）
- **cuML**：GPU 機器學習（類似 scikit-learn）

**技術亮點**：
\`\`\`python
# GPU 直接讀取 Parquet（零拷貝）
gdf = cudf.read_parquet("data/decision_result.parquet")

# GPU K-Means 聚類（0.5 秒完成）
kmeans = cuKMeans(n_clusters=3, random_state=42)
labels = kmeans.fit_predict(X_scaled)
\`\`\`

**自動降級機制**：
- 優先使用 GPU (cuDF + cuML)
- 如果 GPU 不可用，自動降級至 CPU (Pandas + scikit-learn)

---

## ⏱️ Benchmark 測試

執行完整的效能測試：

\`\`\`bash
./benchmark.sh
\`\`\`

**輸出範例**：
\`\`\`
📈 Benchmark Results
====================================
Total Execution Time: 150s

詳細拆解:
├─ Stage 1 (Spark ETL):   145s (97%)
│  ├─ 資料生成 + 清洗
│  └─ Parquet 輸出
└─ Stage 2 (RAPIDS GPU):  5s (3%)
   ├─ Parquet 讀取 (0.8s)
   ├─ K-Means 聚類 (0.5s)
   └─ 結果輸出 (3.7s)
\`\`\`

---

## 📁 專案結構

\`\`\`
geo-decision-matrix/
├─ src/
│  ├─ 1_data_gen.py                    # 資料生成器
│  ├─ 4_decision_matrix.py             # Spark ETL (CPU)
│  ├─ 6_ai_clustering.py               # RAPIDS GPU (主要版本)
│  ├─ 6_ai_clustering_distributed.py   # 雙 GPU 版本（3.1 失敗案例）
│  ├─ 7_api_server.py                  # FastAPI 服務
│  ├─ 9_dashboard.py                   # Streamlit 儀表板
│  └─ article_visualizations.py        # 技術文章圖表生成器
├─ doc/
│  ├─ 3.1article_visual.md             # 3.1 文章規劃（硬體限制）
│  ├─ 3.2_article_plan.md              # 3.2 文章規劃（架構救贖）
│  └─ 3.2_article_content.md           # 3.2 完整文章（3500字）
├─ outputs/
│  ├─ article_topology_bottleneck.png  # 硬體頻寬牆圖表
│  ├─ article_hybrid_architecture.png  # 混合架構流程圖
│  └─ article_benchmark_comparison.png # Benchmark 對比圖
├─ data/                               # 數據目錄（執行後生成）
├─ Dockerfile                          # RAPIDS + Spark 容器
├─ docker-compose.yml                  # Docker Compose 配置
├─ run_pipeline.sh                     # 完整執行腳本
├─ benchmark.sh                        # 效能測試腳本
└─ README.md                           # 本文件
\`\`\`

---

## 🎯 關鍵技術點

### 1. Window Function（Spark）

\`\`\`python
# 計算每一步的 GPS 移動距離
window_spec = Window.partitionBy("user_id").orderBy("timestamp")
df_lag = df.withColumn("prev_lat", F.lag("latitude").over(window_spec)) \
           .withColumn("prev_lon", F.lag("longitude").over(window_spec))
\`\`\`

### 2. Parquet 列式儲存優勢

**CSV (Row-based)**：
\`\`\`
Record 1: [id, lat, lon, speed]
Record 2: [id, lat, lon, speed]
Record 3: [id, lat, lon, speed]
\`\`\`
GPU 讀取 \`speed\` 欄位時需要跳躍存取（32 次記憶體請求）

**Parquet (Column-based)**：
\`\`\`
Column speed: [25.3, 42.1, 18.7, ...]（連續儲存）
\`\`\`
GPU 讀取 \`speed\` 欄位時一次性載入（1 次記憶體請求）

**效能差異**：32 倍加速

### 3. GPU 自動降級機制

\`\`\`python
if GPU_AVAILABLE:
    try:
        # 嘗試 GPU 運算
        gdf = cudf.read_parquet("data.parquet")
        kmeans = cuKMeans(n_clusters=3)
    except Exception as e:
        # 自動降級至 CPU
        GPU_AVAILABLE = False
        return perform_clustering(df)
else:
    # CPU Fallback
    df = pd.read_parquet("data.parquet")
    kmeans = KMeans(n_clusters=3)
\`\`\`

---

## 📈 視覺化圖表

專案包含 3 張高品質技術圖表（\`outputs/\` 目錄）：

### 1. 硬體頻寬牆
![Topology Bottleneck](outputs/article_topology_bottleneck.png)

展示 NVLink (900 GB/s) vs PCIe Detour (12 GB/s) 的對比。

### 2. 混合架構流程
![Hybrid Architecture](outputs/article_hybrid_architecture.png)

完整的 CPU → Parquet → GPU 資料流程。

### 3. Benchmark 對比
![Benchmark](outputs/article_benchmark_comparison.png)

綠色 150s (單 GPU) vs 紅色 420s (雙 GPU)，證明「少即是多」。

---

## 🛠️ 進階使用

### 啟動完整服務

\`\`\`bash
# 1. 啟動 API 服務
python src/7_api_server.py
# 訪問: http://localhost:9090

# 2. 啟動 Streamlit 儀表板
streamlit run src/9_dashboard.py
# 訪問: http://localhost:8501

# 3. 查看 Spark UI（執行 ETL 時）
# 訪問: http://localhost:4040
\`\`\`

### 生成文章圖表

\`\`\`bash
# 生成技術文章所需的視覺化圖表
python src/article_visualizations.py
\`\`\`

輸出：
- \`outputs/article_topology_bottleneck.png\`
- \`outputs/article_hybrid_architecture.png\`
- \`outputs/article_benchmark_comparison.png\`

---

## 🐛 常見問題

### Q1: 執行時出現 "CUDA out of memory"

**解決方案**：
\`\`\`python
# 減少數據量或啟用 RAPIDS Managed Memory
import rmm
rmm.reinitialize(managed_memory=True)
\`\`\`

### Q2: WSL 2 環境雙 GPU 錯誤

**解決方案**：
\`\`\`bash
# 使用單 GPU 版本
export CUDA_VISIBLE_DEVICES=0
python src/6_ai_clustering.py
\`\`\`

或使用 WSL 安全版本：
\`\`\`bash
python src/6_ai_clustering_wsl_safe.py
\`\`\`

### Q3: Spark 找不到 Java

**解決方案**：
\`\`\`bash
# 安裝 OpenJDK
apt-get update && apt-get install -y openjdk-11-jdk

# 設定環境變數
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
\`\`\`

---

## 📚 相關文章

- **3.1 硬體限制篇**：為何雙 GPU 反而更慢？（\`doc/3.1article_visual.md\`）
- **3.2 軟體救贖篇**：混合架構實戰（\`doc/3.2_article_content.md\`）

---

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

## 📄 授權

MIT License

---

## 🙏 致謝

- **Apache Spark**：分散式 ETL 框架
- **NVIDIA RAPIDS**：GPU 加速資料科學
- **PyArrow**：高效的列式儲存
- **Docker**：容器化部署

---

**關鍵字**：Hybrid Architecture, Spark RAPIDS, Parquet GPU, Data Engineering, ETL Pipeline, cuDF cuML, Memory Mapping, Coalesced Access

**專案作者**：Blake  
**最後更新**：2026-01-08
