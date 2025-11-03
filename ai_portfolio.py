import os
import yfinance as yf
from typing import Dict
from openai import OpenAI

class AIPortfolioAnalyzer:
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=api_key)

        # Predefined stock data
        self.stocks = {
            "AAPL": {"name": "Apple Inc.", "sector": "Technology", "beta": 1.2, "return": 15.0, "risk": "Medium", "volatility": 0.25},
            "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "beta": 1.3, "return": 12.0, "risk": "Medium", "volatility": 0.28},
            "MSFT": {"name": "Microsoft Corp.", "sector": "Technology", "beta": 1.1, "return": 14.0, "risk": "Medium", "volatility": 0.22},
            "NVDA": {"name": "NVIDIA Corp.", "sector": "Technology", "beta": 1.8, "return": 20.0, "risk": "High", "volatility": 0.45},
            "JPM": {"name": "JPMorgan Chase", "sector": "Financial", "beta": 1.0, "return": 12.0, "risk": "Low", "volatility": 0.20},
            "BAC": {"name": "Bank of America", "sector": "Financial", "beta": 1.2, "return": 10.0, "risk": "Medium", "volatility": 0.25},
            "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "beta": 0.7, "return": 8.0, "risk": "Low", "volatility": 0.15},
            "PFE": {"name": "Pfizer", "sector": "Healthcare", "beta": 0.8, "return": 6.0, "risk": "Low", "volatility": 0.18},
            "XOM": {"name": "ExxonMobil", "sector": "Energy", "beta": 1.1, "return": 8.0, "risk": "Medium", "volatility": 0.30},
            "SPY": {"name": "S&P 500 ETF", "sector": "Index", "beta": 1.0, "return": 10.0, "risk": "Low", "volatility": 0.15},
            "TSLA": {"name": "Tesla Inc.", "sector": "Automotive", "beta": 2.0, "return": 25.0, "risk": "High", "volatility": 0.55},
            "AMZN": {"name": "Amazon.com", "sector": "Consumer", "beta": 1.3, "return": 16.0, "risk": "Medium", "volatility": 0.30}
        }

    # ---------------- Batch fetch live data
    def fetch_live_data_batch(self, symbols):
        data = {}
        try:
            hist_data = yf.download(symbols, period="2d", interval="1d", group_by='ticker', threads=True)
            for symbol in symbols:
                df = hist_data[symbol] if len(symbols) > 1 else hist_data
                if not df.empty:
                    price = round(df['Close'].iloc[-1], 2)
                    prev_close = df['Close'].iloc[0]
                    daily_change = round(((price - prev_close)/prev_close)*100, 2)
                    data[symbol] = {"price": price, "daily_change": daily_change}
                else:
                    data[symbol] = {"price": None, "daily_change": None}
        except:
            for symbol in symbols:
                data[symbol] = {"price": None, "daily_change": None}
        return data

    # ---------------- Portfolio Analysis
    def analyze_portfolio(self, portfolio: Dict[str, float]) -> str:
        if not portfolio:
            return "Error: Portfolio is empty"
        total_weight = sum(portfolio.values())
        if total_weight == 0:
            return "Error: Portfolio weights sum to zero"

        symbols = list(portfolio.keys())
        live_data = self.fetch_live_data_batch(symbols)

        weighted_beta = 0
        weighted_return = 0
        weighted_volatility = 0
        sectors = {}
        risk_levels = {}

        for symbol, weight in portfolio.items():
            if symbol not in self.stocks:
                continue
            stock = self.stocks[symbol]
            weight_pct = weight / total_weight
            weighted_beta += stock["beta"] * weight_pct
            weighted_return += stock["return"] * weight_pct
            weighted_volatility += stock["volatility"] * weight_pct
            sectors[stock["sector"]] = sectors.get(stock["sector"], 0) + weight
            risk_levels[stock["risk"]] = risk_levels.get(stock["risk"], 0) + weight

        sector_breakdown = "\n".join([f"  - {sector}: {(weight/total_weight)*100:.1f}%" 
                                      for sector, weight in sectors.items()])
        risk_breakdown = "\n".join([f"  - {risk} Risk: {(weight/total_weight)*100:.1f}%" 
                                    for risk, weight in risk_levels.items()])

        return (
            f"📈 Portfolio Analysis\n"
            f"- Total Allocation: {total_weight}%\n"
            f"- Weighted Beta: {round(weighted_beta, 2)}\n"
            f"- Weighted Expected Return: {round(weighted_return, 2)}%\n"
            f"- Weighted Volatility: {round(weighted_volatility, 2)}\n"
            f"- Portfolio Risk: {'High' if weighted_beta > 1.3 else 'Medium' if weighted_beta > 0.8 else 'Low'}\n\n"
            f"Sector Breakdown:\n{sector_breakdown}\n\n"
            f"Risk Distribution:\n{risk_breakdown}"
        )