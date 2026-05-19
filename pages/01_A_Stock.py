'''
A股股票分析 — 个股K线 + 技术指标 + 多股对比
'''
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import streamlit as st
import pandas as pd
import numpy as np

from styles import inject
from data_fetcher import (get_stock_list, get_stock_hist_tx,
                           get_start_date, get_market_pe_pb)
from charts import (plot_kline, plot_rsi, plot_macd, plot_bollinger,
                    plot_nav_comparison, plot_drawdown_comparison,
                    plot_rolling_returns, plot_enhanced_radar)
from scoring import compute_scores, generate_advice

st.set_page_config(page_title='A股股票分析', page_icon='📈', layout='wide')
inject()

st.title('A股股票分析')

# ── Sidebar ──────────────────────────────────────────────

st.sidebar.header('筛选 & 选择')

@st.cache_data(ttl=3600)
def load_stocks():
    try:
        return get_stock_list()
    except Exception:
        return pd.DataFrame()

with st.spinner('加载股票列表...'):
    stock_df = load_stocks()

if stock_df.empty:
    st.error('获取股票列表失败，请检查网络。')
    st.stop()

search = st.sidebar.text_input('搜索股票', placeholder='名称或代码，如：平安、000001')
if search:
    mask = stock_df['name'].str.contains(search, na=False) | stock_df['code'].str.contains(search, na=False)
    filtered = stock_df[mask].head(100)
else:
    filtered = stock_df.head(80)

st.sidebar.caption(f'{len(filtered)} / {len(stock_df)} 只股票')

mode = st.sidebar.radio('分析模式', ['单股深度分析', '多股对比'], horizontal=True)

if mode == '单股深度分析':
    options = [f"{r['code']} - {r['name']}" for _, r in filtered.iterrows()]
    selected = st.sidebar.selectbox('选择股票', options=options)
    lookback = st.sidebar.selectbox('回看时间', ['1个月', '3个月', '6个月', '1年', '2年'], index=2)
else:
    options = [f"{r['code']} - {r['name']}" for _, r in filtered.iterrows()]
    selected_list = st.sidebar.multiselect(
        '选择股票（2-5只）', options=options, max_selections=5,
        placeholder='至少选 2 只')
    lookback = st.sidebar.selectbox('回看时间', ['1个月', '3个月', '6个月', '1年', '2年'], index=3)

# ── 单股深度分析 ──────────────────────────────────────

