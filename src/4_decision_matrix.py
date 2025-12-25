from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
import math
import time  # <--- 新增這個

# --- 核心邏輯：Haversine 公式 ---
def calculate_haversine(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return 0.0
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    a = min(1.0, max(0.0, a))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def main():
    spark = SparkSession.builder.appName("GeoDecisionMatrix").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    print(">>> [ETL] 讀取並前處理數據...")
    df = spark.read.csv("data/gps_tracks.csv", header=True, inferSchema=True)

    # 1. 計算每一步的距離
    window_spec = Window.partitionBy("user_id").orderBy("timestamp")
    df_lag = df.withColumn("prev_lat", F.lag("latitude").over(window_spec)) \
               .withColumn("prev_lon", F.lag("longitude").over(window_spec))
    
    haversine_udf = F.udf(calculate_haversine, DoubleType())
    
    df_detailed = df_lag.withColumn("step_distance", 
        haversine_udf("prev_lat", "prev_lon", "latitude", "longitude")
    ).na.fill(0.0, subset=["step_distance"])

    # 2. 定義「異常停滯」
    df_detailed = df_detailed.withColumn("is_stuck", 
        F.when(F.col("step_distance") == 0.0, 1).otherwise(0)
    )

    print(">>> [Aggregation] 執行決策聚合分析...")
    
    # 3. 聚合計算
    decision_matrix = df_detailed.groupBy("city", "user_id").agg(
        F.sum("step_distance").alias("total_km"),
        F.count("timestamp").alias("total_records"),
        F.sum("is_stuck").alias("stuck_count")
    )

    # 4. 計算最終分數
    decision_matrix = decision_matrix.withColumn("final_score", 
        (F.col("total_km") * 100) - (F.col("stuck_count") * 20)
    )

    # 格式化
    decision_matrix = decision_matrix.withColumn("total_km", F.round("total_km", 4)) \
                                     .withColumn("final_score", F.round("final_score", 2))

    print("\n========= 城市運營決策矩陣 (Decision Matrix) =========")
    decision_matrix.orderBy(F.desc("final_score")).show(truncate=False)

    # --- 匯出結果為 JSON ---
    print(">>> [Export] 正在匯出結果為 JSON...")
    output_file = "data/decision_result.json"
    pandas_df = decision_matrix.orderBy(F.desc("final_score")).toPandas()
    pandas_df.to_json(output_file, orient="records", force_ascii=False, indent=4)
    print(f">>> 匯出完成！API 伺服器將讀取此檔案：{output_file}")

    # ==========================================
    # 這裡就是關鍵！讓程式暫停 300 秒 (5分鐘)
    # ==========================================
    print("\n>>> [UI MODE] 程式已暫停，請立刻打開瀏覽器：http://localhost:4040")
    print(">>> (5 分鐘後將自動關閉...)")
    time.sleep(300) 

    spark.stop()

if __name__ == "__main__":
    main()