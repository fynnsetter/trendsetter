import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import os
import json
import re
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from agents import TechnicalAgent, FundamentalAgent, SentimentAgent, Orchestrator

load_dotenv()

st.set_page_config(
    page_title="TrendSetter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# SESSION STATE
# =====================================================
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "NVDA"

# =====================================================
# WATCHLIST FUNCTIONS
# =====================================================

WATCHLIST_FILE = 'watchlist.json'

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                return json.load(f)
        except:
            return ["NVDA", "AAPL", "GOOGL", "TSLA"]
    return ["NVDA", "AAPL", "GOOGL", "TSLA"]

def save_watchlist(wlist):
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(wlist, f)

# =====================================================
# GOOGLE FONTS + CUSTOM CSS
# =====================================================

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@700;900&family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
    /* Font variables */
    :root {
        --font-logo: 'Merriweather', serif;
        --font-body: 'Montserrat', sans-serif;
        --primary: #00D4AA;
        --secondary: #1A1A2E;
        --text-light: #CCD6F6;
        --text-muted: #8892B0;
        --border-color: #233;
    }
    
    /* Logo styling */
    .logo-text {
        font-family: 'Merriweather', serif;
        font-weight: 900;
        font-size: 2.2rem;
        color: #00D4AA;
        text-align: center;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .logo-sub {
        font-family: 'Montserrat', sans-serif;
        font-weight: 300;
        font-size: 0.75rem;
        color: #8892B0;
        text-align: center;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-top: 2px;
    }
    
    /* Sidebar logo */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0.5rem 0 0.25rem 0;
        margin-left: -4px;
    }
    .sidebar-logo-icon {
        font-size: 1.5rem;
    }
    .sidebar-logo-text {
        font-family: 'Merriweather', serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: #00D4AA;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .sidebar-logo-sub {
        font-family: 'Montserrat', sans-serif;
        font-weight: 300;
        font-size: 0.5rem;
        color: #8892B0;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: -2px;
    }
    
    /* Cards */
    .metric-card {
        background: #1A1A2E;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #233;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #00D4AA;
        transform: translateY(-2px);
    }
    .metric-value {
        font-family: 'Merriweather', serif;
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .metric-label {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.7rem;
        color: #8892B0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Agent cards */
    .agent-card {
        background: #1A1A2E;
        padding: 1rem;
        border-radius: 10px;
        border-left: 3px solid #00D4AA;
        height: 100%;
        transition: all 0.3s ease;
    }
    .agent-card:hover {
        border-color: #00D4AA;
    }
    .agent-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    .agent-score {
        font-family: 'Merriweather', serif;
        font-size: 1.2rem;
        font-weight: 700;
    }
    .agent-explain {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.85rem;
        color: #CCD6F6;
        line-height: 1.5;
    }
    .agent-reasons {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.75rem;
        color: #8892B0;
        margin-top: 0.5rem;
    }
    
    /* Status indicators */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-dot.active { background: #00D4AA; }
    .status-dot.inactive { background: #EB5757; }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #8892B0;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.8rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #233;
        margin-top: 2rem;
    }
    
    /* Tabs - Rounded rectangle style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #1A1A2E;
        padding: 0.5rem;
        border-radius: 12px;
        border: 1px solid #233;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Montserrat', sans-serif;
        color: #8892B0;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
        border-radius: 8px;
        background-color: transparent;
        transition: all 0.2s ease;
        border: none !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #CCD6F6;
        background-color: rgba(255,255,255,0.05);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #00D4AA;
        background-color: #233;
        border: none !important;
    }
    
    .holding-card {
        background: #1A1A2E;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #233;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    .holding-card:hover {
        border-color: #00D4AA;
    }
    .scanner-card {
        background: #1A1A2E;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #233;
        margin-bottom: 0.5rem;
    }
    .positive { color: #00D4AA; }
    .negative { color: #EB5757; }
    
    /* Quick stats row */
    .stat-item {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0 0.25rem;
        background: #1A1A2E;
        border-radius: 8px;
        border: 1px solid #233;
        text-align: center;
        min-width: 80px;
    }
    .stat-value {
        font-weight: 700;
        color: #FFFFFF;
        font-size: 1rem;
    }
    .stat-label {
        font-size: 0.6rem;
        color: #8892B0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

popular_stocks = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc.",
    "NVDA": "NVIDIA Corp.", "AMZN": "Amazon.com Inc.", "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.", "JPM": "JPMorgan Chase & Co.", "VTI": "Vanguard Total Stock Market",
    "SPY": "S&P 500 ETF", "VOO": "Vanguard S&P 500 ETF", "QQQ": "Invesco QQQ Trust",
    "BRK.B": "Berkshire Hathaway", "UNH": "UnitedHealth Group", "XOM": "Exxon Mobil Corp.",
    "JNJ": "Johnson & Johnson", "WMT": "Walmart Inc.", "PG": "Procter & Gamble",
    "MA": "Mastercard Inc.", "HD": "Home Depot Inc.", "BAC": "Bank of America",
    "DIS": "Walt Disney Co.", "NFLX": "Netflix Inc.", "ADBE": "Adobe Inc.",
    "AMD": "Advanced Micro Devices", "INTC": "Intel Corp.", "PFE": "Pfizer Inc.",
    "COST": "Costco Wholesale", "CVX": "Chevron Corp.", "MRK": "Merck & Co.",
    "ABBV": "AbbVie Inc.", "NKE": "Nike Inc.", "MCD": "McDonald's Corp.",
    "F": "Ford Motor Co.", "GM": "General Motors Co.", "BA": "Boeing Co.",
    "UBER": "Uber Technologies Inc.", "LYFT": "Lyft Inc.", "RIVN": "Rivian Automotive Inc."
}

PORTFOLIO_FILE = 'portfolio_data.json'

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    return {'holdings': [], 'cash': 10000, 'transactions': []}

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=2)

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d')
        if not data.empty:
            return data['Close'].iloc[-1]
    except:
        return None
    return None

def calc_rsi(data, window=14):
    if len(data) < window:
        return 50
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    if loss.iloc[-1] == 0:
        return 50
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    if pd.isna(rsi.iloc[-1]):
        return 50
    return rsi.iloc[-1]

def safe_get_price(data, index):
    try:
        if len(data) > abs(index):
            return data.iloc[index]
        return data.iloc[-1] if len(data) > 0 else 0
    except:
        return data.iloc[-1] if len(data) > 0 else 0

def get_earnings_calendar(ticker):
    try:
        stock = yf.Ticker(ticker)
        earnings = stock.earnings_dates
        if earnings is not None and not earnings.empty:
            future_earnings = earnings[earnings.index > datetime.now()]
            if not future_earnings.empty:
                next_earnings = future_earnings.index[0]
                return next_earnings
        return None
    except:
        return None

def get_earnings_estimate(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'next_earnings': info.get('earningsDate', None),
            'eps_estimate': info.get('epsEstimate', None),
        }
    except:
        return {}

# =====================================================
# LOGO (centered at top)
# =====================================================

st.markdown("""
<div style="text-align:center;padding:0.5rem 0 0.25rem 0;">
    <div class="logo-text">TrendSetter</div>
    <div class="logo-sub">AI-Powered Investment Research</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR - SIMPLIFIED WATCHLIST
# =====================================================

watchlist = load_watchlist()

with st.sidebar:
    # Sidebar logo
    st.markdown("""
    <div class="sidebar-logo">
        <span class="sidebar-logo-icon">📊</span>
        <div>
            <div class="sidebar-logo-text">TrendSetter</div>
            <div class="sidebar-logo-sub">AI-Powered Research</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🔍 Search")
    
    # Simple search - just sets the ticker directly
    search_input = st.text_input("", placeholder="Type ticker...", label_visibility="collapsed", key="stock_search")
    
    if search_input:
        # Directly set the ticker to what they typed
        st.session_state.selected_ticker = search_input.upper()
        ticker = search_input.upper()
        st.caption(f"📌 Using: {ticker}")
    else:
        # No search - use the selected ticker from watchlist or default
        ticker = st.session_state.selected_ticker if st.session_state.selected_ticker else "NVDA"
        st.caption(f"📌 Current: {ticker}")
    
    st.markdown("---")
    
    st.markdown("### ⏱️ Time Period")
    timeframe_options = {
        "1 Day": "1d",
        "1 Week": "5d",
        "1 Month": "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year": "1y",
        "2 Years": "2y",
        "5 Years": "5y",
        "Multi-Timeframe (AI)": "multi"
    }
    period_label = st.selectbox("", list(timeframe_options.keys()), index=5, label_visibility="collapsed")
    period = timeframe_options[period_label]
    
    st.markdown("---")
    
    st.markdown("### ⭐ Watchlist")
    
    # SIMPLE WATCHLIST - click a button, it sets the ticker
    if watchlist:
        for wt in watchlist:
            is_active = (wt == st.session_state.selected_ticker)
            # Highlight the active one
            label = f"▶ {wt}" if is_active else wt
            if st.button(label, key=f"watch_{wt}", use_container_width=True):
                st.session_state.selected_ticker = wt
                st.rerun()
    
    add_to_watch = st.text_input("", placeholder="Add ticker...", key="add_watch", label_visibility="collapsed")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add", use_container_width=True):
            if add_to_watch and add_to_watch.upper() not in watchlist:
                watchlist.append(add_to_watch.upper())
                save_watchlist(watchlist)
                st.rerun()
    with col2:
        if st.button("🗑️ Remove", use_container_width=True):
            if add_to_watch and add_to_watch.upper() in watchlist:
                watchlist.remove(add_to_watch.upper())
                save_watchlist(watchlist)
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🤖 AI Agents")
    st.markdown("""
    <div style="display:flex;flex-direction:column;gap:4px;font-size:0.85rem;">
        <div><span class="status-dot active"></span> <span style="color:#8892B0;">Technical</span> <span style="color:#00D4AA;float:right;">Active</span></div>
        <div><span class="status-dot active"></span> <span style="color:#8892B0;">Fundamental</span> <span style="color:#00D4AA;float:right;">Active</span></div>
        <div><span class="status-dot active"></span> <span style="color:#8892B0;">Sentiment</span> <span style="color:#00D4AA;float:right;">Active</span></div>
        <div><span class="status-dot active"></span> <span style="color:#8892B0;">Orchestrator</span> <span style="color:#00D4AA;float:right;">Active</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    api_status = "✅" if os.getenv('ANTHROPIC_API_KEY') else "❌"
    news_status = "✅" if os.getenv('NEWS_API_KEY') else "❌"
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;gap:2px;font-size:0.75rem;color:#8892B0;">
        <div>API: {api_status} Claude • {news_status} News</div>
        <div>📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("⚠️ Educational purposes only.")

# =====================================================
# DATA FETCHING
# =====================================================

@st.cache_data(ttl=3600)
def fetch_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        info = stock.info
        return data, info
    except Exception as e:
        return pd.DataFrame(), {}

# Use the ticker from session state OR search
# The search box already sets st.session_state.selected_ticker
if 'ticker' not in locals():
    ticker = st.session_state.selected_ticker if st.session_state.selected_ticker else "NVDA"

if period == "multi":
    data, info = fetch_data(ticker, "1y")
else:
    data, info = fetch_data(ticker, period)

if data.empty:
    st.error(f"No data found for {ticker}")
    st.stop()

current_price = data['Close'].iloc[-1]
prev_price = safe_get_price(data['Close'], -2)
change = ((current_price - prev_price) / prev_price * 100) if prev_price != 0 else 0

# =====================================================
# TABS (4 tabs: Analysis, Portfolio, Scanner, Compare)
# =====================================================

tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis", "💼 Portfolio", "🔍 Scanner", "📊 Compare"])

# =====================================================
# TAB 1: ANALYSIS
# =====================================================

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Company</div><div class="metric-value" style="font-size:1.1rem;">{info.get('longName', ticker)}</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Sector</div><div class="metric-value" style="font-size:1.1rem;">{info.get('sector', 'Unknown')}</div></div>""", unsafe_allow_html=True)
    with col3:
        change_color = "#00D4AA" if change >= 0 else "#EB5757"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Price</div><div class="metric-value">${current_price:.2f}</div><div style="color:{change_color};font-weight:600;">{change:+.2f}%</div></div>""", unsafe_allow_html=True)
    with col4:
        market_cap = info.get('marketCap', 0)
        cap_str = f"${market_cap/1e12:.2f}T" if market_cap > 1e12 else f"${market_cap/1e9:.2f}B" if market_cap > 1e9 else f"${market_cap/1e6:.2f}M"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Market Cap</div><div class="metric-value" style="font-size:1.1rem;">{cap_str}</div></div>""", unsafe_allow_html=True)
    
    # =====================================================
    # PRICE CHART
    # =====================================================
    st.markdown("### 📊 Price Chart")
    chart_type = st.radio("Chart Type", ["Line", "Candlestick"], horizontal=True, index=0)
    
    if len(data) < 2:
        st.info("📊 Not enough data points for a chart with this time period. Try selecting a longer time period (1 Month or more).")
    else:
        if chart_type == "Line":
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close', line=dict(color='#00D4AA', width=2)))
            if len(data) >= 50:
                fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(50).mean(), mode='lines', name='50-day MA', line=dict(color='#FF6B6B', width=1)))
            if len(data) >= 200:
                fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(200).mean(), mode='lines', name='200-day MA', line=dict(color='#F2C94D', width=1)))
        else:
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Candlestick')])
            if len(data) >= 50:
                fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(50).mean(), mode='lines', name='50-day MA', line=dict(color='#FF6B6B', width=1)))
            if len(data) >= 200:
                fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(200).mean(), mode='lines', name='200-day MA', line=dict(color='#F2C94D', width=1)))
        
        fig.update_layout(height=450, template='plotly_dark', margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
        st.plotly_chart(fig, use_container_width=True)
    
    # =====================================================
    # TECHNICAL INDICATORS
    # =====================================================
    st.markdown("### 📊 Technical Indicators")
    returns = data['Close'].pct_change()
    volatility = returns.std() * (252 ** 0.5)
    rsi = calc_rsi(data['Close'])
    ma_50 = data['Close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else current_price
    ma_200 = data['Close'].rolling(200).mean().iloc[-1] if len(data) >= 200 else current_price
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = (macd - macd_signal).iloc[-1]
    
    # Volume Analysis
    avg_volume = data['Volume'].rolling(20).mean().iloc[-1] if len(data) >= 20 else data['Volume'].mean()
    current_volume = data['Volume'].iloc[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        rsi_color = "#00D4AA" if 30 < rsi < 70 else "#F2C94D" if rsi < 30 else "#EB5757"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">RSI</div><div class="metric-value" style="color:{rsi_color};">{rsi:.1f}</div><div style="font-size:0.7rem;color:#8892B0;">{'Oversold' if rsi < 30 else 'Overbought' if rsi > 70 else 'Neutral'}</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Volatility</div><div class="metric-value">{volatility*100:.1f}%</div><div style="font-size:0.7rem;color:#8892B0;">Annualized</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">50-day MA</div><div class="metric-value">${ma_50:.2f}</div><div style="font-size:0.7rem;color:#8892B0;">{'Above' if current_price > ma_50 else 'Below'} price</div></div>""", unsafe_allow_html=True)
    with col4:
        macd_color = "#00D4AA" if macd_hist > 0 else "#EB5757"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">MACD</div><div class="metric-value" style="color:{macd_color};">{macd_hist:.3f}</div><div style="font-size:0.7rem;color:#8892B0;">{'Bullish' if macd_hist > 0 else 'Bearish'}</div></div>""", unsafe_allow_html=True)
    
    # Volume Analysis Row
    volume_color = "#00D4AA" if volume_ratio > 1.2 else "#F2C94D" if volume_ratio > 0.8 else "#8892B0"
    volume_text = "Above Average" if volume_ratio > 1.2 else "Average" if volume_ratio > 0.8 else "Below Average"
    st.markdown(f"""
    <div style="background:#1A1A2E;padding:0.75rem 1rem;border-radius:10px;border:1px solid #233;margin-top:0.5rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="color:#8892B0;">📊 Volume</span>
            <span style="color:{volume_color};font-weight:600;">{current_volume:,.0f} ({volume_text})</span>
            <span style="color:#8892B0;font-size:0.8rem;">Avg: {avg_volume:,.0f}</span>
            <span style="color:{volume_color};">{volume_ratio:.1f}x average</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # =====================================================
    # AI AGENT ANALYSIS
    # =====================================================
    st.markdown("---")
    st.markdown("### 🤖 AI Agent Analysis")
    
    indicators = {'rsi': rsi, 'ma_50': ma_50, 'ma_200': ma_200, 'macd_hist': macd_hist, 'volatility': volatility, 'current_price': current_price}
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        st.warning("Claude API key not found. Add to .env file.")
    else:
        with st.spinner("AI agents analyzing..."):
            try:
                tech_agent = TechnicalAgent()
                fund_agent = FundamentalAgent()
                sent_agent = SentimentAgent()
                orchestrator = Orchestrator()
                
                tech_result = tech_agent.analyze(ticker, indicators)
                fund_result = fund_agent.analyze(ticker, info)
                sent_result = sent_agent.analyze(ticker)
                final_result = orchestrator.analyze(ticker, tech_result, fund_result, sent_result)
                
                score = final_result['total_score']
                if score >= 6:
                    signal_text = f"STRONG BUY (+{score})"
                    color = "#00D4AA"
                elif score >= 3:
                    signal_text = f"BUY (+{score})"
                    color = "#6FCF97"
                elif score >= 0:
                    signal_text = f"HOLD ({score:+.0f})"
                    color = "#F2C94D"
                elif score >= -3:
                    signal_text = f"SELL/REDUCE ({score:+.0f})"
                    color = "#F2994A"
                else:
                    signal_text = f"STRONG SELL ({score:+.0f})"
                    color = "#EB5757"
                
                st.markdown(f"""<div style="background:#1A1A2E;padding:1.5rem;border-radius:12px;border:2px solid {color};text-align:center;margin:1rem 0;"><div style="color:{color};font-size:2rem;font-weight:700;">{signal_text}</div><div style="color:#8892B0;">Confidence: {final_result['confidence']:.0f}%</div><div style="color:#CCD6F6;margin-top:0.5rem;">{final_result['summary']}</div></div>""", unsafe_allow_html=True)
                
                st.markdown("### Agent Breakdown")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    tech_color = "#00D4AA" if tech_result['score'] > 0 else "#EB5757" if tech_result['score'] < 0 else "#F2C94D"
                    st.markdown(f"""<div class="agent-card" style="border-left-color:{tech_color};"><div class="agent-title">🔵 Technical</div><div class="agent-score" style="color:{tech_color};">Score: {tech_result['score']:+d}</div><div class="agent-explain">{tech_result['explanation']}</div></div>""", unsafe_allow_html=True)
                
                with col2:
                    fund_color = "#00D4AA" if fund_result['score'] > 0 else "#EB5757" if fund_result['score'] < 0 else "#F2C94D"
                    st.markdown(f"""<div class="agent-card" style="border-left-color:{fund_color};"><div class="agent-title">🟢 Fundamental</div><div class="agent-score" style="color:{fund_color};">Score: {fund_result['score']:+d}</div><div class="agent-explain">{fund_result['explanation']}</div></div>""", unsafe_allow_html=True)
                
                with col3:
                    sent_color = "#00D4AA" if sent_result['score'] > 0 else "#EB5757" if sent_result['score'] < 0 else "#F2C94D"
                    st.markdown(f"""<div class="agent-card" style="border-left-color:{sent_color};"><div class="agent-title">🟡 Sentiment</div><div class="agent-score" style="color:{sent_color};">Score: {sent_result['score']:+d}</div><div class="agent-explain">{sent_result['explanation']}</div></div>""", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"AI Agents error: {str(e)}")
    
    # =====================================================
    # POSITION SIZING - FORCED WHITE TEXT (FIXED)
    # =====================================================
    st.markdown("---")
    st.markdown("### 💰 Position Sizing")

    portfolio = load_portfolio()
    total_cash = portfolio['cash']
    total_holdings_value = 0
    for h in portfolio['holdings']:
        price = get_stock_price(h['ticker'])
        if price:
            total_holdings_value += h['shares'] * price

    total_capital = total_cash + total_holdings_value

    # Inline span forces pure white text, normal size – overrides any green
    st.markdown(
        f'<span style="color: #FFFFFF; font-size: 1rem;">💰 Your total capital: ${total_capital:,.2f} (Cash: ${total_cash:,.2f} + Holdings: ${total_holdings_value:,.2f})</span>',
        unsafe_allow_html=True
    )

    if period == "multi":
        st.info("🧠 Analyzing multiple timeframes for stronger signal...")
        
        periods_to_analyze = [
            ("1 Month", "1mo"),
            ("3 Months", "3mo"),
            ("1 Year", "1y")
        ]
        
        scores = []
        signals = []
        valid_analyses = 0
        
        for name, p in periods_to_analyze:
            try:
                temp_stock = yf.Ticker(ticker)
                temp_data = temp_stock.history(period=p)
                
                if temp_data.empty:
                    signals.append(f"**{name}:** No data available")
                    continue
                
                if len(temp_data) < 5:
                    signals.append(f"**{name}:** Not enough data points")
                    continue
                
                temp_close = temp_data['Close']
                temp_price = temp_close.iloc[-1]
                
                temp_rsi = calc_rsi(temp_close)
                
                if len(temp_data) >= 50:
                    temp_ma_50 = temp_close.rolling(50).mean().iloc[-1]
                else:
                    temp_ma_50 = temp_price
                
                if len(temp_data) >= 200:
                    temp_ma_200 = temp_close.rolling(200).mean().iloc[-1]
                else:
                    temp_ma_200 = temp_price
                
                temp_exp1 = temp_close.ewm(span=12, adjust=False).mean()
                temp_exp2 = temp_close.ewm(span=26, adjust=False).mean()
                temp_macd = (temp_exp1 - temp_exp2).iloc[-1]
                
                temp_score = 0
                temp_signals = []
                
                if temp_price > temp_ma_50:
                    temp_score += 1
                    temp_signals.append("Above 50-day MA")
                else:
                    temp_score -= 1
                    temp_signals.append("Below 50-day MA")
                
                if temp_price > temp_ma_200:
                    temp_score += 1
                    temp_signals.append("Above 200-day MA")
                else:
                    temp_score -= 1
                    temp_signals.append("Below 200-day MA")
                
                if temp_rsi < 30:
                    temp_score += 2
                    temp_signals.append("RSI oversold")
                elif temp_rsi > 70:
                    temp_score -= 2
                    temp_signals.append("RSI overbought")
                else:
                    temp_signals.append("RSI neutral")
                
                if temp_macd > 0:
                    temp_score += 1
                    temp_signals.append("MACD bullish")
                else:
                    temp_score -= 1
                    temp_signals.append("MACD bearish")
                
                scores.append(temp_score)
                signals.append(f"**{name}:** Score {temp_score:+d} - {', '.join(temp_signals[:3])}")
                valid_analyses += 1
                
            except Exception as e:
                signals.append(f"**{name}:** Error - {str(e)[:30]}")
        
        if scores and valid_analyses > 0:
            avg_score = sum(scores) / len(scores)
            position_pct = 0
            if avg_score >= 3:
                position_pct = 15
            elif avg_score >= 1.5:
                position_pct = 10
            elif avg_score >= 0:
                position_pct = 5
            
            st.markdown("#### 📊 Multi-Timeframe Breakdown")
            for signal in signals:
                st.caption(signal)
            
            st.markdown(f"**Average Score:** {avg_score:+.1f} (based on {valid_analyses} timeframes)")
            
            if position_pct > 0:
                invest = total_capital * (position_pct / 100)
                shares = invest / current_price if current_price > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""<div class="metric-card"><div class="metric-label">Position Size</div><div class="metric-value">{position_pct}%</div><div style="font-size:0.8rem;color:#8892B0;">of ${total_capital:,.2f} capital</div></div>""", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""<div class="metric-card"><div class="metric-label">Invest</div><div class="metric-value">${invest:,.2f}</div><div style="font-size:0.8rem;color:#8892B0;">at ${current_price:.2f}</div></div>""", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""<div class="metric-card"><div class="metric-label">Shares</div><div class="metric-value">{shares:.2f}</div><div style="font-size:0.8rem;color:#8892B0;">{ticker} shares</div></div>""", unsafe_allow_html=True)
            else:
                st.info("⏳ Mixed signals across timeframes - wait for clearer direction")
        else:
            st.info("⏳ Not enough data for multi-timeframe analysis. Try selecting a single timeframe instead.")

    else:
        if 'final_result' in locals():
            position_pct = final_result.get('position_pct', 0)
        else:
            position_pct = 0

        if position_pct > 0:
            invest = total_capital * (position_pct / 100)
            shares = invest / current_price if current_price > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Position Size</div><div class="metric-value">{position_pct}%</div><div style="font-size:0.8rem;color:#8892B0;">of ${total_capital:,.2f} capital</div></div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Invest</div><div class="metric-value">${invest:,.2f}</div><div style="font-size:0.8rem;color:#8892B0;">at ${current_price:.2f}</div></div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Shares</div><div class="metric-value">{shares:.2f}</div><div style="font-size:0.8rem;color:#8892B0;">{ticker} shares</div></div>""", unsafe_allow_html=True)
            
            if volatility > 0.35:
                stop_loss = current_price * 0.80
                loss_pct = -20
            elif volatility > 0.25:
                stop_loss = current_price * 0.85
                loss_pct = -15
            else:
                stop_loss = current_price * 0.90
                loss_pct = -10
            
            st.markdown(f"""
            <div style="background:#1A1A2E;padding:1rem;border-radius:10px;margin-top:0.5rem;display:flex;justify-content:space-between;">
                <div><span style="color:#8892B0;">Stop Loss:</span> <strong>${stop_loss:.2f}</strong></div>
                <div><span style="color:#8892B0;">Risk:</span> <strong style="color:#EB5757;">{loss_pct}%</strong></div>
                <div><span style="color:#8892B0;">Take Profit:</span> <strong style="color:#00D4AA;">${current_price * 1.15:.2f} (+15%)</strong></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("⏳ Wait for a stronger signal before entering a position.")
    
    # =====================================================
    # QUICK STATS & EARNINGS CALENDAR (BOTTOM)
    # =====================================================
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    
    pe_ratio = info.get('trailingPE', 'N/A')
    eps = info.get('trailingEps', 'N/A')
    dividend_yield = info.get('dividendYield', None)
    if dividend_yield:
        dividend_yield = f"{dividend_yield * 100:.2f}%"
    else:
        dividend_yield = "N/A"
    
    high_52w = info.get('fiftyTwoWeekHigh', current_price)
    low_52w = info.get('fiftyTwoWeekLow', current_price)
    from_high = ((high_52w - current_price) / high_52w * 100) if high_52w else 0
    from_low = ((current_price - low_52w) / low_52w * 100) if low_52w else 0
    
    stats_html = f"""
    <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
        <div class="stat-item">
            <div class="stat-label">P/E Ratio</div>
            <div class="stat-value">{pe_ratio if pe_ratio != 'N/A' else '—'}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">EPS</div>
            <div class="stat-value">${eps if eps != 'N/A' else '—'}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Dividend Yield</div>
            <div class="stat-value">{dividend_yield}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">52W High</div>
            <div class="stat-value">${high_52w:.2f}</div>
            <div style="font-size:0.6rem;color:#EB5757;">-{from_high:.1f}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">52W Low</div>
            <div class="stat-value">${low_52w:.2f}</div>
            <div style="font-size:0.6rem;color:#00D4AA;">+{from_low:.1f}%</div>
        </div>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)
    
    # Earnings Calendar
    st.markdown("### 📅 Earnings Calendar")
    
    earnings_date = get_earnings_calendar(ticker)
    earnings_estimates = get_earnings_estimate(ticker)
    
    if earnings_date:
        days_until = (earnings_date - datetime.now()).days
        if days_until > 0:
            st.info(f"📊 Next earnings: **{earnings_date.strftime('%B %d, %Y')}** ({days_until} days away)")
        else:
            st.info(f"📊 Next earnings: **{earnings_date.strftime('%B %d, %Y')}** (Today!)")
        
        if earnings_estimates.get('eps_estimate'):
            st.caption(f"EPS Estimate: ${earnings_estimates['eps_estimate']:.2f}")
    else:
        st.caption("📊 No upcoming earnings date available")

# =====================================================
# TAB 2: PORTFOLIO
# =====================================================

with tab2:
    st.markdown("### 💼 Portfolio Tracker")
    
    portfolio = load_portfolio()
    
    total_value = 0
    total_cost = 0
    
    for h in portfolio['holdings']:
        price = get_stock_price(h['ticker'])
        if price:
            h['current_price'] = price
            total_value += h['shares'] * price
            total_cost += h['shares'] * h['avg_price']
    
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Portfolio Value</div><div class="metric-value">${total_value:,.2f}</div></div>""", unsafe_allow_html=True)
    with col2:
        pnl_color = "#00D4AA" if total_pnl >= 0 else "#EB5757"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Total P&L</div><div class="metric-value" style="color:{pnl_color};">${total_pnl:+,.2f}</div><div style="color:{pnl_color};">{total_pnl_pct:+.1f}%</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Cash</div><div class="metric-value">${portfolio['cash']:,.2f}</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Total Capital</div><div class="metric-value">${total_value + portfolio['cash']:,.2f}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 💰 Cash Management")
    
    col1, col2 = st.columns(2)
    with col1:
        deposit_amount = st.number_input("Deposit ($)", min_value=0.01, value=1000.0, step=100.0, key="deposit")
        if st.button("💰 Deposit", type="primary"):
            portfolio['cash'] += deposit_amount
            portfolio['transactions'].append({'type': 'DEPOSIT', 'amount': deposit_amount, 'date': datetime.now().strftime('%Y-%m-%d %H:%M')})
            save_portfolio(portfolio)
            st.success(f"Deposited ${deposit_amount:,.2f}")
            st.rerun()
    
    with col2:
        withdraw_amount = st.number_input("Withdraw ($)", min_value=0.01, value=100.0, step=100.0, key="withdraw")
        if st.button("🏦 Withdraw", type="secondary"):
            if withdraw_amount > portfolio['cash']:
                st.error(f"Insufficient cash. Available: ${portfolio['cash']:,.2f}")
            else:
                portfolio['cash'] -= withdraw_amount
                portfolio['transactions'].append({'type': 'WITHDRAWAL', 'amount': withdraw_amount, 'date': datetime.now().strftime('%Y-%m-%d %H:%M')})
                save_portfolio(portfolio)
                st.success(f"Withdrew ${withdraw_amount:,.2f}")
                st.rerun()
    
    st.markdown("---")
    st.markdown("### ➕ Add Holding")
    
    col1, col2 = st.columns(2)
    
    with col1:
        add_ticker = st.selectbox("Ticker", list(popular_stocks.keys()), key="add_ticker")
        current_price = get_stock_price(add_ticker)
        if current_price:
            st.caption(f"Current market price: ${current_price:.2f}")
        
        input_method = st.radio("Enter by:", ["Shares", "Amount ($)"], horizontal=True, key="input_method")
        
        if input_method == "Shares":
            add_shares = st.number_input("Number of Shares", min_value=0.01, value=1.0, step=0.5, key="add_shares")
            if current_price:
                add_price = current_price
                add_amount = add_shares * add_price
                st.caption(f"Total cost: ${add_amount:,.2f}")
            else:
                add_price = st.number_input("Buy Price ($)", min_value=0.01, value=100.0, step=0.5, key="add_price")
                add_amount = add_shares * add_price
        else:
            add_amount = st.number_input("Amount to Invest ($)", min_value=0.01, value=1000.0, step=100.0, key="add_amount")
            if current_price:
                add_price = current_price
                add_shares = add_amount / add_price
                st.caption(f"Shares: {add_shares:.2f}")
            else:
                add_price = st.number_input("Buy Price ($)", min_value=0.01, value=100.0, step=0.5, key="add_price")
                add_shares = add_amount / add_price
        
        if st.button("Add to Portfolio", type="primary"):
            if add_amount > portfolio['cash']:
                st.error(f"Insufficient cash! Available: ${portfolio['cash']:,.2f}")
            else:
                existing = False
                for h in portfolio['holdings']:
                    if h['ticker'] == add_ticker:
                        total_shares = h['shares'] + add_shares
                        total_cost = (h['shares'] * h['avg_price']) + (add_shares * add_price)
                        h['avg_price'] = total_cost / total_shares
                        h['shares'] = total_shares
                        existing = True
                        break
                
                if not existing:
                    portfolio['holdings'].append({
                        'ticker': add_ticker,
                        'shares': add_shares,
                        'avg_price': add_price,
                        'date_added': datetime.now().strftime('%Y-%m-%d')
                    })
                
                portfolio['cash'] -= add_amount
                portfolio['transactions'].append({
                    'type': 'BUY',
                    'ticker': add_ticker,
                    'shares': add_shares,
                    'price': add_price,
                    'amount': add_amount,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
                
                save_portfolio(portfolio)
                st.success(f"Added {add_shares:.2f} shares of {add_ticker} at ${add_price:.2f}")
                st.rerun()
    
    with col2:
        st.markdown("### ➖ Remove Holding")
        
        if portfolio['holdings']:
            holding_options = []
            for h in portfolio['holdings']:
                price = get_stock_price(h['ticker'])
                if price:
                    holding_options.append(f"{h['ticker']} ({h['shares']:.2f} shares @ ${price:.2f})")
                else:
                    holding_options.append(f"{h['ticker']} ({h['shares']:.2f} shares)")
            
            if holding_options:
                selected_holding = st.selectbox("Select holding to sell", holding_options)
                selected_ticker = selected_holding.split(" ")[0]
                
                sell_holding = None
                for h in portfolio['holdings']:
                    if h['ticker'] == selected_ticker:
                        sell_holding = h
                        break
                
                if sell_holding:
                    current_price = get_stock_price(selected_ticker)
                    shares_available = sell_holding['shares']
                    st.caption(f"Shares available: {shares_available:.2f}")
                    if current_price:
                        st.caption(f"Current price: ${current_price:.2f}")
                        st.caption(f"Total value: ${shares_available * current_price:,.2f}")
                    
                    sell_method = st.radio("Sell by:", ["Shares", "Amount ($)"], horizontal=True, key="sell_method")
                    
                    if sell_method == "Shares":
                        sell_shares = st.number_input("Shares to sell", min_value=0.01, max_value=float(shares_available), value=min(1.0, shares_available), step=0.5, key="sell_shares")
                        sell_amount = sell_shares * current_price if current_price else 0
                        if current_price:
                            st.caption(f"Proceeds: ${sell_amount:,.2f}")
                    else:
                        max_sell = shares_available * current_price if current_price else shares_available
                        sell_amount = st.number_input("Amount to sell ($)", min_value=0.01, max_value=float(max_sell), value=min(100.0, float(max_sell)), step=50.0, key="sell_amount")
                        sell_shares = sell_amount / current_price if current_price else 0
                    
                    if st.button("Sell Selected", type="secondary"):
                        if sell_shares > shares_available:
                            st.error(f"Insufficient shares! Available: {shares_available:.2f}")
                        elif sell_shares <= 0:
                            st.error("Please enter a valid number")
                        else:
                            for h in portfolio['holdings']:
                                if h['ticker'] == selected_ticker:
                                    sell_proceeds = sell_shares * current_price if current_price else 0
                                    
                                    if sell_shares >= h['shares']:
                                        portfolio['holdings'].remove(h)
                                        st.info(f"Removed all {h['ticker']} shares")
                                    else:
                                        h['shares'] -= sell_shares
                                    
                                    portfolio['cash'] += sell_proceeds
                                    
                                    portfolio['transactions'].append({
                                        'type': 'SELL',
                                        'ticker': h['ticker'],
                                        'shares': sell_shares,
                                        'price': current_price,
                                        'amount': sell_proceeds,
                                        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
                                    })
                                    
                                    save_portfolio(portfolio)
                                    st.success(f"Sold {sell_shares:.2f} shares of {selected_ticker} for ${sell_proceeds:,.2f}")
                                    st.rerun()
                                    break
        else:
            st.info("No holdings to sell")
    
    st.markdown("---")
    st.markdown("### 📊 Current Holdings")
    
    if portfolio['holdings']:
        for h in portfolio['holdings']:
            current_price = get_stock_price(h['ticker'])
            if current_price:
                value = h['shares'] * current_price
                cost = h['shares'] * h['avg_price']
                pnl = value - cost
                pnl_pct = (pnl / cost * 100) if cost > 0 else 0
                
                pnl_color = "#00D4AA" if pnl >= 0 else "#EB5757"
                
                st.markdown(f"""
                <div class="holding-card" style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <strong style="font-size:1.2rem;">{h['ticker']}</strong>
                        <span style="color:#8892B0;font-size:0.8rem;margin-left:0.5rem;">{h['shares']:.2f} shares</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.1rem;">${value:,.2f}</div>
                        <div style="color:{pnl_color};">{pnl_pct:+.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if len(portfolio['holdings']) > 1:
            fig_pie = px.pie(
                values=[h['shares'] * get_stock_price(h['ticker']) for h in portfolio['holdings']],
                names=[h['ticker'] for h in portfolio['holdings']],
                title='Portfolio Allocation',
                color_discrete_sequence=px.colors.sequential.Tealgrn
            )
            fig_pie.update_layout(template='plotly_dark', height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No holdings yet. Add some stocks above!")
    
    st.markdown("---")
    st.markdown("### 📜 Recent Transactions")
    
    if portfolio.get('transactions'):
        tx_df = pd.DataFrame(portfolio['transactions'][-10:][::-1])
        st.dataframe(tx_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No transactions recorded")

# =====================================================
# TAB 3: SCANNER
# =====================================================

with tab3:
    st.markdown("### 🔍 Opportunity Scanner")
    
    default_watchlist = ["NVDA", "AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA", "JPM"]
    
    st.markdown("#### 📋 Watchlist")
    watchlist_input = st.text_area(
        "Enter stock tickers (one per line)",
        value="\n".join(default_watchlist),
        height=150,
        help="Add stocks you want to scan for opportunities"
    )
    
    scan_list = [t.strip().upper() for t in watchlist_input.split("\n") if t.strip()]
    
    scan_button = st.button("🔍 Scan Watchlist", type="primary")
    
    if scan_button or 'scanned_results' in st.session_state:
        if scan_button:
            st.session_state.scanned_results = None
        
        with st.spinner("Scanning stocks..."):
            results = []
            progress_bar = st.progress(0)
            
            for i, ticker in enumerate(scan_list):
                progress_bar.progress((i + 1) / len(scan_list))
                
                try:
                    temp_data, temp_info = fetch_data(ticker, "1y")
                    if temp_data.empty:
                        continue
                    
                    price = temp_data['Close'].iloc[-1]
                    prev = temp_data['Close'].iloc[-2] if len(temp_data) > 1 else price
                    change = ((price - prev) / prev * 100) if prev != 0 else 0
                    
                    temp_returns = temp_data['Close'].pct_change()
                    temp_volatility = temp_returns.std() * (252 ** 0.5)
                    temp_rsi = calc_rsi(temp_data['Close'])
                    
                    temp_ma_50 = temp_data['Close'].rolling(50).mean().iloc[-1] if len(temp_data) >= 50 else price
                    temp_ma_200 = temp_data['Close'].rolling(200).mean().iloc[-1] if len(temp_data) >= 200 else price
                    
                    score = 0
                    signals = []
                    
                    if price > temp_ma_50:
                        score += 1
                        signals.append("Above 50-day MA")
                    else:
                        score -= 1
                        signals.append("Below 50-day MA")
                    
                    if price > temp_ma_200:
                        score += 1
                        signals.append("Above 200-day MA")
                    else:
                        score -= 1
                        signals.append("Below 200-day MA")
                    
                    if temp_rsi < 30:
                        score += 2
                        signals.append("RSI oversold")
                    elif temp_rsi > 70:
                        score -= 2
                        signals.append("RSI overbought")
                    else:
                        signals.append("RSI neutral")
                    
                    if temp_volatility < 0.20:
                        score += 1
                        signals.append("Low volatility")
                    elif temp_volatility > 0.40:
                        score -= 1
                        signals.append("High volatility")
                    
                    name = temp_info.get('longName', ticker)[:30]
                    
                    results.append({
                        'Ticker': ticker,
                        'Name': name,
                        'Price': price,
                        'Change %': change,
                        'Score': score,
                        'Signals': signals,
                        'RSI': temp_rsi if not pd.isna(temp_rsi) else 50,
                        'Volatility': temp_volatility if not pd.isna(temp_volatility) else 0.25
                    })
                    
                except Exception as e:
                    pass
            
            progress_bar.empty()
            
            results.sort(key=lambda x: x['Score'], reverse=True)
            
            st.markdown("---")
            st.markdown("### 📊 Scan Results")
            
            if results:
                for r in results:
                    if r['Score'] >= 3:
                        signal_emoji = "🟢"
                        signal_text = "Strong Buy"
                        color = "#00D4AA"
                    elif r['Score'] >= 1:
                        signal_emoji = "🟡"
                        signal_text = "Buy"
                        color = "#F2C94D"
                    elif r['Score'] >= -1:
                        signal_emoji = "⚪"
                        signal_text = "Hold"
                        color = "#8892B0"
                    elif r['Score'] >= -3:
                        signal_emoji = "🟠"
                        signal_text = "Reduce"
                        color = "#F2994A"
                    else:
                        signal_emoji = "🔴"
                        signal_text = "Sell"
                        color = "#EB5757"
                    
                    st.markdown(f"""
                    <div class="scanner-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <strong style="font-size:1.1rem;">{r['Ticker']}</strong>
                                <span style="color:#8892B0;font-size:0.8rem;margin-left:0.5rem;">{r['Name']}</span>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:1.1rem;">${r['Price']:.2f}</div>
                                <div style="color:{"#00D4AA" if r['Change %'] >= 0 else "#EB5757"};">{r['Change %']:+.2f}%</div>
                            </div>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-top:0.5rem;">
                            <span style="color:{color};font-weight:600;">{signal_emoji} {signal_text} (Score: {r['Score']:+d})</span>
                            <span style="color:#8892B0;font-size:0.8rem;">RSI: {r['RSI']:.1f} | Vol: {r['Volatility']*100:.1f}%</span>
                        </div>
                        <div style="color:#8892B0;font-size:0.7rem;margin-top:0.3rem;">
                            {', '.join(r['Signals'][:3])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No results found. Try adding different tickers.")

# =====================================================
# TAB 4: COMPARE
# =====================================================

with tab4:
    st.markdown("### 📊 Stock Comparison")
    
    st.markdown("Select up to 5 stocks to compare their performance.")
    
    compare_tickers = st.multiselect(
        "Select stocks to compare",
        options=list(popular_stocks.keys()),
        default=["NVDA", "AAPL", "GOOGL"],
        max_selections=5
    )
    
    if len(compare_tickers) >= 2:
        compare_data = {}
        for t in compare_tickers:
            stock = yf.Ticker(t)
            hist = stock.history(period='1y')
            if not hist.empty:
                compare_data[t] = hist['Close']
        
        if compare_data:
            df = pd.DataFrame(compare_data)
            normalized = df / df.iloc[0] * 100
            
            fig = go.Figure()
            for ticker in normalized.columns:
                fig.add_trace(go.Scatter(
                    x=normalized.index,
                    y=normalized[ticker],
                    mode='lines',
                    name=ticker,
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title="Performance Comparison (1 Year)",
                yaxis_title="% Change",
                height=500,
                template='plotly_dark',
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 📊 Performance Table")
            performance = pd.DataFrame()
            for ticker in compare_data:
                data = compare_data[ticker]
                performance.loc[ticker, 'Current Price'] = f"${data.iloc[-1]:.2f}"
                performance.loc[ticker, '1Y Return (%)'] = f"{((data.iloc[-1] / data.iloc[0]) - 1) * 100:.2f}%"
                performance.loc[ticker, 'High'] = f"${data.max():.2f}"
                performance.loc[ticker, 'Low'] = f"${data.min():.2f}"
                performance.loc[ticker, 'Volatility (%)'] = f"{data.pct_change().std() * 252 * 100:.2f}%"
            
            st.dataframe(performance, use_container_width=True)
        else:
            st.warning("Could not fetch data for selected stocks")
    else:
        st.info("Select at least 2 stocks to compare (max 5)")

# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<div class="footer">
    TrendSetter • AI-Powered Investment Research • For educational purposes only
</div>
""", unsafe_allow_html=True)
