import yfinance as yf
import pandas as pd
import os
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import pickle

def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / (loss + 1e-8)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculates the Moving Average Convergence Divergence (MACD)."""
    fast_ema = data['Close'].ewm(span=fast_period, adjust=False).mean()
    slow_ema = data['Close'].ewm(span=slow_period, adjust=False).mean()
    macd = fast_ema - slow_ema
    signal_line = macd.ewm(span=signal_period, adjust=False).mean()
    return macd, signal_line

class DataCollector:
    """Refactored data collector that includes professional-grade indicators like RSI and MACD."""
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
            
            stock_data.to_csv(os.path.join(self.raw_path, f"{ticker}_{start_date}_to_{end_date}.csv"))
            return stock_data
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            return None
    
    def add_technical_indicators(self, data):
        data = data.copy()
        data['RSI'] = calculate_rsi(data)
        data['MACD'], data['MACD_Signal'] = calculate_macd(data)
        data['Volatility'] = data['Close'].rolling(window=20).std()
        return data.dropna()
    
    def preprocess_for_models(self, data, ticker):
        processed_data = self.add_technical_indicators(data)
        
        features_to_scale = ['Close', 'RSI', 'MACD', 'MACD_Signal', 'Volatility']
        scaler = MinMaxScaler(feature_range=(-1, 1))
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