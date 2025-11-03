# ------------------- streamlit_app.py -------------------
import streamlit as st
import pandas as pd
import plotly.express as px
from yahooquery import Ticker, search
from streamlit_lottie import st_lottie
import yfinance as yf
from ai_portfolio import AIPortfolioAnalyzer
import requests
import feedparser

# ------------------- Lottie Loader -------------------
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except:
        return None
    return None

# ------------------- Features -------------------
features = [
    {"title": "Real-time Stock Data", "desc": "Get live updates on major stocks, indices, and market trends.", 
     "lottie": "https://assets2.lottiefiles.com/packages/lf20_1pxqjqps.json"},
    {"title": "AI-Powered Portfolio", "desc": "Analyze your portfolio with weighted calculations, returns, and risk breakdowns.", 
     "lottie": "https://assets2.lottiefiles.com/packages/lf20_tutvdkg0.json"},
    {"title": "Sector & Risk Breakdown", "desc": "Visualize portfolio sectors and risk levels for better diversification.", 
     "lottie": "https://assets2.lottiefiles.com/packages/lf20_puciaact.json"}
]

# ------------------- Cached Helpers -------------------
@st.cache_data(ttl=60)
def fetch_stock_history(symbol, period="30d"):
    try:
        t = Ticker(symbol)
        data = t.history(period=period)
        if data.empty:
            return None
        return data.reset_index()
    except:
        return None

@st.cache_data(ttl=300)
def find_ticker_by_name(company_name):
    try:
        result = search(company_name)
        if result['quotes']:
            return result['quotes'][0]['symbol']
    except:
        return None

@st.cache_data(ttl=30)
def get_current_prices(symbols):
    prices = {}
    for symbol in symbols:
        try:
            data = yf.Ticker(symbol).history(period="1d")
            if not data.empty:
                prices[symbol] = data['Close'].iloc[-1]
        except:
            prices[symbol] = None
    return prices

# ------------------- Sidebar Helpers -------------------
@st.cache_data(ttl=60)
def fetch_index_value(ticker_symbol):
    try:
        hist = Ticker(ticker_symbol).history(period="2d")
        if not hist.empty:
            last = round(hist['close'].iloc[-1],2)
            prev = round(hist['close'].iloc[-2],2)
            diff = round(last - prev,2)
            return last, diff
    except:
        pass
    return "N/A", 0

@st.cache_data(ttl=120)
def fetch_index_history(ticker_symbol, days=30):
    try:
        hist = Ticker(ticker_symbol).history(period=f"{days}d").reset_index()
        return hist
    except:
        return pd.DataFrame()