if mode == '单股深度分析':
    if not selected:
        st.info('请选择一只股票')
        st.stop()

    code = selected.split(' - ')[0]
    name = selected.split(' - ', 1)[1]
    start_date = get_start_date(lookback)

    with st.spinner(f'加载 {name} 数据...'):
        df = get_stock_hist_tx(code, start_date)

    if df.empty:
        st.error(f'{name} ({code}) 获取数据失败')
        st.stop()

    # 信息卡片
    latest = df.iloc[-1]
    chg = latest['close'] - df.iloc[-2]['close'] if len(df) > 1 else 0
    chg_pct = (chg / df.iloc[-2]['close']) * 100 if len(df) > 1 else 0
    clr = '#e74c3c' if chg >= 0 else '#27ae60'
    sign = '+' if chg >= 0 else ''

    info1, info2, info3, info4 = st.columns(4)
    with info1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">{name}</div>
            <div class="value" style="font-size:1.1rem;">{code}</div>
            <div class="sub">{latest['close']:.2f} <span class="{'up' if chg>=0 else 'down'}">{sign}{chg:.2f} ({sign}{chg_pct:.2f}%)</span></div>
        </div>''', unsafe_allow_html=True)

    with info2:
        high, low = df['high'].max(), df['low'].min()
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">区间最高 / 最低</div>
            <div class="value" style="font-size:1rem;">{high:.2f} / {low:.2f}</div>
            <div class="sub">振幅 {(high/low - 1) * 100:.1f}%</div>
        </div>''', unsafe_allow_html=True)

    with info3:
        vol_avg = df['volume'].mean() if 'volume' in df.columns else 0
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">区间日均成交量</div>
            <div class="value" style="font-size:1rem;">{vol_avg/1e6:.1f}万手</div>
            <div class="sub">{lookback}</div>
        </div>''', unsafe_allow_html=True)

    with info4:
        ret = (latest['close'] / df.iloc[0]['close'] - 1) * 100
        r_sign = '+' if ret >= 0 else ''
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">区间收益</div>
            <div class="value" style="font-size:1rem;color:{'#e74c3c' if ret>=0 else '#27ae60'};">
                {r_sign}{ret:.2f}%</div>
            <div class="sub">{lookback}</div>
        </div>''', unsafe_allow_html=True)

    # K线图
    st.plotly_chart(plot_kline(df, title=f'{name} ({code})'), use_container_width=True)

    # 技术指标
    tech_tab1, tech_tab2, tech_tab3 = st.tabs(['RSI', 'MACD', '布林带'])
    with tech_tab1:
        st.plotly_chart(plot_rsi(df), use_container_width=True)
    with tech_tab2:
        st.plotly_chart(plot_macd(df), use_container_width=True)
    with tech_tab3:
        st.plotly_chart(plot_bollinger(df), use_container_width=True)

    # 简易评分
    data = {name: df}
    scores = compute_scores(data)
    advice = generate_advice(scores)
    if advice:
        a = advice[0]
        st.markdown(f'''
        <div class="advice-card">
            <div style="display:flex;align-items:center;margin-bottom:12px;">
                <span class="score-badge {a['level_class']}">{a['total']}</span>
                <div>
                    <strong style="font-size:1.2rem;">{a['stars']} {a['level']}</strong>
                    <div style="color:#6b7280;font-size:0.82rem;">综合评分 · 满分100</div>
                </div>
            </div>
            <div style="display:flex;gap:24px;font-size:0.85rem;">
                <div><strong>优势：</strong>{', '.join(a['strengths']) if a['strengths'] else '暂无明显优势'}</div>
                <div><strong>风险：</strong>{', '.join(a['warnings']) if a['warnings'] else '暂无显著风险信号'}</div>
                <div><strong>适合：</strong>{a['suitable']}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

# ── 多股对比 ──────────────────────────────────────────

else:
    if len(selected_list) < 2:
        st.info('请选择至少 2 只股票开始对比')
        st.stop()

    codes = [s.split(' - ')[0] for s in selected_list]
    names = [s.split(' - ', 1)[1] for s in selected_list]
    start_date = get_start_date(lookback)

    data = {}
    with st.spinner('获取多只股票数据...'):
        for code, name in zip(codes, names):
            try:
                df = get_stock_hist_tx(code, start_date)
                if not df.empty:
                    data[name] = df
            except Exception as e:
                st.warning(f'{name} ({code}) 获取失败: {e}')

    if len(data) < 2:
        st.error('有效数据不足')
        st.stop()

    # 信息卡片
    info_cols = st.columns(len(names))
    for i, (code, name) in enumerate(zip(codes, names)):
        df = data.get(name)
        if df is not None:
            ret = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
            r_clr = '#e74c3c' if ret >= 0 else '#27ae60'
            r_sign = '+' if ret >= 0 else ''
            with info_cols[i]:
                st.markdown(f'''
                <div class="info-card">
                    <div class="etf-name">{name}</div>
                    <div class="etf-code">{code}</div>
                    <div class="price" style="color:{r_clr};">{r_sign}{ret:.2f}%</div>
                    <div class="row"><span>区间收益</span><span>{lookback}</span></div>
                </div>
                ''', unsafe_allow_html=True)

    # 图表
    st.subheader(f'对比周期：{lookback}')

    tab1, tab2, tab3 = st.tabs(['走势 & 回撤', '指标对比', '雷达图 & 建议'])

    with tab1:
        view_mode = st.radio('', ['净值走势', '回撤曲线', '滚动收益'],
                             horizontal=True, label_visibility='collapsed')
        if view_mode == '净值走势':
            st.plotly_chart(plot_nav_comparison(data), use_container_width=True)
        elif view_mode == '回撤曲线':
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
            st.download_button('导出 CSV', csv, 'stock_compare.csv', 'text/csv')

    with tab3:
        scores = compute_scores(data)
        st.plotly_chart(plot_enhanced_radar(scores), use_container_width=True)

        # 投资建议
        advices = generate_advice(scores)
        st.subheader('投资建议')
        for a in advices:
            if a['total'] == 0:
                st.info(f'{a["name"]}: 数据不足，无法评分')
                continue
            stars_display = '⭐' * len(a['stars'].replace('★', '⭐').replace('☆', ''))
            st.markdown(f'''
            <div class="advice-card">
                <div style="display:flex;align-items:center;margin-bottom:10px;">
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
st.caption('数据来源：腾讯证券 · 东方财富  |  仅供分析参考，不构成投资建议')
