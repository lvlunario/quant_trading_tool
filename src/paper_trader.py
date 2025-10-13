import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
import os
import time
import schedule
from portfolio_analyzer import PortfolioAnalyzer
import sys

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# Stocks to be traded by the bot - passed from Streamlit or default
# The first argument to the script will be a comma-separated list of tickers
DEFAULT_UNIVERSE = ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA', 'AMZN']
try:
    TRADE_UNIVERSE = sys.argv[1].split(',') if len(sys.argv) > 1 else DEFAULT_UNIVERSE
except:
    TRADE_UNIVERSE = DEFAULT_UNIVERSE


class PaperTrader:
    def __init__(self):
        self.api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=BASE_URL, api_version='v2')
        self.analyzer = PortfolioAnalyzer(
            qlstm_path="models/saved_models/qlstm_best.pth",
            qa3c_path="models/saved_models/qa3c_agent.pth"
        )
        print("Paper Trader Initialized. Connecting to Alpaca...")
        self.log_account_status()

    def log_account_status(self):
        try:
            account = self.api.get_account()
            print(f"[{time.ctime()}] Alpaca Account: {account.status} | Portfolio Value: ${account.portfolio_value} | Buying Power: ${account.buying_power}")
        except Exception as e:
            print(f"Error connecting to Alpaca: {e}")

    def run_trading_logic(self):
        print(f"\n--- Running Trading Logic at {time.ctime()} ---")
        if not self.api.get_clock().is_open:
            print("Market is closed. Skipping trading logic.")
            return

        try:
            positions = self.api.list_positions()
            held_tickers = {p.symbol: p.qty for p in positions}

            for ticker in TRADE_UNIVERSE:
                recommendation, confidence, price = self.analyzer.get_recommendation(ticker)
                print(f"Analyzing {ticker}: Recommendation={recommendation}, Confidence={confidence:.2f}, Price=${price:.2f}")

                # --- Trade Execution Logic ---
                # Define how much capital to use per trade, e.g., $1,000
                trade_capital = 1000
                qty_to_trade = int(trade_capital // price)
                if qty_to_trade == 0:
                    print(f"Skipping {ticker}, price is too high for defined trade capital.")
                    continue

                if recommendation == "Buy" and confidence > 0.65: # Higher confidence for live trades
                    if ticker not in held_tickers:
                        print(f"Action: Placing BUY order for {qty_to_trade} shares of {ticker}")
                        self.api.submit_order(symbol=ticker, qty=qty_to_trade, side='buy', type='market', time_in_force='day')
                    else:
                        print(f"Action: Holding {ticker}, already in portfolio.")

                elif recommendation == "Sell" and confidence > 0.65:
                    if ticker in held_tickers:
                        qty_held = int(held_tickers[ticker])
                        print(f"Action: Placing SELL order for {qty_held} shares of {ticker}")
                        self.api.submit_order(symbol=ticker, qty=qty_held, side='sell', type='market', time_in_force='day')
                    else:
                        print(f"Action: No SELL for {ticker}, not in portfolio.")
                else:
                    print(f"Action: Holding {ticker} based on model recommendation.")
        
        except Exception as e:
            print(f"An error occurred during trading logic: {e}")

def job():
    trader = PaperTrader()
    trader.run_trading_logic()

if __name__ == "__main__":
    print("Starting autonomous paper trading bot...")
    print(f"Trading Universe: {TRADE_UNIVERSE}")
    print("Bot will run trading logic every 5 minutes during market hours.")
    
    # Run once immediately
    job()
    
    # Schedule to run every 5 minutes
    schedule.every(5).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

