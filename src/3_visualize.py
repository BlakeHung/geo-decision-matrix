import pandas as pd
import folium

# 設定檔案路徑
INPUT_FILE = 'data/gps_tracks.csv'
OUTPUT_MAP = 'data/trajectory_map.html'

def generate_map():
    print("正在讀取數據...")
    df = pd.read_csv(INPUT_FILE)

    # 建立地圖，中心點設在台灣
    m = folium.Map(location=[24.9, 121.3], zoom_start=10)

    # --- 繪製 台北 User A (藍色) ---
    user_a = df[df['user_id'] == 'user_a_taipei']
    if not user_a.empty:
        points_a = user_a[['latitude', 'longitude']].values.tolist()
        folium.PolyLine(points_a, color="blue", weight=5, opacity=0.7, tooltip="Taipei User").add_to(m)
        # 起點標記
        folium.Marker(points_a[0], popup="User A Start", icon=folium.Icon(color='blue')).add_to(m)
        print(f"已繪製台北軌跡：{len(points_a)} 個點")

    # --- 繪製 新竹 User C (紅色 - 災難組) ---
    user_c = df[df['user_id'] == 'user_c_hsinchu']
    if not user_c.empty:
        points_c = user_c[['latitude', 'longitude']].values.tolist()
        folium.PolyLine(points_c, color="red", weight=5, opacity=0.7, tooltip="Hsinchu User").add_to(m)
        
        # 特別標記：那個「卡住」的黑洞點 (取第 15 個點左右)
        # 這是我們在生成數據時故意設定重疊的地方
        stuck_point = points_c[15]
        folium.Marker(
            stuck_point, 
            popup="<b>新竹重劃區黑洞</b><br>座標重疊發生地", 
            icon=folium.Icon(color='red', icon='warning', prefix='fa')
        ).add_to(m)
        
        print(f"已繪製新竹軌跡：{len(points_c)} 個點")

    # 存檔
    m.save(OUTPUT_MAP)
    print(f"\n地圖已產生！請在 Windows 檔案總管開啟以下路徑查看：")
    print(f"{OUTPUT_MAP}")

if __name__ == "__main__":
    generate_map()