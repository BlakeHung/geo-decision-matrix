
# Geo Decision Matrix: 重建地圖決策系統

> 這是部落格系列文章 **[Map API Migration Trilogy]** 的實作專案。
> 連結：[第一部曲：倖存者偏差如何讓我失去信心](你的部落格連結)

## 專案背景 (The Story)
幾年前，我因為依賴 Node.js 單機腳本抽樣驗證地圖 API，導致了嚴重的「倖存者偏差」誤判。
這個專案旨在利用現代化數據架構 (**Apache Spark + LLM**)，重建當年的決策流程，證明如何透過全量數據分析與 AI 輔助，避免商業邏輯上的災難。

## 專案架構
* **Stage 1: Data Generation** (`src/1_data_gen.py`)
    * 模擬 100 萬筆 B2B 訂單數據。
    * 定向注入 "Edge Case"（如新竹重劃區的圖資缺失），模擬真實世界的長尾風險。
* **Stage 2: Spark ETL** (`src/2_spark_etl.py`)
    * 使用 PySpark 進行全量數據清洗與距離計算。
    * 識別潛在的賠償風險區域。
* **Stage 3: AI Decision (Coming Soon)**
    * 整合 LLM 進行 ROI 風險評估。

## 如何執行 (How to Run)

### 1. 啟動環境
```bash
docker-compose up -d

```

### 2. 生成模擬數據 (1M records)

```bash
python src/1_data_gen.py

```

### 3. 執行 Spark 全量分析

```bash
docker exec -it spark-master spark-submit /app/src/2_spark_etl.py

```
