from pyspark.sql import SparkSession
from pyspark.sql.functions import col, acos, cos, sin, lit, avg, count, when
import math
import json
import os

# 啟動 Spark (單機模式)
spark = SparkSession.builder \
    .appName("GeoRiskETL") \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()

print("🔥 Spark Session 啟動成功，開始 ETL 流程...")

# 1. Extract
df = spark.read.csv("data/raw_addresses.csv", header=True, inferSchema=True)

# 2. Transform: 計算 Haversine Distance (公尺)
# 地球半徑 R = 6371 km
df = df.withColumn("error_m", 
    acos(
        sin(col("g_lat")*math.pi/180) * sin(col("m_lat")*math.pi/180) + 
        cos(col("g_lat")*math.pi/180) * cos(col("m_lat")*math.pi/180) * cos((col("m_lng")-col("g_lng"))*math.pi/180)
    ) * 6371 * 1000
)

# 定義風險單：誤差 > 50m
df = df.withColumn("is_risky", when(col("error_m") > 50, 1).otherwise(0))

# 聚合統計
result = df.groupBy("city").agg(
    avg("error_m").alias("avg_error"),
    (pd_sum := avg("is_risky")).alias("risk_rate") # avg(0/1) 即為比例
).orderBy("risk_rate", ascending=False)

# 3. Load: 顯示並儲存結果
print("📊 各城市地圖風險分析報告：")
result.show()

# 轉存 JSON 給 AI 使用
summary = [row.asDict() for row in result.collect()]
json_path = "data/risk_summary.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(f"✅ ETL 完成，知識庫已更新：{json_path}")
spark.stop()