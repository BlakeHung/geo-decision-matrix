#!/bin/bash

# ========================================
# Geo Decision Matrix - 完整執行流程
# ========================================
# 此腳本展示從資料生成 → Spark ETL → GPU 聚類的完整流程
# 對應文章 3.2 的混合架構實作

set -e  # 遇到錯誤立即停止

echo "========================================="
echo "🚀 Geo Decision Matrix Pipeline"
echo "========================================="
echo ""

# Step 1: 資料生成（50 萬筆 GPS 軌跡）
echo "📊 Step 1: 生成模擬 GPS 數據（500,000 筆）..."
python src/1_data_gen.py
echo "✅ 完成！輸出: data/gps_tracks.csv"
echo ""

# Step 2: Spark ETL 清洗（CPU 階段）
echo "🔥 Step 2: Spark ETL 資料清洗（CPU 運算）..."
echo "⏱️  預計耗時: ~145 秒"
echo "💡 提示: 可打開 http://localhost:4040 查看 Spark UI"
time python src/4_decision_matrix.py
echo "✅ 完成！輸出: data/decision_result.parquet + data/decision_result.json"
echo ""

# Step 3: RAPIDS GPU 聚類（GPU 階段）
echo "⚡ Step 3: RAPIDS GPU K-Means 聚類（GPU 運算）..."
echo "⏱️  預計耗時: ~5 秒"
time python src/6_ai_clustering.py
echo "✅ 完成！輸出: data/clustered_result.json"
echo ""

# 總結
echo "========================================="
echo "✅ Pipeline 執行完畢！"
echo "========================================="
echo ""
echo "📁 生成的檔案："
ls -lh data/decision_result.parquet 2>/dev/null && echo "  - decision_result.parquet (GPU 最佳化格式)"
ls -lh data/decision_result.json 2>/dev/null && echo "  - decision_result.json (API 相容格式)"
ls -lh data/clustered_result.json 2>/dev/null && echo "  - clustered_result.json (聚類結果)"
echo ""
echo "🎯 下一步："
echo "  - 啟動 API: python src/7_api_server.py"
echo "  - 啟動 Dashboard: streamlit run src/9_dashboard.py"
echo "  - 查看文章: doc/3.2_article_content.md"
