from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
import math

# --- 核心邏輯：Haversine 公式 (含防禦機制) ---
def calculate_haversine(lat1, lon1, lat2, lon2):
    """
    計算兩點間的 Haversine 距離 (公里)
    """
    # 1. 基礎防禦：過濾空值
    if None in [lat1, lon1, lat2, lon2]:
        return 0.0

    R = 6371  # 地球半徑 (km)
    
    # 將經緯度轉為弧度
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    
    # 2. 進階防禦 (High C 潔癖重點)：
    # 當兩點極度接近或重疊時，浮點數誤差可能導致 a 略大於 1 (如 1.00000000002)
    # 這會導致 sqrt(1-a) 出現虛數或定義域錯誤，進而產生 NaN。
    # 所以我們必須限制 a 的範圍在 [0, 1] 之間。
    a = min(1.0, max(0.0, a))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance

def main():
    # 啟動 Spark (Local Mode)
    spark = SparkSession.builder \
        .appName("GeoDecisionMatrix") \
        .master("local[*]") \
        .getOrCreate()

    # 降低 Log 雜訊
    spark.sparkContext.setLogLevel("ERROR")

    print(">>> [Spark] 正在讀取 GPS 軌跡數據...")
    try:
        df = spark.read.csv("data/gps_tracks.csv", header=True, inferSchema=True)
    except Exception as e:
        print(f"!!! 讀取檔案失敗: {e}")
        return

    # 定義 Window：依照 User 分組，並按時間排序
    window_spec = Window.partitionBy("user_id").orderBy("timestamp")

    # 取得「上一筆」資料 (Lag)
    df_lag = df.withColumn("prev_lat", F.lag("latitude").over(window_spec)) \
               .withColumn("prev_lon", F.lag("longitude").over(window_spec))

    # 註冊 UDF
    haversine_udf = F.udf(calculate_haversine, DoubleType())

    print(">>> [Spark] 正在執行分散式運算 (模擬中)...")
    
    # 計算距離
    result_df = df_lag.withColumn("distance_km", 
        haversine_udf("prev_lat", "prev_lon", "latitude", "longitude")
    )

    # 填補第一筆資料的 Null 為 0
    result_df = result_df.na.fill(0.0, subset=["distance_km"])

    print("\n========= 分析報告 =========")
    
    print("\n[台北 User A] 正常移動數據：")
    result_df.filter(F.col("user_id") == "user_a_taipei") \
             .select("timestamp", "latitude", "distance_km") \
             .show(5, truncate=False)

    print("\n[新竹 User C] 災難數據檢測 (注意 distance_km 是否成功算出 0)：")
    # 這裡就是驗證我們程式碼有沒有被「重疊點」擊潰的地方
    hsinchu_disaster = result_df.filter(F.col("user_id") == "user_c_hsinchu")
    hsinchu_disaster.select("timestamp", "latitude", "distance_km").show(15, truncate=False)

    # 最終檢查
    nan_count = result_df.filter(F.isnan(F.col("distance_km"))).count()
    print(f"\n系統強健性檢查：發現 {nan_count} 筆 NaN 異常值")
    
    if nan_count == 0:
        print(">>> 測試通過：系統成功抵抗了新竹重劃區的髒數據攻擊！")
    else:
        print(">>> 測試失敗：NaN 滲透進系統了。")

    spark.stop()

if __name__ == "__main__":
    main()