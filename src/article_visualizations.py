#!/usr/bin/env python3
"""
🎨 技術文章視覺化生成器（第三部曲 3.1 文章專用）

功能：生成 doc/3.1article_visual.md 中需要的 3 張技術圖表
1. The Topology Bottleneck - NVLink vs PCIe 頻寬對比
2. The Hybrid Architecture - CPU/GPU 混合架構流程圖
3. The Benchmark - 執行時間對比長條圖

輸出：outputs/article_*.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# 中文字型設定
plt.rcParams['font.family'] = ['Microsoft JhengHei', 'DejaVu Sans', 'Arial']
plt.rcParams['font.size'] = 11

OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# 圖表 #4：The Topology Bottleneck（硬體拓撲對比）
# ============================================================================
def generate_topology_comparison():
    """
    對比圖：左側是「理想世界」（NVLink），右側是「現實」（PCIe through CPU）
    """
    print("🎨 [圖表 #4] 正在生成 Topology Bottleneck 對比圖...")

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, 8))
    fig.patch.set_facecolor('#1a1a1a')

    # ==================== 左側：理想世界（NVLink） ====================
    ax_left.set_facecolor('#2c2c2c')
    ax_left.set_xlim(0, 10)
    ax_left.set_ylim(0, 10)
    ax_left.axis('off')
    ax_left.set_title(
        '✨ Ideal World: NVLink 直連',
        fontsize=16,
        fontweight='bold',
        color='#2ecc71',
        pad=20
    )

    # GPU 0
    gpu0_left = FancyBboxPatch(
        (1, 6), 3, 2,
        boxstyle="round,pad=0.1",
        edgecolor='#3498db',
        facecolor='#34495e',
        linewidth=3
    )
    ax_left.add_patch(gpu0_left)
    ax_left.text(2.5, 7, 'GPU 0\nRTX 3090', ha='center', va='center',
                fontsize=12, fontweight='bold', color='white')

    # GPU 1
    gpu1_left = FancyBboxPatch(
        (6, 6), 3, 2,
        boxstyle="round,pad=0.1",
        edgecolor='#3498db',
        facecolor='#34495e',
        linewidth=3
    )
    ax_left.add_patch(gpu1_left)
    ax_left.text(7.5, 7, 'GPU 1\nRTX 3090', ha='center', va='center',
                fontsize=12, fontweight='bold', color='white')

    # NVLink 連接（粗箭頭，雙向）
    arrow_nvlink_1 = FancyArrowPatch(
        (4, 7.5), (6, 7.5),
        arrowstyle='<->',
        color='#2ecc71',
        linewidth=8,
        mutation_scale=30
    )
    ax_left.add_patch(arrow_nvlink_1)

    arrow_nvlink_2 = FancyArrowPatch(
        (4, 6.5), (6, 6.5),
        arrowstyle='<->',
        color='#2ecc71',
        linewidth=8,
        mutation_scale=30
    )
    ax_left.add_patch(arrow_nvlink_2)

    # 標註頻寬
    ax_left.text(5, 8.5, '🚀 NVLink Bridge', ha='center',
                fontsize=13, fontweight='bold', color='#2ecc71')
    ax_left.text(5, 5.5, '900 GB/s', ha='center',
                fontsize=14, fontweight='bold', color='#2ecc71',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#27ae60', alpha=0.8))

    # 說明文字
    ax_left.text(5, 2, '✅ GPU 間直接通訊\n✅ 超高頻寬\n✅ 延遲極低',
                ha='center', va='center', fontsize=11, color='#95a5a6',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#34495e', alpha=0.8))

    # ==================== 右側：現實（PCIe through CPU） ====================
    ax_right.set_facecolor('#2c2c2c')
    ax_right.set_xlim(0, 10)
    ax_right.set_ylim(0, 10)
    ax_right.axis('off')
    ax_right.set_title(
        '⚠️ My Reality: PCIe 繞行',
        fontsize=16,
        fontweight='bold',
        color='#e74c3c',
        pad=20
    )

    # GPU 0 (x16 lane)
    gpu0_right = FancyBboxPatch(
        (0.5, 7), 2, 1.5,
        boxstyle="round,pad=0.1",
        edgecolor='#3498db',
        facecolor='#34495e',
        linewidth=3
    )
    ax_right.add_patch(gpu0_right)
    ax_right.text(1.5, 7.75, 'GPU 0\n(x16)', ha='center', va='center',
                 fontsize=11, fontweight='bold', color='white')

    # GPU 1 (x4 lane)
    gpu1_right = FancyBboxPatch(
        (7.5, 7), 2, 1.5,
        boxstyle="round,pad=0.1",
        edgecolor='#e67e22',
        facecolor='#34495e',
        linewidth=3
    )
    ax_right.add_patch(gpu1_right)
    ax_right.text(8.5, 7.75, 'GPU 1\n(x4)', ha='center', va='center',
                 fontsize=11, fontweight='bold', color='white')

    # CPU RAM（中間瓶頸）
    cpu_ram = FancyBboxPatch(
        (3.5, 4), 3, 1.5,
        boxstyle="round,pad=0.1",
        edgecolor='#f39c12',
        facecolor='#34495e',
        linewidth=3
    )
    ax_right.add_patch(cpu_ram)
    ax_right.text(5, 4.75, 'CPU + RAM\n(繞行點)', ha='center', va='center',
                 fontsize=11, fontweight='bold', color='#f39c12')

    # PCIe 路徑（細箭頭，曲折）
    # GPU 0 -> CPU
    arrow1 = FancyArrowPatch(
        (2.5, 7.5), (4, 5.5),
        arrowstyle='->',
        color='#e74c3c',
        linewidth=3,
        mutation_scale=20,
        linestyle='--'
    )
    ax_right.add_patch(arrow1)
    ax_right.text(2.8, 6.3, 'PCIe x16\n~12 GB/s', fontsize=9, color='#e74c3c')

    # CPU -> GPU 1
    arrow2 = FancyArrowPatch(
        (6, 5), (7.5, 7.5),
        arrowstyle='->',
        color='#e67e22',
        linewidth=2,
        mutation_scale=20,
        linestyle='--'
    )
    ax_right.add_patch(arrow2)
    ax_right.text(6.8, 6.3, 'PCIe x4\n~3 GB/s', fontsize=9, color='#e67e22')

    # 標註瓶頸
    ax_right.text(5, 2.5, '❌ 需經過 CPU RAM\n❌ 頻寬受限 (75x 慢!)\n❌ 延遲高',
                 ha='center', va='center', fontsize=11, color='#e74c3c',
                 bbox=dict(boxstyle='round,pad=0.8', facecolor='#c0392b', alpha=0.7))

    # 總標題
    fig.suptitle(
        '🔧 硬體『頻寬牆』的物理限制：為什麼雙卡不如單卡？',
        fontsize=18,
        fontweight='bold',
        color='white',
        y=0.98
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    output_path = os.path.join(OUTPUT_DIR, 'article_topology_bottleneck.png')
    plt.savefig(output_path, dpi=300, facecolor='#1a1a1a', bbox_inches='tight')
    print(f"✅ 已生成：{output_path}")
    plt.close()


# ============================================================================
# 圖表 #5：The Hybrid Architecture（混合架構流程圖）
# ============================================================================
def generate_hybrid_architecture():
    """
    Data Flow：Raw Data -> Spark/CPU (Clean) -> Parquet -> RAPIDS/GPU (ML) -> Result
    """
    print("🎨 [圖表 #5] 正在生成 Hybrid Architecture 流程圖...")

    fig, ax = plt.subplots(figsize=(16, 6))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#2c2c2c')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Stage 0: Raw Data
    stage0 = FancyBboxPatch(
        (0.5, 2), 2, 2,
        boxstyle="round,pad=0.15",
        edgecolor='#95a5a6',
        facecolor='#34495e',
        linewidth=2
    )
    ax.add_patch(stage0)
    ax.text(1.5, 3, '📁 Raw Data\n500K GPS\nCSV', ha='center', va='center',
           fontsize=11, color='white')

    # Arrow 1
    arrow1 = FancyArrowPatch(
        (2.5, 3), (3.5, 3),
        arrowstyle='->,head_width=0.4,head_length=0.4',
        color='#3498db',
        linewidth=3
    )
    ax.add_patch(arrow1)

    # Stage 1: Spark/CPU (清洗)
    stage1 = FancyBboxPatch(
        (3.5, 1.5), 3, 3,
        boxstyle="round,pad=0.15",
        edgecolor='#e67e22',
        facecolor='#d35400',
        linewidth=3
    )
    ax.add_patch(stage1)
    ax.text(5, 3.8, '⚙️ Stage 1', ha='center', fontsize=10,
           fontweight='bold', color='white')
    ax.text(5, 3, 'Apache Spark\n(CPU 運算)', ha='center', va='center',
           fontsize=12, fontweight='bold', color='white')
    ax.text(5, 2.2, '• ETL 清洗\n• 距離計算\n• 聚合統計', ha='center',
           fontsize=9, color='#ecf0f1')

    # Arrow 2
    arrow2 = FancyArrowPatch(
        (6.5, 3), (7.5, 3),
        arrowstyle='->,head_width=0.4,head_length=0.4',
        color='#3498db',
        linewidth=3
    )
    ax.add_patch(arrow2)
    ax.text(7, 3.5, 'Parquet', ha='center', fontsize=9, color='#3498db',
           bbox=dict(boxstyle='round', facecolor='#2c3e50', alpha=0.8))

    # Stage 2: RAPIDS/GPU (分群)
    stage2 = FancyBboxPatch(
        (7.5, 1.5), 3, 3,
        boxstyle="round,pad=0.15",
        edgecolor='#2ecc71',
        facecolor='#27ae60',
        linewidth=3
    )
    ax.add_patch(stage2)
    ax.text(9, 3.8, '🚀 Stage 2', ha='center', fontsize=10,
           fontweight='bold', color='white')
    ax.text(9, 3, 'RAPIDS cuML\n(GPU 運算)', ha='center', va='center',
           fontsize=12, fontweight='bold', color='white')
    ax.text(9, 2.2, '• K-Means 聚類\n• 單卡專注\n• 0.51s 極速', ha='center',
           fontsize=9, color='#ecf0f1')

    # Arrow 3
    arrow3 = FancyArrowPatch(
        (10.5, 3), (11.5, 3),
        arrowstyle='->,head_width=0.4,head_length=0.4',
        color='#3498db',
        linewidth=3
    )
    ax.add_patch(arrow3)

    # Stage 3: API/Decision
    stage3 = FancyBboxPatch(
        (11.5, 2), 2, 2,
        boxstyle="round,pad=0.15",
        edgecolor='#9b59b6',
        facecolor='#8e44ad',
        linewidth=2
    )
    ax.add_patch(stage3)
    ax.text(12.5, 3, '📊 Decision\nMatrix\nAPI', ha='center', va='center',
           fontsize=11, color='white')

    # Arrow 4
    arrow4 = FancyArrowPatch(
        (13.5, 3), (14.5, 3),
        arrowstyle='->,head_width=0.4,head_length=0.4',
        color='#3498db',
        linewidth=3
    )
    ax.add_patch(arrow4)

    # Final Output
    stage4 = FancyBboxPatch(
        (14.5, 2.5), 1.2, 1,
        boxstyle="round,pad=0.1",
        edgecolor='#f39c12',
        facecolor='#f39c12',
        linewidth=2
    )
    ax.add_patch(stage4)
    ax.text(15.1, 3, '✅', ha='center', va='center', fontsize=20)

    # 標題
    ax.text(8, 5.3, '🔄 Hybrid Architecture: CPU 扛髒活，GPU 做精算',
           ha='center', fontsize=16, fontweight='bold', color='white')

    # 底部說明
    ax.text(8, 0.5, '💡 關鍵洞察：不強求多卡並行，讓每個硬體做最擅長的事',
           ha='center', fontsize=11, color='#95a5a6')

    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'article_hybrid_architecture.png')
    plt.savefig(output_path, dpi=300, facecolor='#1a1a1a', bbox_inches='tight')
    print(f"✅ 已生成：{output_path}")
    plt.close()


# ============================================================================
# 圖表 #6：The Benchmark（執行時間對比）
# ============================================================================
def generate_benchmark_comparison():
    """
    長條圖：Dask Multi-GPU (420s) vs Hybrid Single-GPU (150s)
    """
    print("🎨 [圖表 #6] 正在生成 Benchmark 對比長條圖...")

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#2c2c2c')

    # 數據
    methods = ['Dask Multi-GPU\n(分散式失敗)', 'Hybrid Single-GPU\n(混合架構)']
    times = [420, 150]
    colors = ['#e74c3c', '#2ecc71']

    # 繪製長條圖
    bars = ax.barh(methods, times, color=colors, edgecolor='white', linewidth=2)

    # 添加數值標籤
    for i, (bar, time) in enumerate(zip(bars, times)):
        width = bar.get_width()
        label_x = width + 10

        if i == 0:  # Dask Multi-GPU
            ax.text(label_x, bar.get_y() + bar.get_height()/2,
                   f'{time}s\n(Communication Overhead)',
                   va='center', fontsize=13, color='#e74c3c',
                   fontweight='bold')
        else:  # Hybrid Single-GPU
            ax.text(label_x, bar.get_y() + bar.get_height()/2,
                   f'{time}s\n(Compute Only)',
                   va='center', fontsize=13, color='#2ecc71',
                   fontweight='bold')

    # 坐標軸設定
    ax.set_xlabel('執行時間 (秒)', fontsize=14, color='white')
    ax.set_xlim(0, 500)
    ax.tick_params(colors='white', labelsize=12)
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 標題
    ax.set_title(
        '📊 成績單：多卡竟然比單卡還慢 2.8 倍！',
        fontsize=18,
        fontweight='bold',
        color='white',
        pad=20
    )

    # 添加對比箭頭
    ax.annotate(
        '',
        xy=(150, 0.5), xytext=(420, 0.5),
        arrowprops=dict(arrowstyle='<->', color='#f39c12', lw=3)
    )
    ax.text(285, 0.5, '快 2.8x', ha='center', va='bottom',
           fontsize=14, fontweight='bold', color='#f39c12',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='#34495e', alpha=0.9))

    # 底部說明
    fig.text(0.5, 0.02,
            '💡 結論：少即是多 (Less is More) - 單卡專注運算，避免通訊開銷',
            ha='center', fontsize=12, color='#95a5a6')

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    output_path = os.path.join(OUTPUT_DIR, 'article_benchmark_comparison.png')
    plt.savefig(output_path, dpi=300, facecolor='#1a1a1a', bbox_inches='tight')
    print(f"✅ 已生成：{output_path}")
    plt.close()


# ============================================================================
# 主程式
# ============================================================================
def main():
    print("=" * 60)
    print("🎨 技術文章視覺化生成器")
    print("=" * 60)
    print()

    # 生成 3 張圖表
    generate_topology_comparison()
    print()
    generate_hybrid_architecture()
    print()
    generate_benchmark_comparison()

    print()
    print("=" * 60)
    print("🎉 所有圖表生成完成！")
    print("=" * 60)
    print()
    print("📁 輸出位置：")
    print(f"   ✅ {OUTPUT_DIR}/article_topology_bottleneck.png")
    print(f"   ✅ {OUTPUT_DIR}/article_hybrid_architecture.png")
    print(f"   ✅ {OUTPUT_DIR}/article_benchmark_comparison.png")
    print()
    print("📸 還需要你拍照的：")
    print("   📷 圖片 #1: 機殼側板打開（兩顆 PSU + 兩張顯卡）")
    print("   📷 圖片 #2: Dual PSU Starter 接頭特寫")
    print("   📷 圖片 #3: 終端機 NCCL 報錯截圖（可選）")
    print()

if __name__ == "__main__":
    main()
