import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import pickle

class DataCollector:
    """Enhanced data collector for quantum trading system"""
    
    def __init__(self, save_path="data"):
        self.save_path = save_path
        self.raw_path = os.path.join(save_path, "raw")
        self.processed_path = os.path.join(save_path, "processed")
        
        # Create directories
        os.makedirs(self.raw_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)

    def download_stock_data(self, ticker, start_date, end_date):
        """Download stock data from Yahoo Finance"""
        try:
            print(f"Downloading {ticker} data from {start_date} to {end_date}")
            stock_data = yf.download(ticker, start=start_date, end=end_date)
            
            if stock_data.empty:
                print(f"No data found for {ticker}")
                return None
                
            # Save raw data
            filename = f"{ticker}_{start_date}_to_{end_date}.csv"
            filepath = os.path.join(self.raw_path, filename)
            stock_data.to_csv(filepath)
            print(f"Saved raw data to: {filepath}")
            
            return stock_data
            
        except Exception as e:
            print(f"Error downloading {ticker}: {e}")
            return None
    
    def add_technical_indicators(self, data):
        """Add technical indicators as per Chen et al. paper"""
        data = data.copy()
        
        # Moving averages
        data['MA5'] = data['Close'].rolling(window=5).mean()
        data['MA10'] = data['Close'].rolling(window=10).mean()
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA60'] = data['Close'].rolling(window=60).mean()
        
        # Volatility
        data['Volatility'] = (
            data['Close'].rolling(window=20).std() / 
            data['Close'].rolling(window=20).mean()
        )
        
        return data.dropna()
    
    def preprocess_for_qlstm(self, data, ticker, sequence_length=4, 
                           prediction_horizon=5, threshold=0.012):
        """Preprocess data for QLSTM training as per Chen et al."""
        
        # Add technical indicators
        processed_data = self.add_technical_indicators(data)
        
        # Create future labels
        future_returns = processed_data['Close'].pct_change(prediction_horizon).shift(-prediction_horizon)
        
        labels = []
        for ret in future_returns:
            if pd.isna(ret):
                labels.append(-1)  # Invalid
            elif ret > threshold:
                labels.append(1)   # Up
            elif ret < -threshold:
                labels.append(0)   # Down
            else:
                labels.append(-1)  # Neutral
        
        processed_data['label'] = labels
        
        # Normalize features
        features_to_scale = ['Open', 'High', 'Low', 'Close', 'MA5', 'MA10']
        scaler = MinMaxScaler(feature_range=(0, 1))
        processed_data[features_to_scale] = scaler.fit_transform(processed_data[features_to_scale])
        
        # Save processed data and scaler
        processed_filename = f"{ticker}_processed.csv"
        processed_filepath = os.path.join(self.processed_path, processed_filename)
        processed_data.to_csv(processed_filepath)
        
        scaler_filename = f"{ticker}_scaler.pkl"
        scaler_filepath = os.path.join(self.processed_path, scaler_filename)
        with open(scaler_filepath, 'wb') as f:
            pickle.dump(scaler, f)
        
        print(f"Saved processed data to: {processed_filepath}")
        print(f"Saved scaler to: {scaler_filepath}")
        
        return processed_data, scaler

def main():
    """Main data collection function"""
    collector = DataCollector()
    
    # Tickers as per paper and common stocks
    tickers = {
        'currency': ['USDTWD=X'],  # Primary focus from paper
        'stocks': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA']
    }
    
    start_date = "2020-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print("Starting data collection for quantum trading system")
    print(f"Date range: {start_date} to {end_date}")
    print("-" * 50)
    
    for category, ticker_list in tickers.items():
        print(f"\nProcessing {category} tickers:")
        for ticker in ticker_list:
            data = collector.download_stock_data(ticker, start_date, end_date)
            if data is not None:
                processed_data, scaler = collector.preprocess_for_qlstm(data, ticker)
                print(f"✓ {ticker}: {len(processed_data)} records processed")
            else:
                print(f"✗ {ticker}: Failed to download")
    
    print("\nData collection completed!")

if __name__ == '__main__':
    main()
