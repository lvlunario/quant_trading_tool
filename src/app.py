import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import os
import subprocess
import torch
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
import psutil

# Import project modules
from models import QA3C, vqc_a3c, n_qubits_a3c
from backtest_engine import TradingEnvironment
from portfolio_analyzer import PortfolioAnalyzer

# --- Page Config ---
st.set_page_config(page_title="Quantum Trading System", page_icon="⚛️", layout="wide")

# --- Load Alpaca API Keys ---
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# --- App State Management ---
if 'qlstm_trained' not in st.session_state:
    st.session_state.qlstm_trained = os.path.exists("models/saved_models/qlstm_best.pth")
if 'qa3c_trained' not in st.session_state:
    st.session_state.qa3c_trained = os.path.exists("models/saved_models/qa3c_agent.pth")
if 'bot_pid' not in st.session_state:
    st.session_state.bot_pid = None


# --- Main App ---
st.markdown("# 🚀 Quantum Trading System")

# --- Sidebar ---
with st.sidebar:
    st.header("Navigation")
    pages = {"Dashboard": "📊", "Data Collection": "📈", "QLSTM Training": "⚛️", "QA3C Training": "🤖", "Backtesting": "🔬", "Portfolio Analysis": "💼", "Paper Trading": "💰"}
    selected_page = st.selectbox("Select Page", list(pages.keys()))
    st.markdown("---")
    st.header("Model Status")
    st.info(f"QLSTM Trained: {'✅' if st.session_state.qlstm_trained else '❌'}")
    st.info(f"QA3C Trained: {'✅' if st.session_state.qa3c_trained else '❌'}")

# --- Page Implementations ---
# ... (Dashboard, Data Collection, QLSTM/QA3C Training, Backtesting pages remain the same) ...

if selected_page == "Portfolio Analysis":
    st.subheader("💼 On-Demand Portfolio Analysis")
    st.info("Get Buy/Sell/Hold recommendations for any stock using the trained QA3C agent.")
    if not st.session_state.qa3c_trained:
        st.warning("Please train the QA3C agent first.")
    else:
        tickers_input = st.text_input("Enter stock tickers (comma-separated)", "AAPL, GOOG, NVDA")
        if st.button("Analyze Portfolio"):
            with st.spinner("Analyzing... This may take a moment."):
                analyzer = PortfolioAnalyzer("models/saved_models/qlstm_best.pth", "models/saved_models/qa3c_agent.pth")
                tickers = [t.strip().upper() for t in tickers_input.split(',')]
                results = []
                for ticker in tickers:
                    rec, conf, price = analyzer.get_recommendation(ticker)
                    results.append({"Ticker": ticker, "Price": f"${price:.2f}", "Recommendation": rec, "Confidence": f"{conf:.2%}"})
                st.dataframe(pd.DataFrame(results), use_container_width=True)

elif selected_page == "Paper Trading":
    st.subheader("💰 Live Paper Trading Control Panel")
    if not API_KEY or not SECRET_KEY:
        st.error("Alpaca API keys not found. Please add them to your .env file.")
    elif not st.session_state.qa3c_trained:
        st.warning("Please train the QA3C agent first to enable the trading bot.")
    else:
        try:
            api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=BASE_URL)
            account = api.get_account()
            st.success("✅ Connected to Alpaca Paper Trading Account")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Portfolio Value", f"${float(account.portfolio_value):,.2f}")
            col2.metric("Buying Power", f"${float(account.buying_power):,.2f}")
            col3.metric("Account Status", account.status.title())

            st.markdown("---")
            st.subheader("Bot Control")

            # Check if the bot process is running
            bot_running = False
            if st.session_state.bot_pid:
                if psutil.pid_exists(st.session_state.bot_pid):
                    bot_running = True
                else:
                    st.session_state.bot_pid = None # Clear stale PID

            if bot_running:
                st.success(f"Trading bot is RUNNING (Process ID: {st.session_state.bot_pid}).")
            else:
                st.info("Trading bot is STOPPED.")

            trade_universe = st.text_input("Stocks to Trade (comma-separated)", 'AAPL,GOOGL,MSFT,NVDA,TSLA,AMZN')

            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start Trading Bot", disabled=bot_running):
                    with st.spinner("Starting bot..."):
                        process = subprocess.Popen(["python", "src/paper_trader.py", trade_universe])
                        st.session_state.bot_pid = process.pid
                        st.success(f"Trading bot started with PID: {process.pid}")
                        st.rerun()

            with col2:
                if st.button("⏹️ Stop Trading Bot", disabled=not bot_running):
                    p = psutil.Process(st.session_state.bot_pid)
                    p.terminate() # or p.kill()
                    st.session_state.bot_pid = None
                    st.warning("Trading bot process stopped.")
                    st.rerun()

            st.markdown("---")
            st.subheader("Current Positions")
            positions = api.list_positions()
            if positions:
                pos_data = [{"Symbol": p.symbol, "Qty": p.qty, "Market Value": f"${float(p.market_value):,.2f}", "Unrealized P/L": f"${float(p.unrealized_pl):,.2f}"} for p in positions]
                st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
            else:
                st.info("No open positions.")

        except Exception as e:
            st.error(f"Failed to connect to Alpaca: {e}")

elif selected_page not in ["Portfolio Analysis", "Paper Trading"]:
    # Placeholder for the other pages
    st.subheader(f"{pages[selected_page]} {selected_page}")
    st.info("This section is for displaying other modules like the Dashboard, Data Collection, Training, and Backtesting pages.")

# --- Footer ---
st.markdown("---")
st.markdown("⚠️ **Important**: This is a research implementation. Quantum computing in finance is experimental. Always use paper trading first.")

