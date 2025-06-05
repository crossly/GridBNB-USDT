# GridTrading Pro v2.0.0

**Advanced Grid Trading System for Binance Spot and Futures**

GridTrading Pro is a sophisticated, modular grid trading system that supports both Binance Spot and USDT-M Futures trading with advanced risk management, dynamic grid adjustment, and comprehensive notification system.

## 🚀 Key Features

### Trading Capabilities
- **Multi-Mode Support**: Binance Spot and USDT-M Futures trading
- **Dynamic Grid Trading**: Automatic grid size adjustment based on market volatility
- **Custom Trading Pairs**: Support for any Binance trading pair
- **Leverage Configuration**: Configurable leverage for futures trading (1x-125x)
- **S1 Strategy**: Advanced position management based on 52-day high/low breakouts

### Risk Management
- **Multi-Layer Protection**: Position limits, drawdown control, daily loss limits
- **Real-time Monitoring**: Continuous risk assessment and alerts
- **Position Management**: Automatic position sizing and rebalancing
- **Emergency Stop**: Automatic trading halt on critical risk events

### Notifications & Monitoring
- **Telegram Integration**: Real-time trade notifications and system alerts
- **Web Dashboard**: Live monitoring interface with charts and statistics
- **Comprehensive Logging**: Detailed logging with rotation and backup
- **Performance Analytics**: Trade statistics, profit tracking, and performance metrics

### Technical Features
- **Testnet Support**: Safe testing environment for strategy development
- **State Persistence**: Automatic state saving and recovery
- **Modular Architecture**: Clean, extensible codebase
- **Error Handling**: Robust error handling with automatic recovery
- **Data Export/Import**: Backup and restore trading data

## 📋 Requirements

- Python 3.8+
- Binance API credentials
- Telegram Bot (for notifications)
- Minimum 1GB RAM, 1 CPU core
- Stable internet connection

## 🛠 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd "GridTrading Pro"
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration Setup

#### Copy Environment Template
```bash
cp .env.example .env
```

#### Edit Configuration Files
1. **Edit `.env`** with your credentials:
```env
# Binance API Credentials
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional Settings
INITIAL_PRINCIPAL=1000.0
INITIAL_BASE_PRICE=600.0
```

2. **Edit `config.yaml`** for trading parameters:
```yaml
trading:
  mode: "spot"  # or "futures"
  symbol: "BNB/USDT"
  leverage: 1  # for futures mode
  testnet: false

grid:
  initial_size: 2.0
  min_size: 1.0
  max_size: 4.0
  dynamic_adjustment: true

risk:
  max_drawdown: -0.15
  daily_loss_limit: -0.05
  max_position_ratio: 0.9
  min_position_ratio: 0.1
```

## 🚀 Usage

### Basic Usage
```bash
# Start with default configuration
python main.py

# Use custom config file
python main.py --config my_config.yaml

# Enable testnet mode
python main.py --testnet

# Dry run (no actual trading)
python main.py --dry-run
```

### Trading Modes

#### Spot Trading
```yaml
trading:
  mode: "spot"
  symbol: "BTC/USDT"
  leverage: 1  # Always 1 for spot
```

#### Futures Trading
```yaml
trading:
  mode: "futures"
  symbol: "BTC/USDT"
  leverage: 10  # 1x to 125x
```

### Supported Trading Pairs
- BTC/USDT, ETH/USDT, BNB/USDT
- ADA/USDT, DOT/USDT, LINK/USDT
- And many more major cryptocurrencies

## 📊 Web Dashboard

Access the web dashboard at: `http://localhost:58181`

Features:
- Real-time price and position monitoring
- Trade history and analytics
- System status and uptime
- Risk metrics and alerts
- Grid visualization

## 🔔 Telegram Notifications

