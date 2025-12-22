import csv
import random
import time
import os

# 設定輸出路徑
OUTPUT_DIR = 'data'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'gps_tracks.csv')

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_data():
    print("正在製造「定向災難」數據中 (不依賴 Pandas)...")
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['user_id', 'timestamp', 'latitude', 'longitude', 'city']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # ==========================================
        # 劇本一：台北 (Taipei) - 正常數據
        # ==========================================
        base_lat_tp = 25.0780
        base_lon_tp = 121.5750
        current_time = int(time.time())
        
        for i in range(50):
            base_lat_tp += random.uniform(-0.0001, 0.0001)
            base_lon_tp += random.uniform(-0.0001, 0.0001)
            writer.writerow({
                'user_id': 'user_a_taipei',
                'timestamp': current_time + i * 10,
                'latitude': round(base_lat_tp, 6),
                'longitude': round(base_lon_tp, 6),
                'city': 'Taipei'
            })

        # ==========================================
        # 劇本二：新竹 (Hsinchu) - 災難數據 (NaN 製造機)
        # ==========================================
        base_lat_hc = 24.8050
        base_lon_hc = 120.9750
        
        for i in range(50):
            # 關鍵點：製造完全重疊的座標，引發距離計算的分母為 0 或 acos 錯誤
            if 10 < i < 20: 
                pass # 經緯度完全不變
            elif i == 30:
                base_lat_hc += 0.5 # 瞬間移動
            elif i == 31:
                base_lat_hc -= 0.5
            else:
                base_lat_hc += random.uniform(-0.0002, 0.0002)
                base_lon_hc += random.uniform(-0.0002, 0.0002)

            writer.writerow({
                'user_id': 'user_c_hsinchu',
                'timestamp': current_time + i * 10,
                'latitude': round(base_lat_hc, 6),
                'longitude': round(base_lon_hc, 6),
                'city': 'Hsinchu'
            })

    print(f"數據生成完畢！請檢查: {OUTPUT_FILE}")

if __name__ == '__main__':
    generate_data()