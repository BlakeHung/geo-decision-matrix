import folium
import pandas as pd
import json
import os
import random

# 設定檔案路徑
INPUT_FILE = 'data/clustered_result.json'
OUTPUT_MAP = 'decision_matrix_map.html'

def generate_fake_coordinates(row):
    """
    如果資料中沒有經緯度，我們就在台北市中心隨機生成。
    中心點：台北 101 (25.0330, 121.5654)
    """
    # 隨機偏移量 (約 5公里範圍)
    lat_offset = random.uniform(-0.05, 0.05)
    lon_offset = random.uniform(-0.05, 0.05)
    return 25.0330 + lat_offset, 121.5654 + lon_offset

def create_map():
    print("🗺️ [Step 7] 初始化地圖繪製程序...")

    # 1. 檢查輸入檔案
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到檔案: {INPUT_FILE}")
        print("   請先執行 'python src/6_ai_clustering.py' 來生成數據。")
        return

    # 2. 讀取數據
    try:
        df = pd.read_json(INPUT_FILE)
        print(f"📊 已載入 {len(df)} 筆分群數據。")
    except Exception as e:
        print(f"❌ 讀取 JSON 失敗: {e}")
        return

    if len(df) == 0:
        print("❌ 數據為空，無法繪圖。")
        return

    # 3. 初始化地圖 (以台北為中心)
    # 使用 CartoDB dark_matter 風格，看起來比較像「戰情室」
    m = folium.Map(location=[25.0330, 121.5654], zoom_start=12, tiles='CartoDB dark_matter')

    # 定義顏色映射 (配合 Step 6 的 Label)
    color_map = {
        "Risk: Congested (紅色警戒)": "#ff4d4d", # 紅
        "Good: Efficient (綠色暢通)": "#2ecc71", # 綠
        "Normal: Average (黃色觀察)": "#f1c40f"  # 黃
    }

    print("🎨 正在將數據點標記在地圖上...")
    
    # 為了效能，如果數據太多，只畫前 500 筆
    max_points = 500
    if len(df) > max_points:
        print(f"⚠️ 數據過多，僅繪製前 {max_points} 筆以確保瀏覽器流暢度...")
        plot_df = df.head(max_points)
    else:
        plot_df = df

    count = 0
    for _, row in plot_df.iterrows():
        # 處理座標 (如果沒有 lat/lon，就造假)
        if 'lat' in row and 'lon' in row:
            lat, lon = row['lat'], row['lon']
        else:
            lat, lon = generate_fake_coordinates(row)
        
        # 取得顏色
        label = row.get('label', 'Unknown')
        color = color_map.get(label, "#gray")
        
        # 建立 Popup 內容 (HTML)
        # 這裡會顯示 GenAI 的建議 (如果有的話)
        ai_advice = row.get('ai_advice', 'Analysis pending...')
        
        popup_html = f"""
        <div style="font-family: Arial; width: 220px;">
            <h4 style="margin: 0; color: {color};">{label}</h4>
            <hr style="margin: 5px 0;">
            <b>Driver:</b> {row.get('driver_id', 'N/A')}<br>
            <b>Speed:</b> {row.get('average_speed', 0):.1f} km/h<br>
            <b>Stuck:</b> {row.get('stuck_count', 0)} times<br>
            <hr style="margin: 5px 0;">
            <b style="color: #666;">🤖 AI Advice:</b><br>
            <i style="font-size: 12px;">{ai_advice}</i>
        </div>
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7
        ).add_to(m)
        count += 1

    # 4. 存檔
    m.save(OUTPUT_MAP)
    print(f"✨ 成功繪製 {count} 個點！")
    
    # 這裡教你怎麼在 WSL 裡打開檔案
    print(f"🚀 地圖已生成: {OUTPUT_MAP}")
    print("👉 請在 Windows 檔案總管中找到此檔案並雙擊打開，或使用以下指令預覽 (如果你有安裝 browser tool):")
    print(f"   explorer.exe {OUTPUT_MAP}")

if __name__ == "__main__":
    create_map()