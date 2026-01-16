#!/bin/bash

# ========================================
# Benchmark 測試腳本
# ========================================
# 測試完整 Pipeline 的執行時間
# 對應文章 3.2 第五章的效能數據

set -e

echo "========================================="
echo "⏱️  Benchmark: Hybrid Single-GPU Architecture"
echo "========================================="
echo ""

# 清理舊數據
echo "🧹 清理舊數據..."
rm -rf data/decision_result.parquet data/decision_result.json data/clustered_result.json
echo ""

# 計時變數
TOTAL_START=$(date +%s)

# ==========================================
# Stage 1: Spark ETL (CPU 階段)
# ==========================================
echo "📊 Stage 1: Spark ETL (CPU Compute)..."
SPARK_START=$(date +%s)

python src/1_data_gen.py > /dev/null 2>&1
python src/4_decision_matrix.py 2>&1 | grep -v "WARN\|INFO" || true

SPARK_END=$(date +%s)
SPARK_TIME=$((SPARK_END - SPARK_START))
echo "✅ Stage 1 完成: ${SPARK_TIME}s"
echo ""

# ==========================================
# Stage 2: RAPIDS GPU (GPU 階段)
# ==========================================
echo "⚡ Stage 2: RAPIDS GPU (GPU Compute)..."
RAPIDS_START=$(date +%s)

python src/6_ai_clustering.py 2>&1 | grep -E "Loading|GPU|CPU|完成|Done"

RAPIDS_END=$(date +%s)
RAPIDS_TIME=$((RAPIDS_END - RAPIDS_START))
echo "✅ Stage 2 完成: ${RAPIDS_TIME}s"
echo ""

# ==========================================
# 總結報告
# ==========================================
TOTAL_END=$(date +%s)
TOTAL_TIME=$((TOTAL_END - TOTAL_START))

echo "========================================="
echo "📈 Benchmark Results"
echo "========================================="
echo ""
echo "Total Execution Time: ${TOTAL_TIME}s"
echo ""
echo "詳細拆解:"
echo "├─ Stage 1 (Spark ETL):   ${SPARK_TIME}s"
echo "│  ├─ 資料生成 + 清洗"
echo "│  └─ Parquet 輸出"
echo "└─ Stage 2 (RAPIDS GPU):  ${RAPIDS_TIME}s"
echo "   ├─ Parquet 讀取"
echo "   ├─ K-Means 聚類"
echo "   └─ 結果輸出"
echo ""
echo "========================================="
echo "💡 效能洞察"
echo "========================================="
echo ""
echo "Spark (CPU) 處理時間: ${SPARK_TIME}s"
echo "  - 邏輯複雜的 ETL 清洗工作"
echo "  - Window Function、Haversine 計算"
echo ""
echo "RAPIDS (GPU) 處理時間: ${RAPIDS_TIME}s"
echo "  - 純粹的矩陣運算 (K-Means)"
echo "  - Parquet 零解析成本"
echo ""

# 計算效能比例
SPARK_PERCENT=$((SPARK_TIME * 100 / TOTAL_TIME))
RAPIDS_PERCENT=$((RAPIDS_TIME * 100 / TOTAL_TIME))

echo "時間佔比:"
echo "  - CPU ETL:   ${SPARK_PERCENT}%"
echo "  - GPU ML:    ${RAPIDS_PERCENT}%"
echo ""
echo "結論: CPU 做邏輯，GPU 做運算，這就是混合架構的藝術。"
echo ""

# 儲存結果
echo "📊 儲存 Benchmark 結果..."
cat > benchmark_result.txt <<EOF
Benchmark Results ($(date))
====================================
Total Time:     ${TOTAL_TIME}s
Spark ETL:      ${SPARK_TIME}s (${SPARK_PERCENT}%)
RAPIDS GPU:     ${RAPIDS_TIME}s (${RAPIDS_PERCENT}%)

Architecture: Hybrid Single-GPU
- Stage 1: CPU (Apache Spark)
- Handover: Parquet (Zero-copy)
- Stage 2: GPU (NVIDIA RAPIDS)
EOF

echo "✅ 結果已儲存: benchmark_result.txt"
