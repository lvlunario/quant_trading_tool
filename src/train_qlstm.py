import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
import numpy as np
import os

# Import the model definitions
from models import QLSTM, q_layer_lstm, n_qubits_lstm
from data_preprocessor import preprocess_data

# --- Configuration ---
TICKER = "AAPL"
INPUT_DIM = 6   # Open, High, Low, Close, MA5, MA10
HIDDEN_DIM = 4  # A small hidden dimension for this simple task
OUTPUT_DIM = 2  # Probabilities for 'up' or 'down'
EPOCHS = 50
LEARNING_RATE = 5e-3 # From the paper
BATCH_SIZE = 32
MODEL_SAVE_PATH = "qlstm_forecaster.pth"

# --- Main Training Logic ---
def train():
    print("1. Preprocessing data...")
    X, y, _ = preprocess_data(TICKER)
    if X is None:
        return
        
    # Split data into training and validation sets
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Convert to PyTorch Tensors
    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_val_t = torch.tensor(X_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val, dtype=torch.long)

    # Create DataLoaders
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_dataset = TensorDataset(X_val_t, y_val_t)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    print("2. Initializing QLSTM model...")
    model = QLSTM(
        input_dim=INPUT_DIM,
        hidden_dim=HIDDEN_DIM,
        q_layer=q_layer_lstm,
        n_qubits=n_qubits_lstm,
        output_dim=OUTPUT_DIM
    )
    
    # Loss and Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.RMSprop(model.parameters(), lr=LEARNING_RATE) # As per the paper

    print("3. Starting training...")
    for epoch in range(EPOCHS):
        model.train()
        total_train_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_train_loss += loss.item()

        # Validation
        model.eval()
        total_val_loss = 0
        correct = 0
        total = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                total_val_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += batch_y.size(0)
                correct += (predicted == batch_y).sum().item()

        avg_train_loss = total_train_loss / len(train_loader)
        avg_val_loss = total_val_loss / len(val_loader)
        accuracy = 100 * correct / total
        
        print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Accuracy: {accuracy:.2f}%")

    print("\n4. Training complete.")
    
    # Save the trained model
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"Model saved to {MODEL_SAVE_PATH}")


if __name__ == '__main__':
    train()
