import torch
import torch.nn as nn
import pennylane as qml
from pennylane import numpy as np

# Quantum device setup - exact specifications from Chen et al. paper
n_qubits_lstm = 4  # QLSTM quantum circuit
n_qubits_a3c = 8   # QA3C VQC as specified in paper
dev_lstm = qml.device("default.qubit", wires=n_qubits_lstm)
dev_a3c = qml.device("default.qubit", wires=n_qubits_a3c)

# Quantum circuits from Chen et al. paper
@qml.qnode(dev_lstm, interface="torch", diff_method="backprop")
def q_layer_lstm(inputs, weights):
    """QLSTM quantum circuit from Chen et al."""
    # Angle embedding
    for i in range(min(len(inputs), n_qubits_lstm)):
        qml.RY(inputs[i], wires=i)
    
    # Entangling layers
    qml.BasicEntanglerLayers(weights, wires=range(n_qubits_lstm))
    
    return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits_lstm)]

@qml.qnode(dev_a3c, interface="torch", diff_method="backprop") 
def vqc_a3c(inputs, weights):
    """QA3C VQC from Chen et al. - 8 qubits with strong entangling layers"""
    # Angle embedding
    for i in range(min(len(inputs), n_qubits_a3c)):
        qml.RY(inputs[i], wires=i)
    
    # Strongly entangling layers
    qml.StronglyEntanglingLayers(weights, wires=range(n_qubits_a3c))
    
    return qml.expval(qml.PauliZ(0))

class QLSTM(nn.Module):
    """Quantum LSTM from Chen et al. paper"""
    def __init__(self, input_dim=6, hidden_dim=2, sequence_length=4, output_dim=2):
        super(QLSTM, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim  # Paper specifies 2
        self.sequence_length = sequence_length
        
        # Quantum layer
        weight_shapes = {"weights": (1, n_qubits_lstm)}
        self.qlayer_weights = qml.qnn.TorchLayer(q_layer_lstm, weight_shapes)

        # LSTM gates
        self.f_gate = nn.Linear(input_dim + hidden_dim, hidden_dim)
        self.i_gate = nn.Linear(input_dim + hidden_dim, hidden_dim)
        self.c_gate = nn.Linear(input_dim + hidden_dim, hidden_dim)
        self.o_gate = nn.Linear(input_dim + hidden_dim, hidden_dim)

        # Output layer
        self.output = nn.Linear(hidden_dim, output_dim)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        batch_size, seq_len, _ = x.shape
        h_t = torch.zeros(batch_size, self.hidden_dim)
        c_t = torch.zeros(batch_size, self.hidden_dim)

        for t in range(seq_len):
            x_t = x[:, t, :]
            
            # Quantum processing
            q_input = x_t[:, :n_qubits_lstm]
            q_out = self.qlayer_weights(q_input)
            
            # LSTM gates
            combined = torch.cat((h_t, x_t), dim=1)
            f_t = torch.sigmoid(self.f_gate(combined))
            i_t = torch.sigmoid(self.i_gate(combined))
            c_hat_t = torch.tanh(self.c_gate(combined))
            o_t = torch.sigmoid(self.o_gate(combined))
            
            # Update states with quantum enhancement
            c_t = f_t * c_t + i_t * c_hat_t
            h_t = o_t * torch.tanh(c_t + q_out[:, :self.hidden_dim])

        output = self.output(h_t)
        return self.softmax(output)

class QA3C(nn.Module):
    """Quantum A3C from Chen et al. - Target: 244 parameters"""
    def __init__(self, input_dim=10, action_dim=3, hidden_dim=8):
        super(QA3C, self).__init__()
        
        # Classical preprocessing (10 -> 8)
        self.classical_layer = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh()
        )
        
        # Quantum VQC
        weight_shapes = {"weights": (1, n_qubits_a3c, 3)}
        self.vqc = qml.qnn.TorchLayer(vqc_a3c, weight_shapes)
        
        # Actor head
        self.actor_head = nn.Sequential(
            nn.Linear(hidden_dim + 1, 32),
            nn.ReLU(),
            nn.Linear(32, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Critic head
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_dim + 1, 32),
            nn.ReLU(), 
            nn.Linear(32, 1)
        )

    def forward(self, x):
        classical_out = self.classical_layer(x)
        vqc_out = self.vqc(classical_out).unsqueeze(1)
        combined = torch.cat([classical_out, vqc_out], dim=1)
        
        policy = self.actor_head(combined)
        value = self.critic_head(combined)
        
        return policy, value.squeeze()

def count_parameters(model):
    """Count trainable parameters"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

if __name__ == "__main__":
    # Test models
    qlstm = QLSTM()
    qa3c = QA3C()
    
    print(f"QLSTM parameters: {count_parameters(qlstm)}")
    print(f"QA3C parameters: {count_parameters(qa3c)} (target: 244)")
    
    # Test forward passes
    test_seq = torch.randn(1, 4, 6)
    test_state = torch.randn(1, 10)
    
    qlstm_out = qlstm(test_seq)
    qa3c_policy, qa3c_value = qa3c(test_state)
    
    print(f"QLSTM output: {qlstm_out.shape}")
    print(f"QA3C policy: {qa3c_policy.shape}, value: {qa3c_value.shape}")
