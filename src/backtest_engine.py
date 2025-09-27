import pandas as pd
import numpy as np
import torch
import os

from models import QLSTM, q_layer_lstm, n_qubits_lstm

class TradingEnvironment:
    """
    A class that simulates the stock trading environment.
    It manages the portfolio, executes trades, and calculates rewards
    based on the methodology from the Chen et al. paper.
    """
    def __init__(self, data, qlstm_model_path, initial_capital=50000):
        self.data = data
        self.initial_capital = initial_capital
        
        # --- State Variables ---
        self.current_step = 0
        self.cash = initial_capital
        self.holdings_value = 0
        self.position_size = 0 # Number of shares
        self.average_cost = 0
        self.total_trades = 0
        self.history = []

        # --- Load the pre-trained QLSTM forecaster ---
        self.qlstm_model = self._load_qlstm(qlstm_model_path)

    def _load_qlstm(self, path):
        """Loads the trained QLSTM model."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"QLSTM model not found at {path}. Please train it first.")
        model = QLSTM(
            input_dim=6, 
            hidden_dim=2,
            q_layer=q_layer_lstm,
            n_qubits=n_qubits_lstm,
            output_dim=2
        )
        model.load_state_dict(torch.load(path))
        model.eval() # Set to evaluation mode
        return model

    def _get_qlstm_prediction(self):
        """Gets the trend prediction from the QLSTM model for the current step."""
        if self.current_step < 4:
            return np.array([0.5, 0.5]) # Default neutral prediction

        # Get the last 4 days of data
        features_to_scale = ['Open', 'High', 'Low', 'Close', 'MA5', 'MA10']
        sequence_data = self.data[features_to_scale].iloc[self.current_step-4 : self.current_step].values
        sequence_tensor = torch.tensor(sequence_data, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            prediction = self.qlstm_model(sequence_tensor).numpy().flatten()
        return prediction

    def _get_state(self):
        """
        Constructs the 10-dimensional state vector for the QA3C agent,
        as described in Table I of the paper.
        """
        current_price = self.data['Close'].iloc[self.current_step]
        
        # 1 & 2: QLSTM Probabilities
        qlstm_preds = self._get_qlstm_prediction()
        qlstm_bullish_prob = qlstm_preds[1] # Probability of 'up'
        qlstm_bearish_prob = qlstm_preds[0] # Probability of 'down'

        # 3: Cash Ratio
        cash_ratio = self.cash / self.initial_capital
        
        # 4: Holdings Ratio
        self.holdings_value = self.position_size * current_price
        holdings_ratio = self.holdings_value / self.initial_capital

        # 5: Unrealized P&L %
        unrealized_pnl_pct = 0
        if self.position_size > 0:
            unrealized_pnl_pct = (current_price - self.average_cost) / self.average_cost
        
        # 6: Average Price Ratio
        avg_price_ratio = (current_price - self.average_cost) / current_price if self.position_size > 0 else 0
        
        # 7 & 8: Price-to-MA Deviations
        price_to_ma20_dev = (current_price - self.data['MA20'].iloc[self.current_step]) / self.data['MA20'].iloc[self.current_step]
        price_to_ma60_dev = (current_price - self.data['MA60'].iloc[self.current_step]) / self.data['MA60'].iloc[self.current_step]
        
        # 9: MA5 vs MA20 Gap
        ma5_vs_ma20_gap = self.data['MA5'].iloc[self.current_step] - self.data['MA20'].iloc[self.current_step]
        
        # 10: 20-day Relative Volatility
        volatility = self.data['Volatility'].iloc[self.current_step]

        return np.array([
            qlstm_bullish_prob, qlstm_bearish_prob, cash_ratio, holdings_ratio,
            unrealized_pnl_pct, avg_price_ratio, price_to_ma20_dev,
            price_to_ma60_dev, ma5_vs_ma20_gap, volatility
        ])

    def reset(self):
        """Resets the environment to the initial state."""
        self.current_step = 0
        self.cash = self.initial_capital
        self.holdings_value = 0
        self.position_size = 0
        self.average_cost = 0
        self.total_trades = 0
        self.history = []
        return self._get_state()

    def step(self, action):
        """
        Executes one time step in the environment.
        Action: 0=hold, 1=buy, 2=sell
        """
        current_price = self.data['Close'].iloc[self.current_step]
        done = self.current_step >= len(self.data) - 1
        reward = 0

        # --- Reward Calculation (from Table III in the paper) ---
        # 1. Time Cost (daily penalty)
        reward -= 0.02
        
        # 2. Holding Penalty (for unrealized losses)
        if self.position_size > 0:
            pnl_pct = (current_price - self.average_cost) / self.average_cost
            if pnl_pct < 0:
                reward += -5 * (pnl_pct ** 2) # Quadratic penalty

        # --- Action Execution ---
        if action == 1: # Buy
            if self.cash > current_price:
                # Buy one unit (e.g., one share)
                self.position_size += 1
                self.cash -= current_price
                self.average_cost = (self.average_cost * (self.position_size - 1) + current_price) / self.position_size
                self.total_trades += 1
                # Entry Reward/Penalty
                if current_price > self.data['MA20'].iloc[self.current_step]:
                    reward += 0.5 # Reward for trend-following
                else:
                    reward -= 2.0 # Penalty for counter-trend
            else:
                reward -= 0.1 # Penalty for invalid action (insufficient funds)

        elif action == 2: # Sell
            if self.position_size > 0:
                pnl_pct = (current_price - self.average_cost) / self.average_cost
                # Exit Reward/Penalty
                if pnl_pct > 0:
                    reward += 10 + 50 * pnl_pct # Profitable sells
                else:
                    reward += -2 - 10 * abs(pnl_pct) # Losing sells
                
                self.cash += self.position_size * current_price
                self.position_size = 0
                self.average_cost = 0
                self.total_trades += 1
            else:
                reward -= 0.1 # Penalty for invalid action (no holdings to sell)
        
        # --- Update state and history ---
        self.current_step += 1
        next_state = self._get_state() if not done else None
        
        portfolio_value = self.cash + self.holdings_value
        self.history.append({
            'step': self.current_step,
            'portfolio_value': portfolio_value,
            'action': action,
            'reward': reward
        })
        
        # Reward Clipping (as per paper)
        reward = np.clip(reward, -15, 30)

        return next_state, reward, done
