#!/usr/bin/env python3
"""
📊 倖存者偏差對比圖生成器 (第三部曲截圖 #8)

功能：
1. 左側：模擬「舊系統抽樣」（稀疏，漏掉邊緣案例）
2. 右側：「新系統全量」（覆蓋完整，抓出異常）
3. 視覺化解釋為什麼「簡單的請求都成功了，但複雜運算被丟棄」

用途：一圖勝千言，展示倖存者偏差的本質
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os

# ==========================================
# 配置
# ==========================================
OUTPUT_FILE = 'outputs/survivorship_bias_comparison.png'

# 中文字型設定（如果有繁體中文字型）
plt.rcParams['font.family'] = ['Microsoft JhengHei', 'DejaVu Sans', 'Arial']
plt.rcParams['font.size'] = 11

# ==========================================
# 主程式
# ==========================================
def generate_comparison_chart():
    print("📊 [截圖 #8] 正在生成倖存者偏差對比圖...")

    # 創建畫布：1行2列
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.patch.set_facecolor('#1a1a1a')  # 暗色背景（戰情室風格）

    # ==========================================
    # 左圖：舊系統（Node.js 抽樣）
    # ==========================================
    ax1.set_facecolor('#2c2c2c')
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    ax1.set_aspect('equal')

    # 標題
    ax1.set_title(
        '🔴 Phase 1: Node.js 單機腳本（倖存者偏差）',
        fontsize=16,
        fontweight='bold',
        color='#e74c3c',
        pad=20
    )

    # 模擬抽樣點（只有「簡單請求」成功回傳）
    np.random.seed(42)

    # 正常成功的點（80個，集中在中心區域）
    success_x = np.random.normal(50, 15, 80)
    success_y = np.random.normal(50, 15, 80)

    # 確保點在畫布內
    success_x = np.clip(success_x, 5, 95)
    success_y = np.clip(success_y, 5, 95)

    # 繪製成功點（綠色）
    ax1.scatter(
        success_x, success_y,
        s=100,
        c='#2ecc71',
        alpha=0.7,
        edgecolors='white',
        linewidths=1,
        label='成功回應 (80 筆)'
    )

    # 失敗但「不可見」的點（灰色虛影，代表被丟棄）
    # 這些是「複雜運算」導致 OOM/Timeout 的請求
    failed_x = [10, 15, 12, 88, 92, 85, 20, 25, 75, 80, 10, 90, 15, 85]
    failed_y = [10, 8, 15, 12, 8, 15, 85, 90, 88, 92, 90, 85, 12, 10]

    ax1.scatter(
        failed_x, failed_y,
        s=200,
        c='#95a5a6',
        alpha=0.3,
        marker='x',
        linewidths=3,
        label='失敗但未記錄 (14 筆) ⚠️'
    )

    # 標記「盲點區域」（邊緣）
    # 上邊緣
    rect_top = patches.Rectangle(
        (0, 85), 100, 15,
        linewidth=2,
        edgecolor='#e74c3c',
        facecolor='#e74c3c',
        alpha=0.2,
        linestyle='--',
        label='監控盲點區域'
    )
    ax1.add_patch(rect_top)

    # 下邊緣
    rect_bottom = patches.Rectangle(
        (0, 0), 100, 15,
        linewidth=2,
        edgecolor='#e74c3c',
        facecolor='#e74c3c',
        alpha=0.2,
        linestyle='--'
    )
    ax1.add_patch(rect_bottom)

    # 左邊緣
    rect_left = patches.Rectangle(
        (0, 15), 15, 70,
        linewidth=2,
        edgecolor='#e74c3c',
        facecolor='#e74c3c',
        alpha=0.2,
        linestyle='--'
    )
    ax1.add_patch(rect_left)

    # 右邊緣
    rect_right = patches.Rectangle(
        (85, 15), 15, 70,
        linewidth=2,
        edgecolor='#e74c3c',
        facecolor='#e74c3c',
        alpha=0.2,
        linestyle='--'
    )
    ax1.add_patch(rect_right)

    # 添加文字說明
    ax1.text(
        50, 5,
        '⚠️ 監控系統顯示：成功率 85%\n（但複雜運算直接 Timeout，未被記錄）',
        ha='center',
        va='center',
        fontsize=11,
        color='#f39c12',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#34495e', alpha=0.8)
    )

    ax1.legend(loc='upper left', framealpha=0.9, facecolor='#2c2c2c', edgecolor='white')
    ax1.axis('off')

    # ==========================================
    # 右圖：新系統（RAPIDS GPU 全量）
    # ==========================================
    ax2.set_facecolor('#2c2c2c')
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.set_aspect('equal')

    # 標題
    ax2.set_title(
        '🟢 Phase 3: RAPIDS GPU 加速（全量覆蓋）',
        fontsize=16,
        fontweight='bold',
        color='#2ecc71',
        pad=20
    )

    # 全量數據（成功 + 邊緣案例）
    # 成功點（相同的 80 個）
    ax2.scatter(
        success_x, success_y,
        s=100,
        c='#2ecc71',
        alpha=0.7,
        edgecolors='white',
        linewidths=1,
        label='正常處理 (80 筆)'
    )

    # 之前失敗的點，現在「被捕捉到」了（紅色高亮）
    ax2.scatter(
        failed_x, failed_y,
        s=200,
        c='#e74c3c',
        alpha=0.9,
        edgecolors='white',
        linewidths=2,
        marker='o',
        label='高風險案例 (14 筆) 🚨'
    )

    # 標記「全覆蓋區域」（綠色邊框）
    full_coverage = patches.Rectangle(
        (0, 0), 100, 100,
        linewidth=3,
        edgecolor='#2ecc71',
        facecolor='none',
        linestyle='-',
        label='全量數據覆蓋'
    )
    ax2.add_patch(full_coverage)

    # 添加文字說明
    ax2.text(
        50, 5,
        '✅ GPU 加速：0.51 秒處理 50 萬筆\n（無遺漏，邊緣案例全部捕捉）',
        ha='center',
        va='center',
        fontsize=11,
        color='#2ecc71',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#34495e', alpha=0.8)
    )

    ax2.legend(loc='upper left', framealpha=0.9, facecolor='#2c2c2c', edgecolor='white')
    ax2.axis('off')

    # ==========================================
    # 整體標題
    # ==========================================
    fig.suptitle(
        '🎯 倖存者偏差：為什麼「監控看起來健康，但系統在漏接關鍵數據」',
        fontsize=18,
        fontweight='bold',
        color='white',
        y=0.98
    )

    # 添加副標題（解釋）
    fig.text(
        0.5, 0.02,
        '📌 關鍵洞察：Node.js 單機腳本只能處理「簡單請求」，複雜運算導致 OOM/Timeout 被丟棄。'
        '\nGPU 全量處理確保「邊緣案例」（高風險區域）被正確識別，避免誤判。',
        ha='center',
        fontsize=11,
        color='#95a5a6'
    )

    # 儲存圖片（高解析度）
    plt.tight_layout(rect=[0, 0.05, 1, 0.96])

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    plt.savefig(
        OUTPUT_FILE,
        dpi=300,
        facecolor='#1a1a1a',
        edgecolor='none',
        bbox_inches='tight'
    )

    print(f"\n✨ 對比圖已生成！")
    print(f"📁 檔案位置: {OUTPUT_FILE}")
    print(f"👉 請用圖片檢視器開啟並截圖")
    print(f"\n💡 截圖重點：")
    print(f"   1. 左側：灰色 X 標記代表「失敗但不可見」的請求")
    print(f"   2. 右側：紅色圓圈標記代表「被成功捕捉」的高風險案例")
    print(f"   3. 對比說明倖存者偏差如何導致誤判")

    # 顯示圖表（如果在圖形介面環境）
    # plt.show()

if __name__ == "__main__":
    generate_comparison_chart()
