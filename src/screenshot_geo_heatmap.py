#!/usr/bin/env python3
"""
🗺️ 地理空間風險視覺化生成器 (第三部曲截圖 #7)

功能：
1. 讀取 gps_tracks.csv 的真實經緯度
2. 標記異常點（座標 0.0, 0.0 = 瞬間移動到非洲外海）
3. 按城市分組，使用戰情室風格地圖
4. 生成高質量截圖素材

用途：展示「全量數據」如何捕捉到邊緣案例
"""

import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import os

# ==========================================
# 配置
# ==========================================
INPUT_FILE = 'data/gps_tracks.csv'
OUTPUT_MAP = 'outputs/geo_risk_heatmap.html'

# 顏色配置（呼應 doc/tech.md 的設計）
COLOR_TAIPEI = '#3498db'   # 藍色：台北正常區域
COLOR_HSINCHU = '#e74c3c'  # 紅色：新竹高風險區
COLOR_ANOMALY = '#ff00ff'  # 紫紅色：異常點（瞬間移動）

# ==========================================
# 主程式
# ==========================================
def create_risk_map():
    print("🗺️ [截圖 #7] 正在生成地理空間風險視覺化...")

    # 1. 檢查檔案
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到檔案: {INPUT_FILE}")
        print("   請先執行 'python src/1_data_gen.py' 來生成 GPS 數據")
        return

    # 2. 讀取數據
    print(f"📊 正在載入 GPS 軌跡數據...")
    df = pd.read_csv(INPUT_FILE)
    print(f"✅ 已載入 {len(df):,} 筆數據")

    # 3. 分類數據
    # 異常點：座標 (0.0, 0.0) = 「瞬間移動到非洲外海」的災難性錯誤
    df_anomaly = df[(df['latitude'] == 0.0) & (df['longitude'] == 0.0)]

    # 正常點：過濾掉異常座標
    df_normal = df[~((df['latitude'] == 0.0) & (df['longitude'] == 0.0))]

    # 按城市分組
    df_taipei = df_normal[df_normal['city'] == 'Taipei']
    df_hsinchu = df_normal[df_normal['city'] == 'Hsinchu']

    print(f"\n📍 數據統計：")
    print(f"  - 台北正常點: {len(df_taipei):,} 筆")
    print(f"  - 新竹正常點: {len(df_hsinchu):,} 筆")
    print(f"  - 異常點 (0,0): {len(df_anomaly):,} 筆 ⚠️")

    # 4. 創建地圖（使用暗色戰情室風格）
    # 中心點：台灣中心（台北和新竹之間）
    map_center = [24.8, 121.0]
    m = folium.Map(
        location=map_center,
        zoom_start=8,
        tiles='CartoDB dark_matter'  # 戰情室風格
    )

    # 5. 繪製台北軌跡（藍色 - 正常營運）
    print("🎨 正在繪製台北軌跡...")
    taipei_coords = df_taipei[['latitude', 'longitude']].values.tolist()

    # 使用 HeatMap 展示密度（但用藍色系）
    if len(taipei_coords) > 0:
        # 取樣以提升性能（每10筆取1筆）
        taipei_sample = taipei_coords[::10]
        for coord in taipei_sample[:500]:  # 最多500點
            folium.CircleMarker(
                location=coord,
                radius=2,
                color=COLOR_TAIPEI,
                fill=True,
                fill_color=COLOR_TAIPEI,
                fill_opacity=0.6,
                popup=f"台北正常點"
            ).add_to(m)

    # 6. 繪製新竹軌跡（紅色 - 高風險區）
    print("🎨 正在繪製新竹軌跡...")
    hsinchu_coords = df_hsinchu[['latitude', 'longitude']].values.tolist()

    if len(hsinchu_coords) > 0:
        hsinchu_sample = hsinchu_coords[::10]
        for coord in hsinchu_sample[:500]:
            folium.CircleMarker(
                location=coord,
                radius=2,
                color=COLOR_HSINCHU,
                fill=True,
                fill_color=COLOR_HSINCHU,
                fill_opacity=0.6,
                popup=f"新竹高風險區"
            ).add_to(m)

    # 7. 標記異常點（紫紅色 - 災難性錯誤）
    if len(df_anomaly) > 0:
        print(f"⚠️ 正在標記 {len(df_anomaly)} 個異常點（瞬間移動）...")

        # 異常點應該在非洲外海 (0, 0)，但地圖上我們用特殊圖標標示
        folium.Marker(
            location=[0, 0],
            popup=folium.Popup(
                f"""
                <div style="font-family: Arial; width: 250px; color: #000;">
                    <h3 style="color: {COLOR_ANOMALY};">🚨 災難性錯誤</h3>
                    <hr>
                    <b>異常點數量:</b> {len(df_anomaly):,} 筆<br>
                    <b>原因:</b> GPS 定位失敗導致座標歸零<br>
                    <b>影響:</b> 若未被偵測，會誤判為「瞬間移動」<br>
                    <hr>
                    <b style="color: red;">這就是倖存者偏差的盲點！</b>
                </div>
                """,
                max_width=300
            ),
            icon=folium.Icon(color='purple', icon='exclamation-triangle', prefix='fa')
        ).add_to(m)

    # 8. 添加圖例（HTML 疊加層）
    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 280px;
        background-color: rgba(0, 0, 0, 0.8);
        border: 2px solid #fff;
        border-radius: 5px;
        z-index: 9999;
        font-family: Arial;
        color: #fff;
        padding: 15px;
    ">
        <h4 style="margin: 0 0 10px 0; color: #fff;">🗺️ Geo Decision Matrix</h4>
        <hr style="margin: 10px 0; border-color: #555;">
        <p style="margin: 5px 0;">
            <span style="color: {COLOR_TAIPEI}; font-size: 20px;">●</span>
            台北正常營運 ({len(df_taipei):,} 筆)
        </p>
        <p style="margin: 5px 0;">
            <span style="color: {COLOR_HSINCHU}; font-size: 20px;">●</span>
            新竹高風險區 ({len(df_hsinchu):,} 筆)
        </p>
        <p style="margin: 5px 0;">
            <span style="color: {COLOR_ANOMALY}; font-size: 20px;">⚠</span>
            異常點 (0,0) ({len(df_anomaly):,} 筆)
        </p>
        <hr style="margin: 10px 0; border-color: #555;">
        <p style="margin: 5px 0; font-size: 11px; color: #aaa;">
            ⚡ Powered by RAPIDS + RTX 3090
        </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # 9. 添加標題
    title_html = """
    <div style="
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        background-color: rgba(0, 0, 0, 0.8);
        border: 2px solid #3498db;
        border-radius: 5px;
        padding: 10px 20px;
        color: #fff;
        font-family: Arial;
        font-size: 18px;
        font-weight: bold;
    ">
        🚀 第三部曲：地理空間風險熱區 | 全量數據 vs 抽樣盲點
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # 10. 儲存地圖
    os.makedirs(os.path.dirname(OUTPUT_MAP), exist_ok=True)
    m.save(OUTPUT_MAP)

    print(f"\n✨ 地圖已生成！")
    print(f"📁 檔案位置: {OUTPUT_MAP}")
    print(f"👉 請用瀏覽器開啟並截圖")
    print(f"\n💡 截圖重點：")
    print(f"   1. 台北（藍）vs 新竹（紅）的軌跡分布")
    print(f"   2. 紫色異常點標記（非洲外海 0,0）")
    print(f"   3. 圖例顯示數據量對比")

    # 嘗試自動開啟（WSL 環境）
    try:
        os.system(f"explorer.exe {OUTPUT_MAP}")
    except:
        pass

if __name__ == "__main__":
    create_risk_map()
