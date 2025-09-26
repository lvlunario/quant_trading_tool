import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler

def preprocess_data(ticker, sequence_length=4, prediction_horizon=5, threshold=0.012):
    """
    Reads raw stock data, calculates features and labels, normalizes,
    and creates sequences for the QLSTM model.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
        sequence_length (int): The number of time steps in each input sequence.
        prediction_horizon (int): The number of days to look ahead for labeling.
        threshold (float): The percentage change required to label as 'up' or 'down'.

    Returns:
        tuple: A tuple containing (X, y) for training and the scaler object.
    """
    # --- 1. Load Data ---
    raw_data_path = os.path.join("..", "data")
    files = [f for f in os.listdir(raw_data_path) if f.startswith(ticker)]
    if not files:
        print(f"No raw data file found for {ticker}")
        return None, None, None
    
    file_path = os.path.join(raw_data_path, files[0])
    df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
    df.dropna(inplace=True)

    # --- 2. Feature Engineering ---
    # As described in the paper
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df['Volatility'] = df['Close'].rolling(window=20).std() / df['Close'].rolling(window=20).mean()
    df.dropna(inplace=True)

    # --- 3. Label Creation for QLSTM ---
    # The paper labels based on future price change > +/- 1.2%
    df['future_change'] = (df['Close'].shift(-prediction_horizon) - df['Close']) / df['Close']
    
    conditions = [
        df['future_change'] > threshold,
        df['future_change'] < -threshold
    ]
    choices = [1, 0] # 1 for 'up', 0 for 'down'
    df['label'] = np.select(conditions, choices, default=-1) # -1 for intermediate cases

    # We only train on clear up/down signals
    df = df[df['label'] != -1].copy()

    # --- 4. Normalization ---
    # The paper uses min-max scaling
    features_to_scale = ['Open', 'High', 'Low', 'Close', 'MA5', 'MA10']
    scaler = MinMaxScaler(feature_range=(0, 1))
    df[features_to_scale] = scaler.fit_transform(df[features_to_scale])

    # --- 5. Sequence Creation ---
    X, y = [], []
    for i in range(len(df) - sequence_length):
        # The input sequence
        X.append(df[features_to_scale].iloc[i:i+sequence_length].values)
        # The label corresponds to the end of the sequence
        y.append(df['label'].iloc[i+sequence_length-1])

    # --- 6. Save Processed Data ---
    processed_file_path = os.path.join(raw_data_path, f"{ticker}_processed.csv")
    df.to_csv(processed_file_path)
    print(f"Saved processed data to {processed_file_path}")

    return np.array(X), np.array(y), scaler


if __name__ == '__main__':
    # We'll use Apple as our primary stock for development
    TICKER = "AAPL"
    X_train, y_train, data_scaler = preprocess_data(TICKER)
    
    if X_train is not None:
        print(f"Created {len(X_train)} sequences for training.")
        print("Shape of X_train:", X_train.shape)
        print("Shape of y_train:", y_train.shape)
