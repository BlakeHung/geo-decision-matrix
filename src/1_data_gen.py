import csv
import random
import time
from datetime import datetime, timedelta

# 設定產出檔案
OUTPUT_FILE = 'data/gps_tracks.csv'
# 關鍵修改：將資料量放大到 50 萬筆 (足以讓 Node.js 崩潰)
NUM_RECORDS = 500000 

def generate_data():
    print(f"正在生成 {NUM_RECORDS} 筆測試數據 (這需要一點時間)...")
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # 寫入 Header
        writer.writerow(['user_id', 'timestamp', 'latitude', 'longitude', 'city'])
        
        start_time = datetime.now()
        
        # 模擬兩個使用者的起點
        users = [
            {'id': 'user_a_taipei', 'lat': 25.0330, 'lon': 121.5654, 'city': 'Taipei'}, # 台北101
            {'id': 'user_c_hsinchu', 'lat': 24.8138, 'lon': 120.9675, 'city': 'Hsinchu'} # 新竹市政府
        ]
        
        for i in range(NUM_RECORDS):
            # 隨機選一個使用者
            user = random.choice(users)
            
            # 模擬時間推進
            current_time = start_time + timedelta(seconds=i)
            timestamp = int(current_time.timestamp())
            
            # --- 製造髒數據邏輯 ---
            
            # 1. 正常移動 (加一點隨機偏移)
            lat_offset = random.uniform(-0.0001, 0.0001)
            lon_offset = random.uniform(-0.0001, 0.0001)
            
            # 2. 災難場景：每 1000 筆製造一次「完全重疊」 (Distance = 0)
            if i % 1000 == 0:
                lat_offset = 0
                lon_offset = 0
            
            # 3. 災難場景：每 5000 筆製造一次「瞬間移動」 (漂移到非洲外海)
            if i % 5000 == 0:
                user['lat'] = 0.0
                user['lon'] = 0.0
            else:
                user['lat'] += lat_offset
                user['lon'] += lon_offset
            
            # 寫入 CSV
            writer.writerow([
                user['id'], 
                timestamp, 
                round(user['lat'], 6), 
                round(user['lon'], 6), 
                user['city']
            ])
            
            # 進度條 (每 5萬筆印一次，不然螢幕會被洗版)
            if i % 50000 == 0:
                print(f"已生成 {i} 筆...")

    print(f"\n>>> 檔案生成完畢：{OUTPUT_FILE}")
    print(f">>> 總筆數：{NUM_RECORDS}")

if __name__ == "__main__":
    generate_data()