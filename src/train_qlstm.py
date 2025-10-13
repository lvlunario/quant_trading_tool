import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import os
from models import QLSTM

def load_processed_data(ticker="AAPL"):
    filepath = f"data/processed/{ticker}_processed.csv"
    if not os.path.exists(filepath):
        print(f"Error: Processed data not found for {ticker}.")
        return None
    return pd.read_csv(filepath, index_col=0, parse_dates=True)

def create_sequences(data, sequence_length=4):
    features = ['Open', 'High', 'Low', 'Close', 'MA5', 'MA10']
    X, y = [], []
    for i in range(sequence_length, len(data)):
        if data['label'].iloc[i] != -1:
            X.append(data[features].iloc[i-sequence_length:i].values)
            y.append(data['label'].iloc[i])
    return np.array(X), np.array(y)

def train_qlstm():
    """Trains the QLSTM model on the specified ticker."""
    print("--- Training QLSTM Forecaster ---")
    TICKER = "AAPL" # Train on a primary stock
    
    data = load_processed_data(TICKER)
    if data is None: return
    
    X, y = create_sequences(data)
    if len(X) == 0:
        print("No valid sequences found for training.")
        return
        
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    train_loader = DataLoader(TensorDataset(torch.FloatTensor(X_train), torch.LongTensor(y_train)), batch_size=32, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.FloatTensor(X_val), torch.LongTensor(y_val)), batch_size=32)
    
    model = QLSTM()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    best_accuracy = 0
    print(f"Starting QLSTM training for {TICKER}...")
    for epoch in range(50):
        model.train()
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
        
        model.eval()
        correct, total = 0, 0
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
            print(f"Epoch {epoch+1}: New best accuracy: {accuracy:.2f}%. Model saved.")
    
    print(f"\nTraining complete! Best validation accuracy: {best_accuracy:.2f}%")

if __name__ == "__main__":
    train_qlstm()
