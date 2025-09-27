#!/usr/bin/env python3
"""
Quick start script for Quantum Trading System
Based on Chen et al. research paper
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        return False

def setup_directories():
    """Create necessary directories"""
    directories = [
        "data/raw", "data/processed", 
        "models/saved_models", "logs", 
        "config", "tests", "notebooks"
    ]
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("\nWARNING: .env file not found!")
        print("1. Copy .env.example to .env")
        print("2. Add your Alpaca API keys for paper trading")
        print("3. Get free paper trading keys at: https://alpaca.markets")
        return False
    else:
        print("Found .env file")
        return True

def test_imports():
    """Test core library imports"""
    try:
        import pennylane
        import torch
        import streamlit
        import yfinance
        import pandas
        import numpy
        print("All core libraries imported successfully")
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        print("Try: pip install -r requirements.txt")
        return False

def main():
    print("Quantum Trading System Quick Start")
    print("Based on Chen et al. research paper")
    print("=" * 50)
    
    success = True
    
    # Setup
    print("\n1. Setting up directories...")
    setup_directories()
    
    print("\n2. Installing requirements...")
    if not install_requirements():
        success = False
    
    print("\n3. Testing imports...")
    if not test_imports():
        success = False
    
    print("\n4. Checking configuration...")
    env_exists = check_env_file()
    
    if success:
        print("\nSetup completed successfully!")
        print("\nNext steps:")
        if not env_exists:
            print("1. cp .env.example .env")
            print("2. Edit .env with Alpaca API keys")
        print("3. python src/data_collector.py    # Collect data")
        print("4. python src/train_qlstm.py       # Train QLSTM")
        print("5. streamlit run src/app.py        # Launch app")
        
        print("\nImportant reminders:")
        print("- This implements experimental quantum trading research")
        print("- Always use paper trading first (no real money)")
        print("- Original paper: 11.87% return, 0.92% drawdown on USD/TWD")
    else:
        print("\nSetup encountered issues. Please resolve them before continuing.")

if __name__ == "__main__":
    main()
