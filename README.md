# Quantum Trading System

Implementation of quantum-enhanced algorithmic trading based on:

**"Quantum-Enhanced Forecasting for Deep Reinforcement Learning in Algorithmic Trading"**  
*by Jun-Hao Chen, Yu-Chien Huang, Yun-Cheng Tsai, Samuel Yen-Chi Chen*

## Research Results

- **Asset**: USD/TWD currency pair
- **Period**: 2020-2025 (~5 years testing)
- **Return**: 11.87% total return
- **Risk**: 0.92% maximum drawdown
- **Trades**: 231 total trades
- **Win Rate**: 56.7%

## Quantum Components

### QLSTM (Quantum Long Short-Term Memory)
- **Architecture**: 4-qubit quantum circuit + classical LSTM
- **Input**: 4-day sequences, 6 features (OHLC + MA5 + MA10)
- **Output**: Binary prediction (up/down > ±1.2% in 5 days)
- **Accuracy**: ~71.5% on USD/TWD data

### QA3C (Quantum Asynchronous Advantage Actor-Critic)
- **Architecture**: 8-qubit VQC + classical heads
- **Parameters**: 244 total (32 quantum + 212 classical)
- **Actions**: Hold (0), Buy (1), Sell (2)
- **Training**: Multi-worker asynchronous learning

## Quick Start

1. **Setup Environment**
```bash
python -m venv trading_env
source trading_env/bin/activate  # Windows: trading_env\Scripts\activate
pip install -r requirements.txt
```

2. **Configure API Keys**
```bash
cp .env.example .env
# Edit .env with your Alpaca paper trading keys
```

3. **Collect Data**
```bash
python src/data_collector.py
```

4. **Train Models**
```bash
python src/train_qlstm.py
```

5. **Run Application**
```bash
streamlit run src/app.py
```

## Important Disclaimers

- **Research Implementation**: Academic research implementation only
- **Experimental Technology**: Quantum computing in finance is experimental
- **No Financial Advice**: Educational purposes only
- **Use Paper Trading**: Test with virtual money first
- **Single Asset Study**: Original results only on USD/TWD
- **Classical Simulation**: Uses classical quantum circuit simulation

## Project Structure

```
trading_system/
├── src/
│   ├── app.py                 # Streamlit web application
│   ├── models.py              # QLSTM and QA3C implementations
│   ├── train_qlstm.py         # QLSTM training script
│   ├── data_collector.py      # Enhanced data collection
│   └── paper_trading.py       # Alpaca integration (future)
├── data/
│   ├── raw/                   # Raw downloaded data
│   └── processed/             # Preprocessed data for models
├── models/saved_models/       # Trained model files
├── config/                    # Configuration files
├── tests/                     # Unit tests
├── notebooks/                 # Analysis notebooks
└── deployment/                # Docker and deployment files
```

## License

MIT License - See LICENSE file for details

## Contact

Based on academic research. For questions about the methodology, refer to the original Chen et al. paper.
