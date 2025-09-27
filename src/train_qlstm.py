import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import os
from models import QLSTM, count_parameters

def load_processed_data(ticker="USDTWD=X"):
    """Load preprocessed data"""
    filepath = f"data/processed/{ticker}_processed.csv"
    if not os.path.exists(filepath):
        print(f"Processed data not found: {filepath}")
        print("Run data collection first: python src/data_collector.py")
        return None, None
    
    data = pd.read_csv(filepath, index_col=0, parse_dates=True)
    return data

def create_sequences(data, sequence_length=4):
    """Create sequences for QLSTM"""
    features = ['Open', 'High', 'Low', 'Close', 'MA5', 'MA10']
    
    X, y = [], []
    for i in range(sequence_length, len(data)):
        if data['label'].iloc[i] != -1:  # Valid label
            sequence = data[features].iloc[i-sequence_length:i].values
            label = data['label'].iloc[i]
            X.append(sequence)
            y.append(label)
    
    return np.array(X), np.array(y)

def train_qlstm():
    """Train QLSTM model"""
    print("Training QLSTM based on Chen et al. methodology")
    print("=" * 50)
    
    # Load data
    data = load_processed_data("USDTWD=X")
    if data is None:
        return
    
    # Create sequences
    X, y = create_sequences(data)
    print(f"Created {len(X)} sequences")
    
    if len(X) == 0:
        print("No valid sequences found!")
        return
    
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.LongTensor(y_train)
    X_val_t = torch.FloatTensor(X_val)
    y_val_t = torch.LongTensor(y_val)
    
    # Create data loaders
    train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=32, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val_t, y_val_t), batch_size=32)
    
    # Initialize model
    model = QLSTM(input_dim=6, hidden_dim=2, sequence_length=4, output_dim=2)
    print(f"Model parameters: {count_parameters(model)}")
    
    # Training setup
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.RMSprop(model.parameters(), lr=5e-3)
    
    # Training loop
    best_accuracy = 0
    for epoch in range(50):
        # Training
        model.train()
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        # Validation
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                outputs = model(batch_X)
                _, predicted = torch.max(outputs, 1)
                total += batch_y.size(0)
                correct += (predicted == batch_y).sum().item()
        
        accuracy = 100 * correct / total
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            torch.save(model.state_dict(), "models/saved_models/qlstm_best.pth")
        
        if epoch % 10 == 0:
            print(f"Epoch {epoch}: Loss={total_loss/len(train_loader):.4f}, Acc={accuracy:.2f}%")
    
    print(f"Training completed! Best accuracy: {best_accuracy:.2f}%")
    print("Paper target: ~71.5%")

if __name__ == "__main__":
    train_qlstm()
