import torch
import torch.nn as nn

class ActorCritic(nn.Module):
    """
    A professionally refactored, deep classical Actor-Critic model.
    This provides a strong, stable foundation for the agent's decision-making process.
    """
    def __init__(self, input_dim, action_dim):
        super(ActorCritic, self).__init__()

        self.shared_layers = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )

        self.actor_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )

        self.critic_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        """Processes the state and returns action logits and a state value."""
        shared_features = self.shared_layers(x)
        action_logits = self.actor_head(shared_features)
        value = self.critic_head(shared_features)
        return action_logits, value

