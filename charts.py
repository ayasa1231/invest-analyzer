'''
共用图表绘制函数
'''
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']


def _rgb(color, alpha=1.0):
    '''hex → rgba'''
    c = color.lstrip('#')
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


# ── 通用对比图 ──────────────────────────────────────────

def plot_nav_comparison(data: dict) -> go.Figure:
    '''归一化净值对比'''
    fig = go.Figure()
    for (name, df), color in zip(data.items(), COLORS):
        norm = df['close'] / df['close'].iloc[0]
        fig.add_trace(go.Scatter(
            x=df['date'], y=norm, mode='lines', name=name,
            line=dict(width=2.5, color=color)))
    fig.update_layout(
        title='净值走势对比 (归一化，起点=1)', xaxis_title='',
        hovermode='x unified', height=400, margin=dict(t=40, b=10),
        plot_bgcolor='#fafbfc', paper_bgcolor='#fafbfc',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def plot_drawdown_comparison(data: dict) -> go.Figure:
    '''回撤对比'''
    fig = go.Figure()
    for (name, df), color in zip(data.items(), COLORS):
        peak = df['close'].expanding().max()
        dd = (df['close'] - peak) / peak * 100
        fig.add_trace(go.Scatter(
            x=df['date'], y=dd, mode='lines', name=name,
            fill='tozeroy', line=dict(width=2, color=color),
            fillcolor=_rgb(color, 0.12)))
    fig.add_hline(y=0, line_dash='dash', line_color='#d1d5db', line_width=1)
    fig.update_layout(
        title='回撤对比', xaxis_title='',
        yaxis_title='回撤 (%)', yaxis=dict(tickformat='.1f'),
        hovermode='x unified', height=360, margin=dict(t=40, b=10),
        plot_bgcolor='#fafbfc', paper_bgcolor='#fafbfc',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def plot_rolling_returns(data: dict, window: int = 30) -> go.Figure:
    '''滚动收益率'''
    fig = go.Figure()
    for (name, df), color in zip(data.items(), COLORS):
        ret = df['close'].pct_change(window) * 100
        fig.add_trace(go.Scatter(
            x=df['date'], y=ret, mode='lines', name=name,
            line=dict(width=2, color=color)))
    fig.add_hline(y=0, line_dash='dash', line_color='#d1d5db', line_width=1)
    fig.update_layout(
        title=f'{window}日滚动收益率', xaxis_title='',
        yaxis_title='收益率 (%)', hovermode='x unified',
        height=380, margin=dict(t=40, b=10),
        plot_bgcolor='#fafbfc', paper_bgcolor='#fafbfc',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def plot_enhanced_radar(scores: dict) -> go.Figure:
    '''6维雷达图'''
    categories = ['趋势得分', '动量得分', '风险得分', '夏普得分',
                  '近1月收益', '累计收益']
    norm = {}
    for name, s in scores.items():
        if s is None:
            continue
        row = {}
        for cat in categories:
            val = s.get(cat, 50)
            if isinstance(val, (int, float)):
                row[cat] = max(0, min(100, val))
            else:
                row[cat] = 50
        # Scale return categories
        for cat in ['近1月收益', '累计收益']:
            raw = s.get(cat, 0)
            if isinstance(raw, (int, float)):
                row[cat] = max(0, min(100, 50 + raw * 3))
            else:
                row[cat] = 50
        norm[name] = row

    fig = go.Figure()
    for (name, vals), color in zip(norm.items(), COLORS):
        fig.add_trace(go.Scatterpolar(
            r=[vals[c] for c in categories],
            theta=categories, fill='toself', name=name,
            line=dict(color=color, width=2.5),
            fillcolor=_rgb(color, 0.2)))
    fig.update_layout(
        title='综合能力雷达图',
        polar=dict(radialaxis=dict(range=[0, 100], showticklabels=False)),
        height=450, margin=dict(t=40, b=10),
        plot_bgcolor='#fafbfc', paper_bgcolor='#fafbfc',
        legend=dict(orientation='h', yanchor='bottom', y=1.06, xanchor='right', x=1))
    return fig


# ── K线图 ───────────────────────────────────────────────

def plot_kline(df: pd.DataFrame, title: str = '') -> go.Figure:
    '''K线图 + MA均线 + 成交量'''
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.7, 0.3], vertical_spacing=0.04)

    # Candlestick
    if 'open' in df.columns:
        fig.add_trace(go.Candlestick(
            x=df['date'], open=df['open'], high=df['high'],
            low=df['low'], close=df['close'],
            name='K线',
            increasing=dict(line=dict(color='#e74c3c'), fillcolor='#e74c3c'),
            decreasing=dict(line=dict(color='#27ae60'), fillcolor='#27ae60'),
        ), row=1, col=1)

    # Moving averages
    for w, style in [(5, 'solid'), (10, 'dash'), (20, 'dot'), (60, 'dashdot')]:
        ma = df['close'].rolling(w).mean()
        fig.add_trace(go.Scatter(
            x=df['date'], y=ma, mode='lines', name=f'MA{w}',
            line=dict(width=1.5, dash=style)), row=1, col=1)

    # Volume
    colors = ['#e74c3c' if c >= o else '#27ae60'
              for c, o in zip(df.get('close', df['close']),
                              df.get('open', df['close']))]
    if 'volume' in df.columns:
        fig.add_trace(go.Bar(
            x=df['date'], y=df['volume'], name='成交量',
            marker=dict(color=colors, opacity=0.5)), row=2, col=1)

    fig.update_layout(
        title=title or 'K线图',
        xaxis_rangeslider_visible=False,
        height=520, margin=dict(t=40, b=10),
        plot_bgcolor='#fafbfc', paper_bgcolor='#fafbfc',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(title=''), yaxis=dict(title='价格'),
        yaxis2=dict(title='成交量'))
    return fig


# ── 技术指标 ────────────────────────────────────────────

def plot_rsi(df: pd.DataFrame, period: int = 14) -> go.Figure:
    '''RSI 指标'''
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=rsi, mode='lines', name=f'RSI({period})',
        line=dict(width=2, color='#3b82f6')))
    fig.add_hline(y=70, line_dash='dash', line_color='#e74c3c', line_width=1,
                  annotation_text='超买 70')
    fig.add_hline(y=30, line_dash='dash', line_color='#27ae60', line_width=1,
                  annotation_text='超卖 30')
    fig.add_hline(y=50, line_dash='dot', line_color='#9ca3af', line_width=0.5)
    fig.update_layout(
        title=f'RSI({period})', height=260, margin=dict(t=40, b=10),
        plot_bgcolor='#fafbfc', paper_bgcolor='#fafbfc',
        yaxis=dict(range=[0, 100]))
    return fig


