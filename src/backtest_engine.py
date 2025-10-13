import numpy as np
import torch
import os

class TradingEnvironment:
    """
    A professionally refactored trading environment using a Sharpe Ratio-based reward system.
    This teaches the agent to maximize risk-adjusted returns, which is the
    primary goal of professional quantitative trading.
    """
    def __init__(self, data, initial_capital=50000, trade_size_percent=0.25):
        self.data_columns = {col: i for i, col in enumerate(data.columns)}
        self.data = data.to_numpy()
        self.initial_capital = initial_capital
        self.trade_size_percent = trade_size_percent
        self.epsilon = 1e-8
        self.reset()

    def _get_state(self):
        """Constructs the state vector from the current market data."""
        if self.current_step >= len(self.data): return None
        
        row = self.data[self.current_step]
        price = row[self.data_columns['Close']]
        portfolio_value = self.cash + (self.position_size * price)

        return np.array([
            self.position_size > 0, # Is holding a position? (1 or 0)
            row[self.data_columns['RSI']],
            row[self.data_columns['MACD']],
            row[self.data_columns['MACD_Signal']],
            row[self.data_columns['Volatility']]
        ])

    def reset(self):
        self.current_step = 0
        self.cash = self.initial_capital
        self.position_size = 0
        self.daily_returns = []
        self.history = [{'value': self.initial_capital}]
        return self._get_state()

    def step(self, action):
        """Action: 0 (Hold), 1 (Buy), 2 (Sell)"""
        current_price = self.data[self.current_step, self.data_columns['Close']]
        
        if action == 1 and self.cash > 0: # Buy
            buy_amount = self.cash * self.trade_size_percent
            self.position_size += buy_amount / (current_price + self.epsilon)
            self.cash -= buy_amount
        elif action == 2 and self.position_size > 0: # Sell
            sell_amount = self.position_size * self.trade_size_percent * current_price
            self.position_size -= self.position_size * self.trade_size_percent
            self.cash += sell_amount

        self.current_step += 1
        done = self.current_step >= len(self.data)

        new_portfolio_value = self.cash + (self.position_size * current_price)
        last_portfolio_value = self.history[-1]['value']
        
        daily_return = (new_portfolio_value - last_portfolio_value) / (last_portfolio_value + self.epsilon)
        self.daily_returns.append(daily_return)

        # The professional's reward: The rolling Sharpe Ratio
        if len(self.daily_returns) > 20:
            rolling_returns = np.array(self.daily_returns[-20:])
            reward = (rolling_returns.mean() / (rolling_returns.std() + self.epsilon))
        else:
            reward = 0 # Not enough data for Sharpe yet

        self.history.append({'value': new_portfolio_value})
        next_state = self._get_state() if not done else None
        
        return next_state, reward, done

