import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
import os
import subprocess
import torch

# Import project modules
from models import QA3C, vqc_a3c, n_qubits_a3c
from backtest_engine import TradingEnvironment

st.set_page_config(
    page_title="Quantum Trading System",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- App State Management ---
if 'qlstm_trained' not in st.session_state:
    st.session_state.qlstm_trained = os.path.exists("models/saved_models/qlstm_best.pth")
if 'qa3c_trained' not in st.session_state:
    st.session_state.qa3c_trained = os.path.exists("models/saved_models/qa3c_agent.pth")


st.markdown("""
# 🚀 Quantum Trading System
### Multi-Modal Analysis Platform

Based on research by Chen et al.: *"Quantum-Enhanced Forecasting for Deep Reinforcement Learning in Algorithmic Trading"*
""")

# --- Sidebar Navigation ---
with st.sidebar:
    st.header("Navigation")
    st.write("📊 **Analysis Modules**")
    
    pages = {
        "Dashboard": "📊",
        "Data Collection": "📈", 
        "QLSTM Training": "⚛️",
        "QA3C Training": "🤖",
        "Backtesting": "🔬",
        "Portfolio Analysis": "💼",
        "Paper Trading": "💰",
    }
    
    selected_page = st.selectbox("Select Page", list(pages.keys()))

    st.markdown("---")
    st.header("Model Status")
    st.info(f"QLSTM Trained: {'✅' if st.session_state.qlstm_trained else '❌'}")
    st.info(f"QA3C Trained: {'✅' if st.session_state.qa3c_trained else '❌'}")


# --- Page Implementations ---

if selected_page == "Dashboard":
    st.subheader("Project Dashboard")
    # Key metrics from paper
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Paper Total Return", "11.87%")
    with col2:
        st.metric("Paper Max Drawdown", "0.92%")
    with col3:
        st.metric("QA3C Parameters", "244", "vs Classical: 3,332")  
    with col4:
        st.metric("QLSTM Accuracy", "~71.5%")
    
    st.markdown("### Welcome to the Quantum Trading System!")
    st.write("""
    This application is an implementation of the research paper by Chen et al., which explores using hybrid quantum-classical machine learning models for algorithmic trading. 
    
    **Follow the steps in the sidebar to:**
    1.  **Collect** financial data.
    2.  **Train** the Quantum LSTM (QLSTM) forecaster.
    3.  **Train** the Quantum A3C (QA3C) trading agent.
    4.  **Backtest** the agent's performance on historical data.
    """)

elif selected_page == "Data Collection":
    st.subheader("📈 Data Collection Module")
    # (Code remains the same as previous version)
    ticker = st.text_input("Ticker Symbol", "USDTWD=X")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime(2000, 1, 1))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    if st.button("Download & Preprocess Data"):
        with st.spinner("Running data collection script..."):
            try:
                result = subprocess.run(["python", "src/data_collector.py"], capture_output=True, text=True, check=True)
                st.success("Data collection and preprocessing complete!")
                st.code(result.stdout)
            except subprocess.CalledProcessError as e:
                st.error("Data collection failed:")
                st.code(e.stderr)

elif selected_page == "QLSTM Training":
    st.subheader("⚛️ QLSTM Forecaster Training")
    st.info("This module trains the Quantum LSTM to predict short-term price trends.")
    if st.button("Train QLSTM Model", disabled=st.session_state.qlstm_trained):
        with st.spinner("Training QLSTM... This may take several minutes."):
            try:
                result = subprocess.run(["python", "src/train_qlstm.py"], capture_output=True, text=True, check=True)
                st.session_state.qlstm_trained = True
                st.success("QLSTM training completed!")
                st.code(result.stdout)
                st.rerun()
            except subprocess.CalledProcessError as e:
                st.error("Training failed:")
                st.code(e.stderr)
    if st.session_state.qlstm_trained:
        st.success("QLSTM model is already trained and saved.")


elif selected_page == "QA3C Training":
    st.subheader("🤖 QA3C Agent Training")
    st.info("This module trains the Reinforcement Learning agent to make trading decisions.")
    if not st.session_state.qlstm_trained:
        st.warning("Please train the QLSTM model first.")
    
    if st.button("Train QA3C Agent", disabled=not st.session_state.qlstm_trained or st.session_state.qa3c_trained):
        st.warning("This is a long process and may take hours. Please be patient.")
        with st.spinner("Training QA3C Agent... See terminal for progress."):
            try:
                # Using Popen to allow real-time feedback in the terminal
                process = subprocess.Popen(["python", "src/train_qa3c.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Placeholder for streaming output to Streamlit if desired
                placeholder = st.empty()
                output = ""
                for line in iter(process.stdout.readline, ''):
                    output += line
                    placeholder.code(output)
                
                process.wait()

                if process.returncode == 0:
                    st.session_state.qa3c_trained = True
                    st.success("QA3C training completed!")
                    st.rerun()
                else:
                    st.error("QA3C training failed. Check terminal for errors.")
                    st.code(process.stderr.read())
            
            except Exception as e:
                st.error(f"An error occurred: {e}")
    
    if st.session_state.qa3c_trained:
        st.success("QA3C agent is already trained and saved.")


elif selected_page == "Backtesting":
    st.subheader("🔬 Performance Backtesting")
    st.info("This module evaluates the trained QA3C agent on historical data.")
    
    if not st.session_state.qa3c_trained:
        st.warning("Please train the QA3C agent first.")
    
    if st.button("Run Backtest", disabled=not st.session_state.qa3c_trained):
        with st.spinner("Running backtest..."):
            try:
                # --- Backtesting Logic ---
                data = pd.read_csv(f"data/processed/USDTWD=X_processed.csv", index_col='Date', parse_dates=True)
                split_index = int(len(data) * 0.8)
                test_data = data.iloc[split_index:]

                env = TradingEnvironment(test_data, "models/saved_models/qlstm_best.pth")
                agent = QA3C(input_dim=10, q_layer=vqc_a3c, n_qubits=n_qubits_a3c, action_dim=3)
                agent.load_state_dict(torch.load("models/saved_models/qa3c_agent.pth"))
                agent.eval()

                state = env.reset()
                done = False
                while not done:
                    state_tensor = torch.FloatTensor(state).unsqueeze(0)
                    with torch.no_grad():
                        policy, _ = agent(state_tensor)
                    action = torch.argmax(policy).item()
                    state, _, done = env.step(action)
                
                # --- Display Results ---
                st.success("Backtest complete!")
                history_df = pd.DataFrame(env.history)
                
                # Metrics
                total_return = (history_df['portfolio_value'].iloc[-1] / env.initial_capital - 1) * 100
                max_drawdown = (1 - history_df['portfolio_value'] / history_df['portfolio_value'].cummax()).max() * 100
                
                st.subheader("Backtest Performance Metrics")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Return", f"{total_return:.2f}%")
                col2.metric("Max Drawdown", f"{max_drawdown:.2f}%")
                col3.metric("Total Trades", f"{env.total_trades}")

                # Chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=history_df['step'], y=history_df['portfolio_value'], name="Portfolio Value"))
                fig.update_layout(title="Portfolio Value Over Time", xaxis_title="Time Steps (Days)", yaxis_title="Portfolio Value ($)")
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred during backtesting: {e}")


else:
    st.subheader(f"{pages[selected_page]} {selected_page}")
    st.info(f"The {selected_page} module is under development.")

# Footer
st.markdown("---")
st.markdown("⚠️ **Important**: This is a research implementation. Quantum computing in finance is experimental. Always use paper trading first.")
