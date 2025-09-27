import torch
import torch.optim as optim
import numpy as np
import pandas as pd
from collections import deque

from models import QA3C, vqc_a3c, n_qubits_a3c
from backtest_engine import TradingEnvironment

# --- Configuration ---
TICKER = "USDTWD=X"
QLSTM_MODEL_PATH = "models/saved_models/qlstm_best.pth"
AGENT_SAVE_PATH = "models/saved_models/qa3c_agent.pth"
INPUT_DIM = 10 # State vector dimension
ACTION_DIM = 3   # Hold, Buy, Sell
MAX_EPISODES = 2000
GAMMA = 0.995 # Discount factor from paper
LEARNING_RATE = 1e-5
BETA_ENTROPY = 0.05 # Entropy regularization term

def train_qa3c():
    """Main training loop for the QA3C agent."""
    print("1. Setting up the environment and agent...")
    
    # Load data
    data_path = f"data/processed/{TICKER}_processed.csv"
    try:
        data = pd.read_csv(data_path, index_col='Date', parse_dates=True)
    except FileNotFoundError:
        print(f"Error: Processed data not found at {data_path}")
        print("Please run data collection and QLSTM training first via the Streamlit app.")
        return

    # Split data into train and test sets (80/20 split)
    split_index = int(len(data) * 0.8)
    train_data = data.iloc[:split_index]

    # Initialize environment and agent
    env = TradingEnvironment(train_data, QLSTM_MODEL_PATH)
    agent = QA3C(input_dim=INPUT_DIM, q_layer=vqc_a3c, n_qubits=n_qubits_a3c, action_dim=ACTION_DIM)
    optimizer = optim.Adam(agent.parameters(), lr=LEARNING_RATE)

    print("2. Starting QA3C agent training...")
    scores = deque(maxlen=100)

    for episode in range(MAX_EPISODES):
        state = env.reset()
        episode_reward = 0
        done = False
        
        saved_log_probs = []
        saved_values = []
        rewards = []

        # --- A single episode rollout ---
        while not done:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            policy, value = agent(state_tensor)

            # Sample action from policy distribution
            action_probs = torch.distributions.Categorical(policy)
            action = action_probs.sample()

            # Store log probability and value
            saved_log_probs.append(action_probs.log_prob(action))
            saved_values.append(value)

            # Step the environment
            next_state, reward, done = env.step(action.item())
            
            rewards.append(reward)
            episode_reward += reward
            state = next_state

        scores.append(episode_reward)

        # --- Calculate losses and update agent ---
        returns = []
        R = 0
        for r in rewards[::-1]:
            R = r + GAMMA * R
            returns.insert(0, R)
        
        returns = torch.tensor(returns)
        returns = (returns - returns.mean()) / (returns.std() + 1e-9)

        log_probs = torch.cat(saved_log_probs)
        values = torch.cat(saved_values)

        advantage = returns - values

        # Calculate actor (policy) and critic (value) loss
        policy_loss = (-log_probs * advantage.detach()).mean()
        value_loss = advantage.pow(2).mean()

        # Entropy loss for exploration
        entropy = -(torch.exp(log_probs) * log_probs).mean()
        entropy_loss = -BETA_ENTROPY * entropy

        # Total loss
        loss = policy_loss + value_loss + entropy_loss

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if (episode + 1) % 100 == 0:
            avg_score = np.mean(scores)
            print(f"Episode {episode+1}/{MAX_EPISODES} | Average Reward (last 100): {avg_score:.2f}")

    print("\n3. Training complete.")
    torch.save(agent.state_dict(), AGENT_SAVE_PATH)
    print(f"Trained agent saved to {AGENT_SAVE_PATH}")

if __name__ == '__main__':
    train_qa3c()
