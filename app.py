streamlit
yfinance
pandas
plotly

import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Swing Screener Pro", layout="wide")

st.title("⚡ Dynamic Swing Trading Screener")
st.write("Strategy: **High Volume (1.8x+) + Price Action Breakout / 20-SMA Support**")

# Default High-Beta & Momentum Stock List
DEFAULT_TICKERS = [
    "COCHINSHIP.NS", "BEL.NS", "MAZDOCK.NS", "RVNL.NS", "DIXON.NS", 
    "PARAS.NS", "DATAPATTNS.NS", "SAVITA.NS", "TRENT.NS", "KAYNES.NS", 
    "HAL.NS", "ZENTEC.NS", "63MOONS.NS"
]

@st.cache_data(ttl=300)
def fetch_stock_data(tickers):
    screened_data = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                continue
            
            # Formatting DataFrame columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Calculations
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            df['VolSMA20'] = df['Volume'].rolling(window=20).mean()

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            ltp = round(float(latest['Close']), 2)
            high_20d = round(float(df['High'].iloc[-21:-1].max()), 2)
            sma20 = round(float(latest['SMA20']), 2)
            vol_surge = round(float(latest['Volume'] / latest['VolSMA20']), 2)
            pct_change = round(float(((ltp - prev['Close']) / prev['Close']) * 100), 2)

            # Technical Conditions Check
            is_volume_high = vol_surge >= 1.8
            is_breakout = ltp >= high_20d
            is_near_sma = (ltp >= sma20 * 0.98) and (ltp <= sma20 * 1.03)

            status = "Hold/Wait"
            if is_volume_high and is_breakout:
                status = "🚀 Breakout Setup"
            elif is_volume_high and is_near_sma:
                status = "🎯 Dip Buy Setup"
            elif is_volume_high:
                status = "⚡ High Vol Accumulation"

            screened_data.append({
                "Ticker": ticker.replace(".NS", ""),
                "LTP (₹)": ltp,
                "Change (%)": pct_change,
                "Vol Surge": f"{vol_surge}x",
                "20-SMA (₹)": sma20,
                "20D High (₹)": high_20d,
                "Status": status,
                "Raw_LTP": ltp,
                "Raw_SMA20": sma20,
                "Raw_High20": high_20d
            })
        except Exception as e:
            continue
            
    return pd.DataFrame(screened_data)

# App Navigation
tab1, tab2 = st.tabs(["🚀 Market Scanner", "📈 Chart & Trade Setup"])

with tab1:
    if st.button("🚀 Scan Market Now", use_container_width=True):
        st.cache_data.clear()

    with st.spinner("Fetching Live Market Data..."):
        df_results = fetch_stock_data(DEFAULT_TICKERS)

    if not df_results.empty:
        # Highlight Setup Stocks
        display_df = df_results[["Ticker", "LTP (₹)", "Change (%)", "Vol Surge", "20-SMA (₹)", "Status"]]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("No data found or market closed.")

with tab2:
    st.subheader("🎯 Auto Trade Levels & Live Chart")
    selected_stock = st.selectbox("Select Stock to Analyze:", [t.replace(".NS", "") for t in DEFAULT_TICKERS])

    if not df_results.empty and selected_stock in df_results["Ticker"].values:
        row = df_results[df_results["Ticker"] == selected_stock].iloc[0]
        
        ltp = row["Raw_LTP"]
        sma20 = row["Raw_SMA20"]
        high20 = row["Raw_High20"]

        # Calculate Auto Swing Levels
        dip_min = round(sma20 * 0.99, 2)
        dip_max = round(sma20 * 1.015, 2)
        breakout_entry = round(high20 * 1.005, 2)
        sl = round(min(sma20 * 0.96, ltp * 0.95), 2)
        target1 = round(ltp + (ltp - sl) * 1.5, 2)
        target2 = round(ltp + (ltp - sl) * 2.5, 2)

        # Show Trade Card
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Dip Buying Zone:** ₹{dip_min} – ₹{dip_max}")
            st.success(f"**Breakout Entry:** Above ₹{breakout_entry}")
            st.error(f"**Stop Loss (SL):** ₹{sl}")
        with col2:
            st.metric("Target 1 (Short-Term)", f"₹{target1}")
            st.metric("Target 2 (Mid-Term)", f"₹{target2}")

        st.markdown("---")
        st.subheader(f"📊 Live TradingView Chart ({selected_stock})")

        # TradingView Embed Widget
        tv_widget = f"""
        <div class="tradingview-widget-container">
          <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_1&symbol=NSE%3A{selected_stock}&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=light&style=1&timezone=Asia%2FKolkata"
                  width="100%" height="450" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
        </div>
        """
        components.html(tv_widget, height=460)