'''
美股 ETF 分析 — 多只对比 + 评分建议
'''
import streamlit as st
import pandas as pd
import numpy as np

from styles import inject
from data_fetcher import get_us_etf_list, get_us_etf_hist
from charts import (plot_nav_comparison, plot_drawdown_comparison,
                    plot_rolling_returns, plot_enhanced_radar, plot_kline)
from scoring import compute_scores, generate_advice

st.set_page_config(page_title='美股ETF分析', page_icon='🌍', layout='wide')
inject()

st.title('美股 ETF 分析')
st.caption('数据源：Yahoo Finance  |  预设 20 只热门美股 ETF')

# ── Sidebar ──────────────────────────────────────────────

st.sidebar.header('选择 ETF')

mode = st.sidebar.radio('分析模式', ['多只对比', '单只详情'], horizontal=True)

PERIOD_MAP = {
    '1个月': '1mo', '3个月': '3mo', '6个月': '6mo',
    '1年': '1y', '2年': '2y', '5年': '5y',
}

etf_list = get_us_etf_list()
search = st.sidebar.text_input('搜索', placeholder='如：SPY、QQQ')
if search:
    mask = etf_list['code'].str.contains(search.upper(), na=False) | etf_list['name'].str.contains(search, na=False)
    filtered = etf_list[mask]
else:
    filtered = etf_list

options = [f"{r['code']} - {r['name']}" for _, r in filtered.iterrows()]

if mode == '单只详情':
    selected = st.sidebar.selectbox('选择 ETF', options=options)
    period_label = st.sidebar.selectbox('回看时间', list(PERIOD_MAP.keys()), index=3)
else:
    selected_list = st.sidebar.multiselect(
        '选择 ETF（2-5只）', options=options, max_selections=5,
        placeholder='至少选 2 只')
    period_label = st.sidebar.selectbox('回看时间', list(PERIOD_MAP.keys()), index=3)

period = PERIOD_MAP[period_label]

# ── 单只详情 ─────────────────────────────────────────────

if mode == '单只详情':
    if not selected:
        st.info('请选择一只 ETF')
        st.stop()

    code = selected.split(' - ')[0]
    name = selected.split(' - ', 1)[1]

    with st.spinner(f'加载 {code} 数据...'):
        df = get_us_etf_hist(code, period)

    if df.empty:
        st.error(f'{code} 获取数据失败，Yahoo Finance 可能暂时不可用。')
        st.stop()

    # Info cards
    latest = df.iloc[-1]
    chg = latest['close'] - df.iloc[-2]['close'] if len(df) > 1 else 0
    chg_pct = (chg / df.iloc[-2]['close']) * 100 if len(df) > 1 else 0

    i1, i2, i3, i4 = st.columns(4)
    with i1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">{code}</div>
            <div class="value" style="font-size:1.1rem;">{latest['close']:.2f} USD</div>
            <div class="sub"><span class="{'up' if chg>=0 else 'down'}">{'+' if chg>=0 else ''}{chg:.2f} ({'+' if chg>=0 else ''}{chg_pct:.2f}%)</span></div>
        </div>''', unsafe_allow_html=True)

    high, low = df['high'].max(), df['low'].min()
    with i2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">区间最高 / 最低</div>
            <div class="value" style="font-size:1rem;">{high:.2f} / {low:.2f}</div>
            <div class="sub">振幅 {(high/low - 1)*100:.1f}%</div>
        </div>''', unsafe_allow_html=True)

    with i3:
        vol_avg = df['volume'].mean() if 'volume' in df.columns else 0
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">区间日均成交量</div>
            <div class="value" style="font-size:1rem;">{vol_avg/1e6:.1f}M</div>
            <div class="sub">{period_label}</div>
        </div>''', unsafe_allow_html=True)

    ret = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
    with i4:
        st.markdown(f'''
        <div class="metric-card">
            <div class="label">区间收益</div>
            <div class="value" style="font-size:1rem;color:{'#e74c3c' if ret>=0 else '#27ae60'};">
                {'+' if ret>=0 else ''}{ret:.2f}%</div>
            <div class="sub">{period_label}</div>
        </div>''', unsafe_allow_html=True)

    # K线图
    st.plotly_chart(plot_kline(df, title=f'{name} ({code})'), use_container_width=True)

    # Scoring
    data_for_score = {name: df}
    scores = compute_scores(data_for_score)
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

# ── 多只对比 ─────────────────────────────────────────────

else:
    if len(selected_list) < 2:
        st.info('选择至少 2 只 ETF 开始对比')
        st.stop()

    codes = [s.split(' - ')[0] for s in selected_list]
    names = [s.split(' - ', 1)[1] for s in selected_list]

    data = {}
    with st.spinner('获取美股数据 (Yahoo Finance)...'):
        for code, name in zip(codes, names):
            try:
                df = get_us_etf_hist(code, period)
                if not df.empty:
                    data[name] = df
            except Exception as e:
                st.warning(f'{code} 获取失败: {e}')

    if len(data) < 2:
        st.error('有效数据不足，Yahoo Finance 可能暂时不可用。')
        st.stop()

    # Info cards
    info_cols = st.columns(len(names))
    for i, (code, name) in enumerate(zip(codes, names)):
        df = data.get(name)
        ret = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100 if df is not None else 0
        r_clr = '#e74c3c' if ret >= 0 else '#27ae60'
        with info_cols[i]:
            st.markdown(f'''
            <div class="info-card">
                <div class="etf-name">{name}</div>
                <div class="etf-code">{code}</div>
                <div class="price" style="color:{r_clr};">{' +' if ret>=0 else ''}{ret:.2f}%</div>
                <div class="row"><span>区间收益</span><span>{period_label}</span></div>
            </div>
            ''', unsafe_allow_html=True)

    # Charts
    st.subheader(f'对比周期：{period_label}')

    tab1, tab2, tab3 = st.tabs(['走势 & 回撤', '指标对比', '雷达图 & 建议'])

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
            st.download_button('导出 CSV', csv, 'us_etf_compare.csv', 'text/csv')

    with tab3:
        scores = compute_scores(data)
        st.plotly_chart(plot_enhanced_radar(scores), use_container_width=True)

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
st.caption('数据来源：Yahoo Finance  |  仅供分析参考，不构成投资建议')
