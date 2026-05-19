'''
统一 CSS 样式注入
'''
import streamlit as st

CSS = '''
<style>
    /* 全局 */
    .stApp { background-color: #f7f8fa; }
    header[data-testid="stHeader"] { background-color: #f7f8fa; }
    section[data-testid="stSidebar"] { background-color: #f0f2f6; }

    /* 标题 */
    h1 { color: #1a1a2e; font-weight: 700; font-size: 1.8rem !important; }
    h2 { color: #1a1a2e; font-weight: 600; padding-top: 0.5rem; }
    h3 { color: #2d3436; font-weight: 600; }

    /* 指标卡片 */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 18px 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        border: 1px solid #eef0f4;
        text-align: center;
        transition: box-shadow 0.15s;
    }
    .metric-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
    .metric-card .label {
        font-size: 0.76rem; color: #6b7280; margin-bottom: 4px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .metric-card .value {
        font-size: 1.4rem; font-weight: 700; color: #1a1a2e;
    }
    .metric-card .sub {
        font-size: 0.72rem; color: #6b7280; margin-top: 2px;
    }

    /* 信息卡片 */
    .info-card {
        background: white;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #eef0f4;
    }
    .info-card .etf-name { font-size: 0.95rem; font-weight: 700; color: #1a1a2e; }
    .info-card .etf-code { font-size: 0.73rem; color: #9ca3af; }
    .info-card .price { font-size: 1.25rem; font-weight: 700; color: #1a1a2e; margin: 6px 0; }
    .info-card .row { display: flex; justify-content: space-between; font-size: 0.76rem; color: #6b7280; margin-top: 2px; }

    /* A股涨跌色：红涨绿跌 */
    .up   { color: #e74c3c !important; }
    .down { color: #27ae60 !important; }

    /* 投资建议卡片 */
    .advice-card {
        background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%);
        border-radius: 12px;
        padding: 20px 24px;
        border: 1px solid #dde4f0;
        margin: 16px 0;
    }
    .advice-card .score-badge {
        display: inline-block;
        font-size: 2rem; font-weight: 800;
        padding: 6px 16px;
        border-radius: 8px;
        margin-right: 12px;
    }
    .score-high   { background: #d4edda; color: #155724; }
    .score-mid    { background: #fff3cd; color: #856404; }
    .score-low    { background: #f8d7da; color: #721c24; }

    /* 侧边栏 */
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #2d3436;
    }

    /* 表格 */
    [data-testid="stDataFrame"] table { font-size: 0.84rem; }
    [data-testid="stDataFrame"] th { font-weight: 600 !important; text-align: center !important; }

    /* 按钮 */
    .stButton > button { border-radius: 8px; font-weight: 500; }

    hr { border-color: #e5e7eb; }
</style>
'''


def inject():
    st.markdown(CSS, unsafe_allow_html=True)
