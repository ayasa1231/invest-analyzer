'''
数据获取模块 — 封装 akshare + yfinance 接口
'''
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# ── 通用工具 ─────────────────────────────────────────────

def _tx_stock_symbol(code: str) -> str:
    '''A股代码转腾讯格式'''
    if code.startswith(('0', '2', '3')):
        return f'sz{code}'
    else:
        return f'sh{code}'


def _sina_symbol(code: str) -> str:
    '''ETF 代码转新浪格式'''
    if code.startswith(('5', '6')):
        return f'sh{code}'
    return f'sz{code}'


def get_start_date(lookback: str) -> str:
    days_map = {
        '1个月': 30, '3个月': 90, '6个月': 180, '1年': 365, '2年': 730,
    }
    days = days_map.get(lookback, 365)
    start = datetime.now() - timedelta(days=days)
    return start.strftime('%Y%m%d')


# ── A股 ETF ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_etf_list() -> pd.DataFrame:
    '''获取 A股 ETF 全量列表'''
    import akshare as ak
    df = ak.fund_etf_spot_em()
    df = df.rename(columns={
        '代码': 'code', '名称': 'name', '最新价': 'price',
        '涨跌幅': 'pct_change', '成交量': 'volume', '成交额': 'amount',
        '换手率': 'turnover',
    })
    keep = [c for c in ['code', 'name', 'price', 'pct_change', 'volume',
                         'amount', 'turnover'] if c in df.columns]
    return df[keep]


@st.cache_data(ttl=1800, show_spinner=False)
def get_etf_nav_history(code: str, start_date: str) -> pd.DataFrame:
    '''ETF 历史净值 (新浪)'''
    import akshare as ak
    symbol = _sina_symbol(code)
    df = ak.fund_etf_hist_sina(symbol=symbol)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    start_dt = pd.to_datetime(start_date)
    return df[df['date'] >= start_dt]


@st.cache_data(ttl=3600)
def get_etf_daily_info() -> pd.DataFrame:
    '''ETF 当日净值 + 类型 + 折价率'''
    import akshare as ak
    df = ak.fund_etf_fund_daily_em()
    df = df.rename(columns={
        '基金代码': 'code', '基金简称': 'name', '类型': 'category',
        '增长值': 'daily_gain', '增长率': 'daily_pct',
        '市价': 'market_price', '折价率': 'discount',
    })
    keep = ['code', 'name', 'category', 'daily_gain', 'daily_pct',
            'market_price', 'discount']
    keep += [c for c in df.columns if '单位净值' in c or '累计净值' in c]
    keep = [c for c in keep if c in df.columns]
    return df[keep]


# ── A股股票 ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_stock_list() -> pd.DataFrame:
    '''A股股票列表'''
    import akshare as ak
    df = ak.stock_info_a_code_name()
    df = df.rename(columns={'code': 'code', 'name': 'name'})
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def get_stock_hist_tx(code: str, start_date: str) -> pd.DataFrame:
    '''A股个股历史K线 (腾讯数据源)'''
    import akshare as ak
    symbol = _tx_stock_symbol(code)
    df = ak.stock_zh_a_hist_tx(
        symbol=symbol, start_date=start_date,
        end_date=datetime.now().strftime('%Y%m%d'))
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df


@st.cache_data(ttl=7200)
def get_market_pe_pb() -> pd.DataFrame:
    '''全市场 PE/PB 估值数据'''
    import akshare as ak
    return ak.stock_a_ttm_lyr()


@st.cache_data(ttl=3600)
def get_stock_hot_rank() -> pd.DataFrame:
    '''热门个股排名 (东方财富)'''
    try:
        import akshare as ak
        return ak.stock_hot_rank_em()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_stock_xstp_rank() -> pd.DataFrame:
    '''向上突破排名 (同花顺)'''
    try:
        import akshare as ak
        return ak.stock_rank_xstp_ths(symbol='向上突破')
    except Exception:
        return pd.DataFrame()


# ── 公募基金 ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_mutual_fund_list() -> pd.DataFrame:
    '''公募基金列表'''
    import akshare as ak
    df = ak.fund_name_em()
    df = df.rename(columns={
        '基金代码': 'code', '基金名称': 'name',
        '基金类型': 'category', '拼音缩写': 'pinyin',
    })
    keep = [c for c in ['code', 'name', 'category', 'pinyin'] if c in df.columns]
    return df[keep]


@st.cache_data(ttl=1800, show_spinner=False)
def get_mutual_fund_nav_history(code: str, start_date: str) -> pd.DataFrame:
    '''单只公募基金历史净值'''
    import akshare as ak
    df = ak.fund_open_fund_info_em(
        symbol=code, indicator='单位净值走势', period='')
    df = df.rename(columns={
        '净值日期': 'date', '单位净值': 'nav',
    })
    # Keep date and nav columns
    keep = ['date'] + [c for c in df.columns if c != 'date']
    df = df[[c for c in keep if c in df.columns]]
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    start_dt = pd.to_datetime(start_date)
    return df[df['date'] >= start_dt]


@st.cache_data(ttl=3600)
def get_mutual_fund_rank() -> pd.DataFrame:
    '''公募基金全部排名'''
    import akshare as ak
    return ak.fund_open_fund_rank_em(symbol='全部')


@st.cache_data(ttl=1800)
def get_mutual_fund_daily() -> pd.DataFrame:
    '''公募基金当日净值'''
    import akshare as ak
    return ak.fund_open_fund_daily_em()


# ── 美股 ETF (yfinance) ─────────────────────────────────

US_ETF_PRESETS = {
    'SPY':  '标普500 ETF',
    'QQQ':  '纳斯达克100 ETF',
    'IWM':  '罗素2000 ETF',
    'DIA':  '道琼斯工业 ETF',
    'XLF':  '金融板块 ETF',
    'XLK':  '科技板块 ETF',
    'XLV':  '医疗保健 ETF',
    'XLE':  '能源板块 ETF',
    'XLI':  '工业板块 ETF',
    'XLY':  '可选消费 ETF',
    'EEM':  '新兴市场 ETF',
    'EFA':  '发达市场(除美国) ETF',
    'TLT':  '20年+美债 ETF',
    'AGG':  '综合债券 ETF',
    'GLD':  '黄金 ETF',
    'VWO':  '先锋新兴市场 ETF',
    'VEA':  '先锋发达市场 ETF',
    'VNQ':  '房地产 ETF',
    'SOXX': '半导体 ETF',
    'SMH':  '费城半导体 ETF',
}


@st.cache_data(ttl=3600)
def get_us_etf_list() -> pd.DataFrame:
    '''美股 ETF 预设列表'''
    return pd.DataFrame([
        {'code': k, 'name': f'{k} - {v}'}
        for k, v in US_ETF_PRESETS.items()
    ])


@st.cache_data(ttl=1800, show_spinner=False)
def get_us_etf_hist(symbol: str, period: str = '1y') -> pd.DataFrame:
    '''美股 ETF 历史数据 (yfinance)'''
    import time
    import yfinance as yf
    for attempt in range(2):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            break
        except Exception:
            if attempt < 1:
                time.sleep(3)
            else:
                return pd.DataFrame()
    if df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    df = df.rename(columns={
        'Date': 'date', 'Open': 'open', 'High': 'high',
        'Low': 'low', 'Close': 'close', 'Volume': 'volume',
    })
    df['date'] = pd.to_datetime(df['date'])
    keep = [c for c in ['date', 'open', 'high', 'low', 'close', 'volume']
            if c in df.columns]
    return df[keep]
