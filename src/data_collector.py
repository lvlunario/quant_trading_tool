import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import pickle

# --- Utility to calculate RSI ---
def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / (loss + 1e-8) # Add epsilon to prevent division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi

class DataCollector:
    """
    Refactored data collector that includes professional-grade indicators like RSI.
    """
    def __init__(self, save_path="data"):
        self.save_path = save_path
        self.raw_path = os.path.join(save_path, "raw")
        self.processed_path = os.path.join(save_path, "processed")
        os.makedirs(self.raw_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)

    def _sanitize_columns(self, data):
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data

    def download_stock_data(self, ticker, start_date, end_date):
        try:
            print(f"Downloading {ticker} data from {start_date} to {end_date}")
            stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if stock_data.empty: return None
            
            stock_data = self._sanitize_columns(stock_data)
            for col in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
                if col in stock_data.columns:
                    stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')
            stock_data.dropna(subset=['Close'], inplace=True)
            
            filename = f"{ticker}_{start_date}_to_{end_date}.csv"
            stock_data.to_csv(os.path.join(self.raw_path, filename))
            return stock_data
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            return None
    
    def add_technical_indicators(self, data):
        data = data.copy()
        data['MA5'] = data['Close'].rolling(window=5).mean()
        data['MA10'] = data['Close'].rolling(window=10).mean()
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA60'] = data['Close'].rolling(window=60).mean()
        data['RSI'] = calculate_rsi(data) # --- NEW: Add RSI ---
        data['Volatility'] = data['Close'].rolling(window=20).std()
        return data.dropna()
    
    def preprocess_for_models(self, data, ticker):
        processed_data = self.add_technical_indicators(data)
        future_returns = processed_data['Close'].pct_change(5).shift(-5)
        
        processed_data['label'] = np.select(
            [future_returns > 0.012, future_returns < -0.012], [1, 0], default=-1
        )
        
        features_to_scale = ['Open', 'High', 'Low', 'Close', 'MA5', 'MA10', 'RSI', 'Volatility']
        scaler = MinMaxScaler(feature_range=(-1, 1)) # Scale between -1 and 1 for better NN performance
        processed_data[features_to_scale] = scaler.fit_transform(processed_data[features_to_scale])
        
        processed_data.to_csv(os.path.join(self.processed_path, f"{ticker}_processed.csv"))
        with open(os.path.join(self.processed_path, f"{ticker}_scaler.pkl"), 'wb') as f:
            pickle.dump(scaler, f)
        
        print(f"✓ {ticker}: Preprocessing complete.")
        return processed_data, scaler

def main():
    collector = DataCollector()
    tickers = {'stocks': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA']}
    start_date, end_date = "2018-01-01", datetime.now().strftime('%Y-%m-%d')
    
    for category, ticker_list in tickers.items():
        print(f"\nProcessing {category} tickers:")
        for ticker in ticker_list:
            data = collector.download_stock_data(ticker, start_date, end_date)
            if data is not None and not data.empty:
                collector.preprocess_for_models(data, ticker)
            else:
                print(f"✗ {ticker}: Failed to download or process")

if __name__ == '__main__':
    main()

