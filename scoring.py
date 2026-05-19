'''
量化评分引擎 & 投资建议生成
'''
import numpy as np
import pandas as pd

RISK_FREE = 0.025
TRADING_DAYS = 252


def compute_scores(data: dict) -> dict:
    '''
    输入: {name: DataFrame(with 'close' column)}
    输出: {name: {总分, 趋势得分, 动量得分, 风险得分, 夏普得分, ...}}
    '''
    results = {}
    for name, df in data.items():
        close = df['close']
        rets = close.pct_change().dropna()
        if len(rets) < 15:
            results[name] = None
            continue

        cum_ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
        ann_ret = (1 + cum_ret / 100) ** (TRADING_DAYS / len(rets)) - 1
        ann_vol = rets.std() * np.sqrt(TRADING_DAYS)
        peak = close.expanding().max()
        max_dd = ((close - peak) / peak).min() * 100
        sharpe = (ann_ret - RISK_FREE) / ann_vol if ann_vol > 0 else 0

        # Recent returns
        n = len(close)
        r_1m = (close.iloc[-1] / close.iloc[-min(21, n)] - 1) * 100
        r_3m = (close.iloc[-1] / close.iloc[-min(63, n)] - 1) * 100
        r_6m = (close.iloc[-1] / close.iloc[-min(126, n)] - 1) * 100

        # Trend score: MA alignment (0-100)
        ma_scores = []
        for w in [5, 10, 20, 60]:
            ma = close.rolling(w).mean()
            if len(ma.dropna()) > 0:
                above = (close.iloc[-1] > ma.iloc[-1])
                ma_scores.append(1 if above else 0)
        trend_score = sum(ma_scores) / len(ma_scores) * 100 if ma_scores else 50

        # Momentum score: weighted recent returns, baseline 55
        raw_momentum = (r_1m * 2.0 + r_3m * 1.2 + r_6m * 0.6) / 6 + 55
        momentum_score = np.clip(raw_momentum, 0, 100)

        # Risk score: penalty for drawdown & volatility, baseline 100
        raw_risk = 100 - abs(max_dd) * 1.2 - ann_vol * 100 * 1.5
        risk_score = np.clip(raw_risk, 0, 100)

        # Sharpe score: baseline 60 (neutral), goes up/down from there
        sharpe_score = np.clip(sharpe * 20 + 60, 0, 100)

        # Composite — balanced weights
        total = (trend_score * 0.25 + momentum_score * 0.25 +
                 risk_score * 0.25 + sharpe_score * 0.25)

        results[name] = {
            '总分': round(total, 1),
            '趋势得分': round(trend_score, 1),
            '动量得分': round(momentum_score, 1),
            '风险得分': round(risk_score, 1),
            '夏普得分': round(sharpe_score, 1),
            '累计收益': round(cum_ret, 2),
            '年化收益': round(ann_ret * 100, 2),
            '年化波动率': round(ann_vol * 100, 2),
            '最大回撤': round(max_dd, 2),
            '夏普比率': round(sharpe, 2),
            '近1月收益': round(r_1m, 2),
            '近3月收益': round(r_3m, 2),
            '近6月收益': round(r_6m, 2),
        }

    return results


def generate_advice(score_data: dict) -> list:
    '''
    根据评分生成投资建议卡片数据
    返回: [{name, total, stars, level, strengths, warnings, suitable}]
    '''
    advices = []
    for name, s in score_data.items():
        if s is None:
            advices.append({
                'name': name, 'total': 0, 'stars': '',
                'level': '数据不足', 'level_class': 'score-low',
                'strengths': [], 'warnings': ['历史数据不足，无法评分'],
                'suitable': '-',
            })
            continue

        total = s['总分']
        if total >= 75:
            stars, level, cls = '★★★★★', '强烈推荐', 'score-high'
        elif total >= 60:
            stars, level, cls = '★★★★', '推荐', 'score-high'
        elif total >= 45:
            stars, level, cls = '★★★', '中性', 'score-mid'
        elif total >= 30:
            stars, level, cls = '★★', '谨慎', 'score-mid'
        else:
            stars, level, cls = '★', '回避', 'score-low'

        # Strengths
        strengths = []
        dims = {'趋势得分': '趋势强劲', '动量得分': '近期动量强',
                '风险得分': '风险控制好', '夏普得分': '风险调整收益高'}
        for key, label in dims.items():
            if s.get(key, 0) >= 60:
                strengths.append(label)

        # Warnings
        warnings = []
        if s['年化波动率'] > 35:
            warnings.append(f'波动率偏高 ({s["年化波动率"]}%)')
        if s['最大回撤'] < -25:
            warnings.append(f'回撤较大 ({s["最大回撤"]}%)')
        if s['夏普比率'] < 0:
            warnings.append('夏普比率为负')

        # Suitable investor type
        if s['年化波动率'] < 15 and s['最大回撤'] > -10:
            suitable = '稳健型、保守型'
        elif s['年化波动率'] < 25:
            suitable = '均衡型、稳健型'
        else:
            suitable = '进取型、短线交易者'

        advices.append({
            'name': name, 'total': total, 'stars': stars,
            'level': level, 'level_class': cls,
            'strengths': strengths,
            'warnings': warnings,
            'suitable': suitable,
        })

    return advices
