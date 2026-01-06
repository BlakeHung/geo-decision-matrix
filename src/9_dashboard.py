import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# 設定網頁標題
st.set_page_config(page_title="AI 物流物流戰情室", layout="wide")

st.title("🚚 Geo-Decision AI 物流智慧戰情室")
st.markdown("---")

# 設定 API 來源 (指向你剛才啟動的 FastAPI)
API_URL_RESULTS = "http://localhost:8000/results"
API_URL_AI = "http://localhost:8000/ai/analyze_risks"

# 側邊欄：重新整理按鈕
if st.sidebar.button("🔄 更新數據"):
    st.cache_data.clear()

try:
    # 1. 抓取分群數據
    res_data = requests.get(API_URL_RESULTS).json()
    df = pd.DataFrame(res_data)

    # 第一排：關鍵指標
    col1, col2, col3 = st.columns(3)
    col1.metric("總司機數", len(df))
    col2.metric("高風險人數", len(df[df['label'].str.contains("Risk")]))
    col3.metric("平均時速", f"{df['average_speed'].mean():.2f} km/h")

    # 第二排：圖表分析
    st.subheader("📊 風險分佈與數據特徵")
    chart_col, data_col = st.columns([1, 1])

    with chart_col:
        fig = px.pie(df, names='label', title="司機風險等級比例", hole=0.4,
                     color_discrete_map={"Risk: Congested":"#EF553B", "Good: Efficient":"#00CC96", "Normal: Average":"#FECB52"})
        st.plotly_chart(fig, use_container_width=True)

    with data_col:
        fig2 = px.scatter(df, x="average_speed", y="stuck_count", color="label",
                         title="時速 vs 擁堵次數分佈",
                         labels={"average_speed": "平均時速", "stuck_count": "擁堵次數"})
        st.plotly_chart(fig2, use_container_width=True)

    # 第三排：AI 顧問建議
    st.markdown("---")
    st.subheader("🤖 RTX 3090 AI 顧問：即時決策建議")
    
    if st.button("🔍 執行 AI 深度分析"):
        with st.spinner('3090 正在運算中...'):
            ai_res = requests.get(API_URL_AI).json()
            ai_df = pd.DataFrame(ai_res['ai_insights'])
            
            # 美化表格顯示
            st.table(ai_df[['driver_id', 'label', 'speed', 'ai_sentiment', 'management_advice']])
            st.success("✅ AI 建議報告已生成")

except Exception as e:
    st.error(f"❌ 無法連線至 API 伺服器，請確保 7_api_server.py 正在運行中。 (錯誤: {e})")