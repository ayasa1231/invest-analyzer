'''
基金 / ETF 对比分析
'''
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import streamlit as st
import pandas as pd
import numpy as np

from styles import inject
from data_fetcher import (get_etf_list, get_etf_nav_history, get_etf_daily_info,
                           get_mutual_fund_list, get_mutual_fund_nav_history,
                           get_mutual_fund_rank, get_start_date)
from charts import (plot_nav_comparison, plot_drawdown_comparison,
                    plot_rolling_returns, plot_enhanced_radar)
from scoring import compute_scores, generate_advice

st.set_page_config(page_title='基金ETF对比', page_icon='📊', layout='wide')
inject()

st.title('基金 / ETF 对比分析')

# ── Sidebar ──────────────────────────────────────────────

st.sidebar.header('筛选 & 选择')

asset_type = st.sidebar.radio('资产类型', ['A股 ETF', '公募基金'], horizontal=True)

@st.cache_data(ttl=3600)
def load_fund_data(typ):
    if typ == 'A股 ETF':
        return get_etf_list(), get_etf_daily_info()
    else:
        return get_mutual_fund_list(), pd.DataFrame()

with st.spinner('加载列表...'):
    fund_df, info_df = load_fund_data(asset_type)

if fund_df.empty:
    st.error('获取数据失败，请检查网络。')
    st.stop()

# Filter by category for mutual funds
if asset_type == '公募基金' and 'category' in fund_df.columns:
    cats = ['全部'] + sorted(fund_df['category'].dropna().unique().tolist())
    cat_filter = st.sidebar.selectbox('基金类型', cats)
    if cat_filter != '全部':
        fund_df = fund_df[fund_df['category'] == cat_filter]

search = st.sidebar.text_input('搜索', placeholder='名称或代码')
if search:
    mask = fund_df['name'].str.contains(search, na=False) | fund_df['code'].str.contains(search, na=False)
    filtered = fund_df[mask].head(100)
else:
    filtered = fund_df.head(80)

st.sidebar.caption(f'{len(filtered)} / {len(fund_df)} 只')

options = [f"{r['code']} - {r['name']}" for _, r in filtered.iterrows()]
selected = st.sidebar.multiselect(
    f'选择（2-5只）', options=options,
    max_selections=5, placeholder='至少选 2 只')

lookback = st.sidebar.selectbox('回看时间', ['1个月', '3个月', '6个月', '1年', '2年'], index=3)

if len(selected) < 2:
    st.info('选择至少 2 只基金/ETF 开始对比')
    st.stop()

codes = [s.split(' - ')[0] for s in selected]
names = [s.split(' - ', 1)[1] for s in selected]

# ── 数据加载 ─────────────────────────────────────────────

start_date = get_start_date(lookback)
data = {}
with st.spinner('获取净值数据...'):
    for code, name in zip(codes, names):
        try:
            if asset_type == 'A股 ETF':
                df = get_etf_nav_history(code, start_date)
            else:
                df = get_mutual_fund_nav_history(code, start_date)
                if 'nav' in df.columns:
                    df = df.rename(columns={'nav': 'close'})
            if not df.empty:
                data[name] = df
        except Exception as e:
            st.warning(f'{name} ({code}) 获取失败: {e}')

if len(data) < 2:
    st.error('有效数据不足')
    st.stop()

# ── 信息卡片 ─────────────────────────────────────────────

st.subheader(f'{asset_type}对比 · {lookback}')

info_cols = st.columns(len(selected))
for i, (code, name) in enumerate(zip(codes, names)):
    df = data.get(name)
    ret = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100 if df is not None else 0
    r_clr = '#e74c3c' if ret >= 0 else '#27ae60'
    r_sign = '+' if ret >= 0 else ''

    # Info card extras
    extra_info = ''
    if asset_type == 'A股 ETF' and not info_df.empty:
        row = info_df[info_df['code'] == code]
        if not row.empty:
            cat = row.iloc[0].get('category', '-')
            disc = row.iloc[0].get('discount', '-')
            extra_info = f'<div class="row"><span>类型</span><span>{cat}</span></div><div class="row"><span>折价率</span><span>{disc}</span></div>'

    with info_cols[i]:
        st.markdown(f'''
        <div class="info-card">
            <div class="etf-name">{name}</div>
            <div class="etf-code">{code}</div>
            <div class="price" style="color:{r_clr};">{r_sign}{ret:.2f}%</div>
            <div class="row"><span>区间收益</span><span>{lookback}</span></div>
            {extra_info}
        </div>
        ''', unsafe_allow_html=True)

# ── 图表 ────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(['走势分析', '指标对比', '雷达图 & 建议'])

with tab1:
    view = st.radio('', ['净值走势', '回撤曲线', '滚动收益'],
                    horizontal=True, label_visibility='collapsed')
    if view == '净值走势':
        st.plotly_chart(plot_nav_comparison(data), use_container_width=True)
    elif view == '回撤曲线':
        st.plotly_chart(plot_drawdown_comparison(data), use_container_width=True)
    else:
        roll = st.selectbox('窗口', [20, 30, 60], index=1,
                            format_func=lambda x: f'{x}日')
        st.plotly_chart(plot_rolling_returns(data, roll), use_container_width=True)

with tab2:
    scores = compute_scores(data)
    rows = []
    for name in names:
        s = scores.get(name)
        if s:
            s['基金'] = name
            rows.append(s)
    if rows:
        df_metrics = pd.DataFrame(rows)
        show_cols = ['基金', '累计收益', '年化收益', '年化波动率', '最大回撤',
                     '夏普比率', '近1月收益', '近3月收益', '近6月收益']
        show_cols = [c for c in show_cols if c in df_metrics.columns]
        st.dataframe(df_metrics[show_cols], use_container_width=True, hide_index=True)
        csv = df_metrics.to_csv(index=False).encode('utf-8-sig')
        st.download_button('导出 CSV', csv, 'fund_compare.csv', 'text/csv')

with tab3:
    scores = compute_scores(data)
    st.plotly_chart(plot_enhanced_radar(scores), use_container_width=True)

    # 排名数据（公募基金）
    if asset_type == '公募基金':
        try:
            rank_df = get_mutual_fund_rank()
            st.subheader('同类排名参考')
            rank_filtered = rank_df[rank_df['基金代码'].isin(codes)] if '基金代码' in rank_df.columns else pd.DataFrame()
            if not rank_filtered.empty:
                show_rank = rank_filtered.head(10)
                st.dataframe(show_rank, use_container_width=True, hide_index=True)
            else:
                st.caption('暂无排名数据')
        except Exception:
            st.caption('排名数据暂不可用')

    # 投资建议
    st.subheader('投资建议')
    advices = generate_advice(scores)
    for a in advices:
        if a['total'] == 0:
            st.info(f'{a["name"]}: 数据不足')
            continue
        st.markdown(f'''
        <div class="advice-card">
            <div style="display:flex;align-items:center;margin-bottom:8px;">
                <span class="score-badge {a['level_class']}">{a['total']}</span>
                <div>
                    <strong style="font-size:1.1rem;">{a['name']} — {a['stars']} {a['level']}</strong>
                    <div style="color:#6b7280;font-size:0.8rem;">
                        优势：{', '.join(a['strengths']) if a['strengths'] else '无'}
                        | 风险：{', '.join(a['warnings']) if a['warnings'] else '低'}
                        | 适合：{a['suitable']}
                    </div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

st.divider()
st.caption('数据来源：东方财富 · 新浪财经  |  仅供分析参考，不构成投资建议')
