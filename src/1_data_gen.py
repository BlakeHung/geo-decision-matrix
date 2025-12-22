import pandas as pd
import numpy as np
import random
import os

# 確保 data 資料夾存在
os.makedirs('data', exist_ok=True)

TOTAL_RECORDS = 1000000
CITIES = ['Taipei', 'NewTaipei', 'Taichung', 'Kaohsiung', 'Changhua', 'Hualien']

# 模擬誤差設定: (城市, 發生誤差機率, 平均誤差公尺數)
# 故事設定：都會區很準，但彰化巷弄與花蓮山區誤差大
ERROR_PROFILES = {
    'Taipei': (0.05, 10),
    'NewTaipei': (0.05, 15),
    'Taichung': (0.10, 20),
    'Kaohsiung': (0.15, 25),
    'Changhua': (0.35, 180),  # 35% 機率誤差 180m
    'Hualien': (0.60, 550)    # 60% 機率誤差 550m
}

print(f"🚀 正在生成 {TOTAL_RECORDS} 筆模擬地圖數據...")

data = []
for i in range(TOTAL_RECORDS):
    city = random.choice(CITIES)
    # 基準點 (Google Maps)
    base_lat, base_lng = 24.0 + random.random(), 121.0 + random.random()
    
    # 對照點 (Map8)
    prob, avg_error = ERROR_PROFILES[city]
    
    if random.random() < prob:
        # 模擬偏差 (0.00001度 約 1公尺)
        # 隨機產生一個偏差方向
        offset = (avg_error / 111000) * random.uniform(0.5, 1.5)
        map8_lat = base_lat + offset
        map8_lng = base_lng + offset
    else:
        map8_lat, map8_lng = base_lat, base_lng
        
    data.append([city, base_lat, base_lng, map8_lat, map8_lng])

df = pd.DataFrame(data, columns=['city', 'g_lat', 'g_lng', 'm_lat', 'm_lng'])
csv_path = 'data/raw_addresses.csv'
df.to_csv(csv_path, index=False)
print(f"✅ 模擬數據已生成：{csv_path} (Size: {os.path.getsize(csv_path)/1024/1024:.2f} MB)")