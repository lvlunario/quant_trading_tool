import torch
import torch.optim as optim
import numpy as np
import pandas as pd
from collections import deque
from tqdm import tqdm
import os

from models import QA3C
from backtest_engine import TradingEnvironment

# --- Professional Hyperparameters ---
TICKER = "AAPL"
QLSTM_MODEL_PATH = "models/saved_models/qlstm_best.pth"
AGENT_SAVE_PATH = "models/saved_models/qa3c_agent.pth"
INPUT_DIM = 5
ACTION_DIM = 3
MAX_EPISODES = 10000
MAX_STEPS_PER_EPISODE = 252
GAMMA = 0.99
LEARNING_RATE = 1e-5
BETA_ENTROPY = 0.01

def train_qa3c():
    print("1. Setting up professional environment and agent...")
    data_path = f"data/processed/{TICKER}_processed.csv"
    try:
        data = pd.read_csv(data_path, index_col='Date', parse_dates=True)
    except FileNotFoundError:
        print(f"Error: Data for {TICKER} not found. Please run the data collector."); return

    train_data = data.iloc[:int(len(data) * 0.8)]
    env = TradingEnvironment(train_data, QLSTM_MODEL_PATH)
    agent = QA3C(input_dim=INPUT_DIM, action_dim=ACTION_DIM)
    optimizer = optim.Adam(agent.parameters(), lr=LEARNING_RATE)
    
    print(f"2. Starting professional training for {TICKER}...")
    scores = deque(maxlen=100)
    progress_bar = tqdm(range(MAX_EPISODES), desc="Training Agent")

    for episode in progress_bar:
        state = env.reset()
        if state is None: continue

        log_probs, values, rewards, entropies = [], [], [], []

        for step in range(MAX_STEPS_PER_EPISODE):
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            policy_logits, value = agent(state_tensor)
            
            # --- DEFINITIVE FIX: Use logits for numerical stability ---
            action_probs = torch.distributions.Categorical(logits=policy_logits)
            action = action_probs.sample()

            log_probs.append(action_probs.log_prob(action))
            values.append(value)
            entropies.append(action_probs.entropy())

            state, reward, done = env.step(action.item())
            rewards.append(reward)
            if done: break
        
        scores.append(sum(rewards))
        if not log_probs: continue
            
        returns, R = [], 0
        for r in rewards[::-1]:
            R = r + GAMMA * R
            returns.insert(0, R)
        
        returns = torch.tensor(returns, dtype=torch.float32)
        if len(returns) > 1: returns = (returns - returns.mean()) / (returns.std() + 1e-8)

        advantage = returns - torch.cat(values).squeeze().detach()
        policy_loss = -(torch.cat(log_probs).squeeze() * advantage).mean()
        value_loss = 0.5 * advantage.pow(2).mean()
        entropy_loss = -BETA_ENTROPY * torch.cat(entropies).mean()

        optimizer.zero_grad()
        (policy_loss + value_loss + entropy_loss).backward()
        torch.nn.utils.clip_grad_norm_(agent.parameters(), 1.0)
        optimizer.step()

        if (episode + 1) % 100 == 0:
            avg_score = np.mean(scores) if scores else 0
            progress_bar.set_description(f"Avg Reward: {avg_score:.4f}")

    print("\n3. Training complete."); torch.save(agent.state_dict(), AGENT_SAVE_PATH)

if __name__ == '__main__':
    train_qa3c()