def plot_macd(df: pd.DataFrame,
              fast: int = 12, slow: int = 26, signal: int = 9) -> go.Figure:
    '''MACD 指标'''
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    macd_bar = (dif - dea) * 2

    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Bar(
        x=df['date'], y=macd_bar, name='柱',
        marker=dict(color=['#e74c3c' if v >= 0 else '#27ae60' for v in macd_bar],
                     opacity=0.5)))
    fig.add_trace(go.Scatter(
        x=df['date'], y=dif, mode='lines', name='DIF',
        line=dict(width=1.5, color='#3b82f6')))
    fig.add_trace(go.Scatter(
        x=df['date'], y=dea, mode='lines', name='DEA',
        line=dict(width=1.5, color='#f59e0b')))
    fig.add_hline(y=0, line_color='#9ca3af', line_width=1)
    fig.update_layout(
        title='MACD', height=260, margin=dict(t=40, b=10),
        plot_bgcolor='#fafbfc', paper_bgcolor='#fafbfc',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def plot_bollinger(df: pd.DataFrame, period: int = 20) -> go.Figure:
    '''布林带'''
    ma = df['close'].rolling(period).mean()
    std = df['close'].rolling(period).std()
    upper = ma + 2 * std
    lower = ma - 2 * std

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=upper, mode='lines', name='上轨',
        line=dict(width=1, color='#9ca3af', dash='dash')))
    fig.add_trace(go.Scatter(
        x=df['date'], y=lower, mode='lines', name='下轨',
        line=dict(width=1, color='#9ca3af', dash='dash'),
        fill='tonexty', fillcolor='rgba(128,128,128,0.06)'))
    fig.add_trace(go.Scatter(
        x=df['date'], y=ma, mode='lines', name=f'MA{period}',
        line=dict(width=1.5, color='#3b82f6')))
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['close'], mode='lines', name='收盘价',
        line=dict(width=2, color='#1a1a2e')))
    fig.update_layout(
        title=f'布林带 (Bollinger, {period})', height=360, margin=dict(t=40, b=10),
        plot_bgcolor='#fafbfc', paper_bgcolor='#fafbfc',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig
