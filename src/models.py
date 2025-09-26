import torch
import torch.nn as nn
import pennylane as qml
from pennylane import numpy as np

# --- Quantum Device Setup ---
# The number of qubits will be determined by the feature dimension in the models
# We use the 'default.qubit' simulator
n_qubits_lstm = 4 # As an example for the quantum part of LSTM
n_qubits_a3c = 8 # As specified in the paper for the QA3C agent
dev_lstm = qml.device("default.qubit", wires=n_qubits_lstm)
dev_a3c = qml.device("default.qubit", wires=n_qubits_a3c)

# --- Quantum Layers ---
# These are the quantum circuits that will be embedded in our PyTorch models.

@qml.qnode(dev_lstm, interface="torch", diff_method="backprop")
def q_layer_lstm(inputs, weights):
    """A simple variational quantum circuit for the QLSTM."""
    qml.AngleEmbedding(inputs, wires=range(n_qubits_lstm))
    qml.BasicEntanglerLayers(weights, wires=range(n_qubits_lstm))
    return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits_lstm)]

@qml.qnode(dev_a3c, interface="torch", diff_method="backprop")
def vqc_a3c(inputs, weights):
    """Variational Quantum Circuit for the QA3C agent, as per the paper."""
    qml.AngleEmbedding(inputs, wires=range(n_qubits_a3c))
    qml.StronglyEntanglingLayers(weights, wires=range(n_qubits_a3c))
    return qml.expval(qml.PauliZ(0))

# --- Model Definitions ---

class QLSTM(nn.Module):
    """
    Quantum Long Short-Term Memory Network.
    This model acts as the trend forecaster.
    """
    def __init__(self, input_dim, hidden_dim, q_layer, n_qubits, output_dim=2):
        super(QLSTM, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Quantum layer setup
        self.q_layer = q_layer
        weight_shapes = {"weights": (1, n_qubits)} # 1 layer, n_qubits params
        self.qlayer_weights = qml.qnn.TorchLayer(self.q_layer, weight_shapes)

        # Classical layers for the LSTM gates
        self.f_gate = nn.Linear(input_dim + hidden_dim, hidden_dim)
        self.i_gate = nn.Linear(input_dim + hidden_dim, hidden_dim)
        self.c_gate = nn.Linear(input_dim + hidden_dim, hidden_dim)
        self.o_gate = nn.Linear(input_dim + hidden_dim, hidden_dim)

        # Output layer
        self.output = nn.Linear(hidden_dim, output_dim)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        batch_size, seq_len, _ = x.shape
        h_t, c_t = (torch.zeros(batch_size, self.hidden_dim),
                    torch.zeros(batch_size, self.hidden_dim))

        for t in range(seq_len):
            x_t = x[:, t, :]
            
            # Here we integrate the quantum layer.
            # A simple way is to process a part of the input through the quantum layer.
            # Let's use the first n_qubits features of the input for the quantum circuit.
            q_input = x_t[:, :n_qubits_lstm]
            q_out = self.qlayer_weights(q_input)
            
            # For simplicity, we concatenate the quantum output with the rest of the input
            # A more complex integration could replace one of the gates entirely.
            combined = torch.cat((h_t, x_t), dim=1)
            
            f = torch.sigmoid(self.f_gate(combined))
            i = torch.sigmoid(self.i_gate(combined))
            c_hat = torch.tanh(self.c_gate(combined))
            o = torch.sigmoid(self.o_gate(combined))
            
            c_t = f * c_t + i * c_hat
            # We can use the quantum output to modulate the hidden state
            h_t = o * torch.tanh(c_t + q_out)

        out = self.output(h_t)
        return self.softmax(out)


class QA3C(nn.Module):
    """
    Quantum Asynchronous Advantage Actor-Critic.
    This is the reinforcement learning agent for decision making.
    """
    def __init__(self, input_dim, q_layer, n_qubits, action_dim=3):
        super(QA3C, self).__init__()
        self.input_dim = input_dim
        
        # Classical pre-processing layer as in the paper
        self.classical_layer = nn.Sequential(
            nn.Linear(input_dim, n_qubits),
            nn.Tanh()
        )
        
        # Quantum layer
        weight_shapes = {"weights": (1, n_qubits, 3)} # 1 layer, n_qubits, 3 params per gate
        self.vqc = qml.qnn.TorchLayer(q_layer, weight_shapes)
        
        # Output heads: one for policy (actor), one for value (critic)
        # In the paper, the VQC output is fed to two linear heads.
        # Since our VQC outputs a single value, we'll add a small classical layer.
        self.actor_head = nn.Sequential(
            nn.Linear(1 + n_qubits, 32),
            nn.ReLU(),
            nn.Linear(32, action_dim),
            nn.Softmax(dim=-1) # Probabilities for actions
        )
        self.critic_head = nn.Sequential(
            nn.Linear(1 + n_qubits, 32),
            nn.ReLU(),
            nn.Linear(32, 1) # Single value estimate
        )

    def forward(self, x):
        classical_out = self.classical_layer(x)
        vqc_out = self.vqc(classical_out).unsqueeze(1)
        
        # Combine classical and quantum outputs to feed into heads
        combined_features = torch.cat((classical_out, vqc_out), dim=1)
        
        policy = self.actor_head(combined_features)
        value = self.critic_head(combined_features)
        
        return policy, value
