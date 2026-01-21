from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
import math
import os
import time

# 設定輸入與輸出路徑
INPUT_FILE = 'data/gps_tracks.csv'
OUTPUT_PARQUET = 'data/cleaned_data.parquet'

def calculate_haversine(lat1, lon1, lat2, lon2):
    """
    計算地球表面兩點之間的距離 (km)
    這是 CPU 擅長的複雜邏輯運算
    """
    if None in [lat1, lon1, lat2, lon2]:
        return 0.0
    
    R = 6371  # 地球半徑 (km)
    
    # 將角度轉為弧度
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2)**2
        
    a = min(1.0, max(0.0, a)) # 防禦性編程：防止浮點數誤差
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def run_spark_etl():
    print("🚀 [Stage 1] Spark ETL 啟動...")
    start_time = time.time()

    # 1. 初始化 Spark Session (加上記憶體限制，防止 OOM)
    # 假設你的主機有 32GB RAM，這裡我們給 Spark 8GB 堆內 + 2GB 堆外
    spark = SparkSession.builder \
        .appName("GeoDecisionMatrix_ETL") \
        .config("spark.driver.memory", "8g") \
        .config("spark.executor.memory", "8g") \
        .config("spark.memory.offHeap.enabled", "true") \
        .config("spark.memory.offHeap.size", "2g") \
        .getOrCreate()

    # 註冊 UDF
    haversine_udf = F.udf(calculate_haversine, DoubleType())

    # 2. 讀取 CSV (Row-based, 慢)
    print(f"📥 正在讀取 CSV: {INPUT_FILE}")
    df = spark.read.csv(INPUT_FILE, header=True, inferSchema=True)

    # 3. 定義 Window (按使用者分組，按時間排序)
    # 這是 GPU 最怕的邏輯 (前後依賴)，交給 CPU 做
    window_spec = Window.partitionBy("user_id").orderBy("timestamp")

    # 4. 資料清洗邏輯
    print("⚙️ 執行複雜清洗邏輯 (Lag + Haversine)...")
    
    # 取得前一筆的經緯度 (Lag)
    df_lag = df.withColumn("prev_lat", F.lag("latitude").over(window_spec)) \
               .withColumn("prev_lon", F.lag("longitude").over(window_spec))

    # 計算距離 (使用 UDF)
    df_detailed = df_lag.withColumn("step_distance_km", 
        haversine_udf("prev_lat", "prev_lon", "latitude", "longitude")
    ).na.fill(0.0, subset=["step_distance_km"])

    # 標記異常停滯 (Stuck)
    df_clean = df_detailed.withColumn("is_stuck", 
        F.when(F.col("step_distance_km") == 0.0, 1).otherwise(0)
    )

    # 5. 寫入 Parquet (Column-based, 快)
    # 這是 GPU 喜歡的格式：零解析成本、合併記憶體讀取
    print(f"💾 正在寫入 Parquet: {OUTPUT_PARQUET}")
    
    # coalesce(1) 是為了強制輸出成單一檔案 (方便展示)，生產環境通常不這樣做
    df_clean.write.parquet(
        OUTPUT_PARQUET, 
        mode="overwrite", 
        compression="snappy"
    )

    elapsed = time.time() - start_time
    print(f"✅ [Stage 1] Spark ETL 完成！耗時: {elapsed:.2f} 秒")
    
    spark.stop()

if __name__ == "__main__":
    run_spark_etl()