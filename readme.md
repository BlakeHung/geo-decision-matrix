# Geo Decision Matrix

**CPU + GPU 混合架構的地理決策系統** — Spark ETL + Parquet + RAPIDS

---

## 專案簡介

地圖 API 供應商遷移評估系統，展示如何用混合架構處理 50 萬筆 GPS 數據。

| 方案                     | 時間        | 狀態            |
| ---------------------- | --------- | ------------- |
| Node.js 單機             | 數小時 / OOM | ❌             |
| Dask Multi-GPU（雙卡）     | 420s      | ❌ 通訊 overhead |
| **Spark + RAPIDS（單卡）** | **150s**  | ✅             |

---

## 架構

```
Raw Data (500K GPS)
       ↓
┌──────────────────────────────┐
│  Stage 1: Spark (CPU)        │  145s
│  - ETL 清洗                   │
│  - Window Function           │
│  - Haversine 距離計算         │
└──────────────────────────────┘
       ↓ Parquet (零拷貝)
┌──────────────────────────────┐
│  Stage 2: RAPIDS (GPU)       │  5s
│  - K-Means 聚類               │
│  - StandardScaler            │
└──────────────────────────────┘
       ↓
  Decision Matrix API
```

---

## 快速開始

### 前置需求

- Docker + NVIDIA Container Toolkit
- NVIDIA GPU（CUDA 11.8+）

### 執行

```bash
# 1. 啟動容器
docker-compose up -d
docker exec -it geo_decision_matrix bash

# 2. 執行 Pipeline
./run_pipeline.sh

# 3. 效能測試
./benchmark.sh
```

---

## 專案結構

```
geo-decision-matrix/
├── src/
│   ├── 1_data_gen.py              # 資料生成（50萬筆 GPS）
│   ├── 4_decision_matrix.py       # Spark ETL (CPU)
│   ├── 6_ai_clustering.py         # RAPIDS GPU 聚類
│   ├── api.py                     # FastAPI Gateway
│   ├── celery_worker.py           # GPU Worker（熱啟動）
│   └── 9_dashboard.py             # Streamlit 儀表板
├── doc/
│   ├── tech.md                    # 技術規格
│   ├── 3.2_article_content.md     # 混合架構文章
│   └── 3.2_social_posts.md        # 社群貼文
├── outputs/                       # 視覺化圖表
├── Dockerfile
├── docker-compose.yml
├── run_pipeline.sh
└── benchmark.sh
```

---

## 核心技術

### 1. Parquet vs CSV

| 特性     | CSV     | Parquet |
| ------ | ------- | ------- |
| 記憶體存取  | 跳躍（32次） | 連續（1次）  |
| GPU 加速 | ❌       | ✅ 32x   |
| 格式     | 字串解析    | 二進制直讀   |

### 2. GPU 熱啟動

```python
# 模型在 Worker 啟動時載入一次
model = pipeline("sentiment-analysis", device=0)  # 15s

@app.task
def analyze(driver_id):
    return model(driver_id)  # 0.51s
```

### 3. 微服務 API

```bash
# 非同步提交
curl -X POST http://localhost:8000/analyze \
  -d '{"driver_id": "D_1234", "speed": 25.5}'

# 輪詢結果
curl http://localhost:8000/result/{task_id}
```

---

## Benchmark

```
Total: 150s
├─ Spark ETL:  145s (97%)
│  ├─ 讀取:     12s
│  ├─ 清洗:    108s
│  └─ 輸出:     25s
└─ RAPIDS GPU:   5s (3%)
   ├─ 讀取:    0.8s
   ├─ K-Means: 0.5s
   └─ 輸出:    3.7s
```

---

## 常見問題

### CUDA out of memory

```python
import rmm
rmm.reinitialize(managed_memory=True)
```

### WSL 2 NCCL 錯誤

```bash
export CUDA_VISIBLE_DEVICES=0
export NCCL_P2P_DISABLE=1
```

---

## 相關文章

- [**3.1 硬體限制篇**：雙 GPU 反而慢 2.8 倍](https://wchung.tw/blog/local-ai-server-dual-psu-z370-nccl-error/)
- [**3.2 混合架構篇**：Spark + Parquet + RAPIDS](https://wchung.tw/blog/hybrid-architecture-spark-rapids-parquet-gpu/)
- **3.3 算力解放篇**：微服務 + 0.51s 推論

---

## License

MIT

---

**關鍵字**：Spark, RAPIDS, Parquet, GPU, Data Engineering, ETL, cuML, FastAPI, Celery

**作者**：Blake
**更新**：2026-01-21