# ------------------- Main App -------------------
def main():
    st.set_page_config(page_title="AI Portfolio Analyzer", page_icon="🤖", layout="wide")
    
    # ------------------- Home Page -------------------
    st.title("📊 AI-Powered Investment Portfolio")
    st.subheader("Platform Features")
    for feature in features:
        st.markdown(f"{feature['title']}")
        st.markdown(feature['desc'])
        lottie_anim = load_lottie_url(feature['lottie'])
        if lottie_anim:
            st_lottie(lottie_anim, height=150)
        st.markdown("---")

    # ------------------- Sidebar -------------------
    with st.sidebar:
        st.markdown("<h1 style='font-size:28px;'>📊 Finance Feed</h1>", unsafe_allow_html=True)

        # Sensex and Nifty
        sensex_val, sensex_diff = fetch_index_value("^BSESN")
        nifty_val, nifty_diff = fetch_index_value("^NSEI")

        sensex_color = "#28a745" if sensex_diff >= 0 else "#dc3545"
        nifty_color = "#28a745" if nifty_diff >= 0 else "#dc3545"

        st.markdown(f"📈 Sensex:** <span style='color:{sensex_color}'>{sensex_val} ({sensex_diff:+})</span>", unsafe_allow_html=True)
        st.markdown(f"📊 Nifty:** <span style='color:{nifty_color}'>{nifty_val} ({nifty_diff:+})</span>", unsafe_allow_html=True)
        
        # Latest Market News
        st.markdown("### Latest Market News")
        rss_url = "https://finance.yahoo.com/news/rssindex"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:5]:  # Top 5 news
            st.markdown(f"- [{entry.title}]({entry.link})")

    # ------------------- Tabs -------------------
    tab1, tab2, tab3 = st.tabs(["Stock Analysis", "AI-Powered Portfolio", "Market Insights"])
    tab1_ph = tab1.empty()
    tab2_ph = tab2.empty()
    tab3_ph = tab3.empty()

    # ------------------- Tab 1: Stock Analysis -------------------
    with tab1_ph.container():
        st.header("Stock Analysis")
        user_input = st.text_input("Enter company name or ticker:", key="stock_input")
        if user_input:
            symbol = user_input.strip().upper()
            if not symbol.endswith(".NS") and not symbol.startswith("^"):
                found_symbol = find_ticker_by_name(user_input)
                if found_symbol:
                    symbol = found_symbol
                    st.write(f"Found ticker: {symbol}")
                else:
                    st.warning("Could not find valid ticker.")
                    symbol = None
            if symbol:
                data_30d = fetch_stock_history(symbol, period="30d")
                if data_30d is not None and len(data_30d) > 1:
                    # ------------------- Stock Metrics -------------------
                    ticker_yf = yf.Ticker(symbol)
                    info = ticker_yf.info

                    current_price = info.get("regularMarketPrice", "N/A")
                    previous_close = info.get("previousClose", "N/A")
                    beta = info.get("beta", "N/A")

                    # 30-Day Volatility
                    returns = data_30d['close'].pct_change().dropna()
                    volatility_30d = round(returns.std() * 100, 2) if len(returns) > 0 else "N/A"

                    # Daily Return
                    daily_return = None
                    if current_price != "N/A" and previous_close != "N/A":
                        daily_return = round(((current_price - previous_close)/previous_close)*100,2)

                    # Colors
                    daily_color = "green" if daily_return is not None and daily_return >=0 else "red"
                    if beta != "N/A":
                        if beta < 1:
                            beta_color = "green"
                        elif beta <= 1.5:
                            beta_color = "orange"
                        else:
                            beta_color = "red"
                    else:
                        beta_color = "black"
                    if volatility_30d != "N/A":
                        if volatility_30d < 2:
                            vol_color = "green"
                        elif volatility_30d <= 5:
                            vol_color = "orange"
                        else:
                            vol_color = "red"
                    else:
                        vol_color = "black"

                    st.markdown(f"{symbol} Metrics:")
                    st.markdown(f"- *Price:* {current_price}")
                    if daily_return is not None:
                        st.markdown(f"- *Daily Return:* <span style='color:{daily_color}'>{daily_return:+}%</span>", unsafe_allow_html=True)
                    st.markdown(f"- *Beta:* <span style='color:{beta_color}'>{beta}</span>", unsafe_allow_html=True)
                    st.markdown(f"- *Volatility (30D):* <span style='color:{vol_color}'>{volatility_30d}%</span>", unsafe_allow_html=True)

                    # Trend Chart (30 days)
                    fig = px.line(data_30d, x='date', y='close', title=f"{symbol} Last 30 Days Trend", template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

    # ------------------- Tab 2: AI-Powered Portfolio -------------------
    with tab2_ph.container():
        st.header("AI-Powered Portfolio")
        portfolio_text = st.text_area("Enter your portfolio:", placeholder="AAPL:40\nGOOGL:30\nSPY:30", height=120)
        api_key = st.text_input("OpenAI API Key (for analysis)", type="password", key="portfolio_api")
        if st.button("Analyze Portfolio"):
            if portfolio_text and api_key:
                analyzer = AIPortfolioAnalyzer(api_key.strip())
                portfolio = {}
                for line in portfolio_text.strip().split('\n'):
                    if ':' in line:
                        sym, wt = line.split(':')
                        portfolio[sym.strip().upper()] = float(wt.strip())
                analysis = analyzer.analyze_portfolio(portfolio)
                st.text_area("Portfolio Analysis Results", analysis, height=300)

                # Real-time Portfolio Bar Chart with 30-day volatility and traffic-light coloring
                prices = get_current_prices(list(portfolio.keys()))
                df_prices = pd.DataFrame(list(prices.items()), columns=['Symbol','Current Price']).dropna()
                if not df_prices.empty:
                    colors = []
                    for sym in df_prices['Symbol']:
                        hist_30d = fetch_stock_history(sym, period="30d")
                        daily_return = 0
                        if hist_30d is not None and len(hist_30d) >= 2:
                            last, prev = hist_30d['close'].iloc[-1], hist_30d['close'].iloc[-2]
                            daily_return = last - prev
                        color = 'green' if daily_return >=0 else 'red'
                        colors.append(color)

                    fig = px.bar(df_prices, x='Symbol', y='Current Price', title='Real-time Stock Prices',
                                 color=colors, color_discrete_map={'green':'green','red':'red'})
                    st.plotly_chart(fig, use_container_width=True)

    # ------------------- Tab 3: Market Insights -------------------
    with tab3_ph.container():
        st.header("Market Insights")
        sensex_ph = st.empty()
        nifty_ph = st.empty()
        gainers_ph = st.empty()
        losers_ph = st.empty()

        # Index Trends
        sensex_30 = fetch_index_history("^BSESN")
        nifty_30 = fetch_index_history("^NSEI")
        if not sensex_30.empty:
            fig1 = px.line(sensex_30, x='date', y='close', title="Sensex Last 30 Days", template="plotly_white")
            sensex_ph.plotly_chart(fig1, use_container_width=True)
        if not nifty_30.empty:
            fig2 = px.line(nifty_30, x='date', y='close', title="Nifty Last 30 Days", template="plotly_white")
            nifty_ph.plotly_chart(fig2, use_container_width=True)

        # Top gainers & losers
        tickers = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
                   "HINDUNILVR.NS","KOTAKBANK.NS","LT.NS","SBIN.NS","BAJFINANCE.NS"]
        prices = get_current_prices(tickers)
        changes = []
        for ticker in tickers:
            if ticker in prices and prices[ticker] is not None:
                try:
                    hist = yf.Ticker(ticker).history(period="2d")
                    if len(hist) >= 2:
                        last, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                        pct_change = ((last - prev)/prev)*100
                        changes.append({"symbol": ticker, "change_pct": pct_change})
                except:
                    continue
        if changes:
            df = pd.DataFrame(changes).sort_values("change_pct", ascending=False)
            gainers = df.head(5)
            losers = df.tail(5).sort_values("change_pct")
            if not gainers.empty:
                fig_g = px.bar(gainers, x='symbol', y='change_pct', title="Top 5 Gainers", 
                               color='change_pct', color_continuous_scale='greens')
                gainers_ph.plotly_chart(fig_g, use_container_width=True)
            if not losers.empty:
                fig_l = px.bar(losers, x='symbol', y='change_pct', title="Top 5 Losers", 
                               color='change_pct', color_continuous_scale='reds')
                losers_ph.plotly_chart(fig_l, use_container_width=True)

if __name__ == "__main__":
    main()