### Setup Telegram Bot
1. Create bot with [@BotFather](https://t.me/botfather)
2. Get bot token and chat ID
3. Configure in `.env` file

### Notification Types
- **Trade Execution**: Buy/sell order confirmations
- **Risk Alerts**: Position and drawdown warnings
- **System Status**: Startup, shutdown, errors
- **Strategy Signals**: Grid adjustments, S1 triggers

## ⚙️ Configuration Guide

### Grid Trading Parameters
```yaml
grid:
  initial_size: 2.0      # Initial grid size (%)
  min_size: 1.0          # Minimum grid size (%)
  max_size: 4.0          # Maximum grid size (%)
  dynamic_adjustment: true # Enable volatility-based adjustment
  
  volatility_thresholds:
    - range: [0, 0.20]
      grid_size: 1.0
    - range: [0.20, 0.40]
      grid_size: 1.5
    # ... more thresholds
```

### Risk Management
```yaml
risk:
  max_drawdown: -0.15        # Maximum portfolio drawdown (-15%)
  daily_loss_limit: -0.05    # Daily loss limit (-5%)
  max_position_ratio: 0.9    # Maximum position size (90%)
  min_position_ratio: 0.1    # Minimum position size (10%)
  risk_check_interval: 300   # Risk check frequency (seconds)
```

### S1 Strategy
```yaml
s1_strategy:
  enabled: true
  lookback_days: 52          # Historical period for high/low
  sell_target_percent: 0.50  # Target position on high breakout
  buy_target_percent: 0.70   # Target position on low breakout
```

## 📈 Strategy Overview

### Grid Trading Strategy
- Places buy orders below current price
- Places sell orders above current price
- Automatically adjusts grid size based on volatility
- Captures profits from price oscillations

### S1 Strategy
- Monitors 52-day high/low levels
- Reduces position on high breakouts
- Increases position on low breakouts
- Independent of main grid strategy

## 🛡️ Risk Management

### Position Limits
- Maximum position ratio (default: 90%)
- Minimum position ratio (default: 10%)
- Automatic position rebalancing

### Drawdown Protection
- Maximum drawdown limit (default: -15%)
- Daily loss limit (default: -5%)
- Emergency stop on critical levels

### Error Handling
- Automatic reconnection on network issues
- Order status verification
- State recovery on restart

## 📁 Project Structure

```
GridTrading Pro/
├── src/
│   ├── core/           # Trading engine and strategies
│   ├── exchanges/      # Exchange integrations
│   ├── notifications/  # Notification systems
│   ├── data/          # Data management
│   ├── utils/         # Utilities and helpers
│   └── config/        # Configuration management
├── tests/             # Test files
├── docs/              # Documentation
├── main.py            # Main entry point
├── config.yaml        # Configuration file
├── requirements.txt   # Dependencies
└── README.md          # This file
```

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Adding New Strategies
1. Create strategy class inheriting from `BaseStrategy`
2. Implement required methods
3. Register in `StrategyManager`

## 📊 Performance Monitoring

### Key Metrics
- Total profit/loss
- Win rate and profit factor
- Maximum drawdown
- Sharpe ratio
- Daily/weekly performance

### Data Export
```bash
# Export trading data
python -c "from src.data import DataManager; dm = DataManager(settings); await dm.export_data('backup/')"
```

## ⚠️ Important Notes

### Security
- Never share API keys
- Use testnet for development
- Enable IP restrictions on Binance
- Regular backup of trading data

### Risk Disclaimer
- Cryptocurrency trading involves significant risk
- Past performance doesn't guarantee future results
- Only trade with funds you can afford to lose
- Understand the strategy before using real money

### Support
- Check logs for error diagnosis
- Use testnet for troubleshooting
- Verify configuration before live trading

## 📝 Migration from v1.0

### Configuration Changes
- New YAML-based configuration
- Environment variable updates
- Strategy parameter adjustments

### Data Migration
```bash
# Import old data
python -c "from src.data import DataManager; dm = DataManager(settings); await dm.import_data('old_data/')"
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check documentation in `docs/` folder
- Review configuration examples
- Test with small amounts first
- Use testnet for development

---

**GridTrading Pro v2.0.0** - Advanced Grid Trading System
Built with ❤️ for the crypto trading community
