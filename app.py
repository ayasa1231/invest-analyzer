'''
全能投资分析平台 — 首页市场总览
'''
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data_fetcher import get_stock_hot_rank, get_stock_xstp_rank, get_etf_list
from styles import inject

st.set_page_config(page_title='投资分析平台', page_icon='📊', layout='wide')
inject()

# ── 头部 ─────────────────────────────────────────────────

st.title('全能投资分析平台')
st.caption('覆盖 A股股票 · 基金/ETF · 美股ETF — 量化评分 + 投资建议')

# ── 市场指数卡片 ──────────────────────────────────────

idx1, idx2, idx3, idx4 = st.columns(4)

index_cards = [
    ('上证指数', '#e74c3c'),
    ('深证成指', '#27ae60'),
    ('创业板指', '#3b82f6'),
    ('科创50', '#f59e0b'),
]

for col, (name, accent) in zip([idx1, idx2, idx3, idx4], index_cards):
    val = '-'
    chg_text = '数据加载中'
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily_em(symbol='sh000001' if name == '上证指数' else
                                         'sz399001' if name == '深证成指' else
                                         'sz399006' if name == '创业板指' else 'sh000688')
        if not df.empty and len(df) >= 2:
            latest_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            latest_price = float(latest_row['close'])
            prev_price = float(prev_row['close'])
            change = latest_price - prev_price
            change_pct = (change / prev_price) * 100
            s = '+' if change >= 0 else ''
            c = '#e74c3c' if change >= 0 else '#27ae60'
            val = f'{latest_price:.2f}'
            chg_text = f'<span style="color:{c};">{s}{change:.2f} ({s}{change_pct:.2f}%)</span>'
    except Exception:
        pass

    with col:
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">{name}</div>
            <div class="value" style="font-size:1.2rem;">{val}</div>
            <div class="sub">{chg_text}</div>
        </div>
        ''', unsafe_allow_html=True)

# ── 热门板块 ──────────────────────────────────────────

st.subheader('热门排名')

tab_a, tab_b = st.tabs(['热门个股', '向上突破'])

with tab_a:
    try:
        hot = get_stock_hot_rank()
        if not hot.empty:
            hot_cols = [c for c in ['代码', '名称', '最新价', '涨跌幅', '成交额', '排名']
                        if c in hot.columns]
            if '代码' in hot.columns:
                show = hot.head(10)
            else:
                show = hot.head(10)
            st.dataframe(show, use_container_width=True, hide_index=True,
                         height=380)
        else:
            st.info('暂无热门排名数据')
    except Exception as e:
        st.info(f'数据加载中: {e}')

with tab_b:
    try:
        xstp = get_stock_xstp_rank()
        if not xstp.empty:
            st.dataframe(xstp.head(10), use_container_width=True,
                         hide_index=True, height=380)
        else:
            st.info('暂无向上突破数据')
    except Exception:
        st.info('数据加载中')

# ── 快捷入口 ──────────────────────────────────────────

st.subheader('快捷导航')

nav1, nav2, nav3 = st.columns(3)
with nav1:
    st.page_link('pages/01_A股股票.py', label='A股股票分析', icon='📈')
    st.caption('个股K线 · 技术指标 · 多股对比')
with nav2:
    st.page_link('pages/02_基金ETF对比.py', label='基金/ETF 对比', icon='📊')
    st.caption('ETF对比 · 公募基金 · 量化评分')
with nav3:
    st.page_link('pages/03_美股ETF.py', label='美股 ETF 分析', icon='🌍')
    st.caption('SPY/QQQ · 跨境对比 · 全球配置')

st.divider()
st.caption('数据来源：东方财富 · 腾讯证券 · Yahoo Finance · 同花顺  |  仅供分析参考，不构成投资建议')
