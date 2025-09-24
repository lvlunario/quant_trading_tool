import yfinance as yf
import pandas as pd
import os
from datetime import datetime

def get_stock_data(ticker, start_date, end_date, save_path="../data"):
    """
    Downloads historical stock data from Yahoo Finance and saves it as a CSV file.
    """
    try:
        # Adjust save_path to be relative to the main project directory
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        stock_data = yf.download(ticker, start=start_date, end=end_date)

        if stock_data.empty:
            print(f"No data found for {ticker} in the specified date range.")
            return

        file_name = f"{ticker}_{start_date}_to_{end_date}.csv"
        full_path = os.path.join(save_path, file_name)
        stock_data.to_csv(full_path)
        print(f"Successfully downloaded and saved data for {ticker} to {full_path}")

    except Exception as e:
        print(f"An error occurred while downloading data for {ticker}: {e}")

if __name__ == '__main__':
    tickers_to_download = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSM", "AMD", "NVDA", "ORCL", "META", "TSLA", "BYD", "BABA", "NFLX"]
    start = "2010-01-01"
    end = datetime.today().strftime('%Y-%m-%d')

    for ticker in tickers_to_download:
        get_stock_data(ticker, start, end)