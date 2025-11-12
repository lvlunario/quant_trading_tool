import torch
import torch.optim as optim
import numpy as np
import pandas as pd
from collections import deque
from tqdm import tqdm
import os

from models import ActorCritic
from backtest_engine import TradingEnvironment

# --- Professional Hyperparameters ---
TICKER = "AAPL"
AGENT_SAVE_PATH = "models/saved_models/agent.pth"
INPUT_DIM = 5
ACTION_DIM = 3
MAX_EPISODES = 10000
MAX_STEPS_PER_EPISODE = 252
GAMMA = 0.99
LEARNING_RATE = 3e-4
BETA_ENTROPY = 0.01
PPO_EPSILON = 0.2 # PPO clipping parameter
PPO_EPOCHS = 10 # Number of optimization epochs per episode

def train_agent():
    print("1. Setting up professional environment and agent...")
    data_path = f"data/processed/{TICKER}_processed.csv"
    try:
        data = pd.read_csv(data_path, index_col='Date', parse_dates=True)
    except FileNotFoundError:
        print(f"Error: Data for {TICKER} not found. Run the data collector."); return

    train_data = data.iloc[:int(len(data) * 0.8)]
    env = TradingEnvironment(train_data)
    agent = ActorCritic(input_dim=INPUT_DIM, action_dim=ACTION_DIM)
    optimizer = optim.Adam(agent.parameters(), lr=LEARNING_RATE)
    
    print(f"2. Starting professional PPO-style training for {TICKER}...")
    scores = deque(maxlen=100)
    progress_bar = tqdm(range(MAX_EPISODES), desc="Training Agent")

    for episode in progress_bar:
        state = env.reset()
        if state is None: continue

        log_probs, values, rewards, states, actions, dones = [], [], [], [], [], []

        for step in range(MAX_STEPS_PER_EPISODE):
            states.append(torch.FloatTensor(state).unsqueeze(0))
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            
            with torch.no_grad():
                policy_logits, value = agent(state_tensor)

            action_dist = torch.distributions.Categorical(logits=policy_logits)
            action = action_dist.sample()
            
            actions.append(action)
            log_probs.append(action_dist.log_prob(action))
            values.append(value)

            state, reward, done = env.step(action.item())
            rewards.append(reward)
            dones.append(done)
            if done: break
        
        scores.append(sum(rewards))

        # --- PPO Update Logic ---
        states = torch.cat(states)
        actions = torch.cat(actions)
        old_log_probs = torch.cat(log_probs).detach()
        
        returns, R = [], 0
        for r, done in zip(rewards[::-1], dones[::-1]):
            R = r + GAMMA * R * (1 - done)
            returns.insert(0, R)
        
        returns = torch.tensor(returns, dtype=torch.float32)
        if len(returns) > 1: returns = (returns - returns.mean()) / (returns.std() + 1e-8)

        for _ in range(PPO_EPOCHS):
            policy_logits, value = agent(states)
            value = value.squeeze()
            
            new_dist = torch.distributions.Categorical(logits=policy_logits)
            new_log_probs = new_dist.log_prob(actions)
            entropy = new_dist.entropy().mean()

            advantage = returns - value.detach()
            
            # PPO Clipped Objective
            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantage
            surr2 = torch.clamp(ratio, 1 - PPO_EPSILON, 1 + PPO_EPSILON) * advantage
            
            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = 0.5 * (returns - value).pow(2).mean()
            
            loss = actor_loss + critic_loss - BETA_ENTROPY * entropy
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(agent.parameters(), 1.0)
            optimizer.step()

        if (episode + 1) % 100 == 0:
            avg_score = np.mean(scores) if scores else 0
            progress_bar.set_description(f"Avg Reward (Sharpe): {avg_score:.4f}")

    print("\n3. Training complete."); torch.save(agent.state_dict(), AGENT_SAVE_PATH)

if __name__ == '__main__':
    train_agent()