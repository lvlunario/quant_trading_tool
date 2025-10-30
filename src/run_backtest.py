import pandas as pd
import numpy as np
import torch
import matplotlib.pyplot as plt
import os

from backtest_engine import TradingEnvironment
from models import ActorCritic

# --- Configuration ---
TICKER = "AAPL" 
AGENT_SAVE_PATH = "models/saved_models/agent.pth"
INITIAL_CAPITAL = 50000
INPUT_DIM = 5 

def calculate_metrics(portfolio_history, benchmark_history, initial_capital):
    """Calculates key performance metrics for the backtest."""
    final_portfolio_value = portfolio_history['value'].iloc[-1]
    final_benchmark_value = benchmark_history['value'].iloc[-1]
    total_return_pct = (final_portfolio_value - initial_capital) / initial_capital
    benchmark_return_pct = (final_benchmark_value - initial_capital) / initial_capital
    portfolio_history['daily_return'] = portfolio_history['value'].pct_change().fillna(0)
    sharpe_ratio = 0.0
    if portfolio_history['daily_return'].std() > 1e-8:
        sharpe_ratio = (portfolio_history['daily_return'].mean() / portfolio_history['daily_return'].std()) * np.sqrt(252)
    roll_max = portfolio_history['value'].cummax()
    daily_drawdown = portfolio_history['value'] / roll_max - 1.0
    max_drawdown = daily_drawdown.min()
    return {
        "Total Return (%)": f"{total_return_pct:.2%}",
        "Benchmark Return (%)": f"{benchmark_return_pct:.2%}",
        "Sharpe Ratio": f"{sharpe_ratio:.2f}",
        "Maximum Drawdown (%)": f"{max_drawdown:.2%}",
        "Final Portfolio Value ($)": f"${final_portfolio_value:,.2f}"
    }

def run_backtest():
    """Runs the full backtest for the trained agent."""
    print("--- Starting Professional Backtest ---")
    
    print(f"1. Loading test data for {TICKER}...")
    data_path = f"data/processed/{TICKER}_processed.csv"
    if not os.path.exists(data_path):
        print(f"Error: Processed data not found. Run data_collector.py"); return
        
    full_data = pd.read_csv(data_path, index_col='Date', parse_dates=True)
    test_data = full_data.iloc[int(len(full_data) * 0.8):]
    print(f"Loaded {len(test_data)} days of test data.")

    print(f"2. Loading professionally trained agent from {AGENT_SAVE_PATH}...")
    if not os.path.exists(AGENT_SAVE_PATH):
        print("Error: Trained agent not found. Run train_agent.py"); return
        
    agent = ActorCritic(input_dim=INPUT_DIM, action_dim=3)
    agent.load_state_dict(torch.load(AGENT_SAVE_PATH))
    agent.eval()

    print("3. Setting up professional trading environment...")
    env = TradingEnvironment(test_data, initial_capital=INITIAL_CAPITAL)
    
    print("4. Running backtest simulation...")
    state = env.reset()
    done = False
    
    while not done:
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            policy_logits, _ = agent(state_tensor)
        action = torch.argmax(policy_logits).item()
        state, _, done = env.step(action)
    
    portfolio_history = pd.DataFrame(env.history)
    portfolio_history.index = test_data.index[:len(portfolio_history)]

    benchmark_start_price = test_data['Close'].iloc[0]
    benchmark_shares = INITIAL_CAPITAL / benchmark_start_price
    benchmark_history = pd.DataFrame({'value': benchmark_shares * test_data['Close']})

    print("\n--- Backtest Results ---")
    metrics = calculate_metrics(portfolio_history, benchmark_history, INITIAL_CAPITAL)
    for name, value in metrics.items():
        print(f"- {name}: {value}")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.plot(portfolio_history.index, portfolio_history['value'], label='Agent Strategy', color='royalblue', linewidth=2)
    ax.plot(benchmark_history.index, benchmark_history['value'], label='Buy and Hold Benchmark', color='grey', linestyle='--')
    ax.set_title(f'Trading Strategy vs. Benchmark for {TICKER}', fontsize=16)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True)
    from matplotlib.ticker import StrMethodFormatter
    ax.yaxis.set_major_formatter(StrMethodFormatter('${x:,.0f}'))
    plt.tight_layout()
    plt.savefig('backtest_results.png')
    print("\nChart saved to backtest_results.png")
    plt.show()

if __name__ == '__main__':
    run_backtest()

