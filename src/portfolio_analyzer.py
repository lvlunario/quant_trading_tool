import yfinance as yf
import pandas as pd
import numpy as np
import torch
import os
from datetime import datetime, timedelta

from models import QLSTM, QA3C, q_layer_lstm, vqc_a3c, n_qubits_lstm, n_qubits_a3c
from data_collector import DataCollector

class PortfolioAnalyzer:
    """
    Analyzes a given stock ticker and provides a trading recommendation
    based on the trained QLSTM and QA3C models.
    """
    def __init__(self, qlstm_path, qa3c_path):
        if not os.path.exists(qlstm_path) or not os.path.exists(qa3c_path):
            raise FileNotFoundError("Trained models not found. Please train both QLSTM and QA3C.")
            
        # Load QLSTM
        self.qlstm_model = QLSTM(input_dim=6, hidden_dim=2, q_layer=q_layer_lstm, n_qubits=n_qubits_lstm)
        self.qlstm_model.load_state_dict(torch.load(qlstm_path))
        self.qlstm_model.eval()

        # Load QA3C
        self.qa3c_agent = QA3C(input_dim=10, q_layer=vqc_a3c, n_qubits=n_qubits_a3c)
        self.qa3c_agent.load_state_dict(torch.load(qa3c_path))
        self.qa3c_agent.eval()

        self.data_collector = DataCollector()

    def get_recommendation(self, ticker):
        """
        Fetches latest data for a ticker, constructs the state, and gets a recommendation.
        """
        try:
            # --- 1. Fetch and process recent data ---
            end_date = datetime.now()
            start_date = end_date - timedelta(days=120) # Need enough data for MAs
            data = self.data_collector.download_stock_data(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            if data is None or len(data) < 60:
                return "Insufficient Data", 0.0, 0.0

            data = self.data_collector.add_technical_indicators(data)
            
            # --- 2. Get QLSTM Prediction for the latest day ---
            sequence_data = data[['Open', 'High', 'Low', 'Close', 'MA5', 'MA10']].iloc[-4:].values
            sequence_tensor = torch.tensor(sequence_data, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                qlstm_preds = self.qlstm_model(sequence_tensor).numpy().flatten()
            
            # --- 3. Construct the state vector for the latest day ---
            latest_data = data.iloc[-1]
            current_price = latest_data['Close']

            state = np.array([
                qlstm_preds[1], # Bullish prob
                qlstm_preds[0], # Bearish prob
                0.5, # Placeholder for cash ratio
                0.5, # Placeholder for holdings ratio
                0.0, # Placeholder for P&L
                0.0, # Placeholder for price ratio
                (current_price - latest_data['MA20']) / latest_data['MA20'],
                (current_price - latest_data['MA60']) / latest_data['MA60'],
                latest_data['MA5'] - latest_data['MA20'],
                latest_data['Volatility']
            ])

            # --- 4. Get QA3C Agent's decision ---
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                policy, _ = self.qa3c_agent(state_tensor)
            
            policy = policy.flatten()
            action = torch.argmax(policy).item()
            confidence = policy[action].item()
            
            action_map = {0: "Hold", 1: "Buy", 2: "Sell"}
            recommendation = action_map[action]

            return recommendation, confidence, current_price

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return "Error", 0.0, 0.0

if __name__ == '__main__':
    analyzer = PortfolioAnalyzer(
        qlstm_path="models/saved_models/qlstm_best.pth",
        qa3c_path="models/saved_models/qa3c_agent.pth"
    )
    tickers = ["AAPL", "GOOG", "MSFT"]
    for t in tickers:
        rec, conf, price = analyzer.get_recommendation(t)
        print(f"Ticker: {t}, Price: ${price:.2f}, Recommendation: {rec} (Confidence: {conf:.2f})")
