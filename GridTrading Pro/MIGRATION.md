# Migration Guide: GridBNB-USDT to GridTrading Pro

This guide helps you migrate from the original GridBNB-USDT project to the new GridTrading Pro v2.0.0.

## 🔄 What's New in GridTrading Pro

### Major Improvements
- **Multi-Exchange Support**: Binance Spot + USDT-M Futures
- **Custom Trading Pairs**: Not limited to BNB/USDT
- **Leverage Configuration**: Configurable leverage for futures (1x-125x)
- **Telegram Notifications**: Replaced PushPlus with Telegram
- **Modular Architecture**: Clean, maintainable codebase
- **Enhanced Risk Management**: More sophisticated risk controls
- **Web Dashboard**: Improved monitoring interface
- **Testnet Support**: Safe testing environment

### Architecture Changes
- **YAML Configuration**: Replaced Python config with YAML
- **Pydantic Validation**: Type-safe configuration management
- **Async/Await**: Full async implementation
- **Strategy System**: Pluggable strategy architecture
- **Data Management**: Improved persistence and backup

## 📋 Migration Steps

### 1. Backup Current Data

Before migrating, backup your current trading data:

```bash
# In your old GridBNB-USDT directory
mkdir backup_$(date +%Y%m%d)
cp -r data/ backup_$(date +%Y%m%d)/
cp trading_system.log backup_$(date +%Y%m%d)/
cp .env backup_$(date +%Y%m%d)/
```

### 2. Install GridTrading Pro

```bash
# Clone new repository
git clone <gridtrading-pro-repo>
cd "GridTrading Pro"

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.\.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration Migration

#### Environment Variables (.env)
**Old format:**
```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
PUSHPLUS_TOKEN=your_token
INITIAL_PRINCIPAL=1000.0
INITIAL_BASE_PRICE=600.0
```

**New format:**
```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
INITIAL_PRINCIPAL=1000.0
INITIAL_BASE_PRICE=600.0
```

#### Trading Configuration
**Old (config.py):**
```python
SYMBOL = 'BNB/USDT'
INITIAL_GRID = 2.0
MAX_POSITION_RATIO = 0.9
MIN_POSITION_RATIO = 0.1
```

**New (config.yaml):**
```yaml
trading:
  mode: "spot"  # or "futures"
  symbol: "BNB/USDT"
  leverage: 1
  testnet: false

grid:
  initial_size: 2.0
  min_size: 1.0
  max_size: 4.0
  dynamic_adjustment: true

risk:
  max_position_ratio: 0.9
  min_position_ratio: 0.1
```

### 4. Notification Setup

#### Replace PushPlus with Telegram

1. **Create Telegram Bot:**
   - Message [@BotFather](https://t.me/botfather)
   - Create new bot: `/newbot`
   - Get bot token

2. **Get Chat ID:**
   - Start chat with your bot
   - Send message to bot
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find your chat ID in response

3. **Update Configuration:**
```yaml
notifications:
  telegram:
    enabled: true
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
    notification_levels:
      - "trade"
      - "risk"
      - "system"
      - "error"
```

### 5. Data Migration

#### Trade History Migration
If you have trade history in the old format, you can convert it:

```python
# migration_script.py
import json
from datetime import datetime

def migrate_trade_history():
    # Load old trade history
    with open('old_data/trade_history.json', 'r') as f:
        old_trades = json.load(f)
    
    # Convert to new format
    new_trades = []
    for trade in old_trades:
        new_trade = {
            'timestamp': trade.get('timestamp', 0),
            'side': trade.get('side', ''),
            'symbol': 'BNB/USDT',  # Add symbol
            'price': trade.get('price', 0),
            'amount': trade.get('amount', 0),
            'total': trade.get('price', 0) * trade.get('amount', 0),
            'profit': trade.get('profit', 0),
            'strategy': 'GRID',  # Add strategy
            'order_id': trade.get('order_id', '')
        }
        new_trades.append(new_trade)
    
    # Save in new format
    with open('GridTrading Pro/data/trade_history.json', 'w') as f:
        json.dump(new_trades, f, indent=2)

if __name__ == "__main__":
    migrate_trade_history()
```

#### State Migration
```python
# state_migration.py
import json

def migrate_state():
    # Load old state (if exists)
    try:
        with open('old_data/trading_state.json', 'r') as f:
            old_state = json.load(f)
    except FileNotFoundError:
        old_state = {}
    
    # Convert to new format
    new_state = {
        'base_price': old_state.get('base_price', 0),
        'grid_size': old_state.get('grid_size', 2.0),
        'total_profit': old_state.get('total_profit', 0),
        'trade_count': old_state.get('trade_count', 0),
        'last_adjustment_time': old_state.get('last_grid_adjust_time', 0),
        'volatility': 0,  # Will be recalculated
        'current_price': 0,  # Will be updated
        'last_save_time': 0
    }
    
    # Save in new format
    with open('GridTrading Pro/data/trading_state.json', 'w') as f:
        json.dump(new_state, f, indent=2)

if __name__ == "__main__":
    migrate_state()
```

### 6. Testing Migration

#### Test with Testnet
```yaml
# config.yaml
trading:
  testnet: true  # Enable testnet
  symbol: "BNB/USDT"
  mode: "spot"
```

```bash
# Run with testnet
python main.py --testnet
```

#### Verify Configuration
```bash
# Test configuration loading
python -c "from src.config.settings import Settings; s = Settings.load_from_file(); print('Config loaded successfully')"
```

## 🔧 Feature Mapping

### Old vs New Features

| Old Feature | New Feature | Notes |
|-------------|-------------|-------|
| PushPlus notifications | Telegram notifications | More reliable, feature-rich |
| Fixed BNB/USDT | Custom trading pairs | Any Binance pair supported |
| Spot only | Spot + Futures | Leverage support added |
| Python config | YAML config | More maintainable |
| Basic web UI | Enhanced dashboard | Better visualization |
| Manual testnet | Built-in testnet | Easier testing |

### Strategy Equivalents

| Old Strategy | New Strategy | Implementation |
|--------------|--------------|----------------|
| Main grid trading | GridStrategy | Core grid logic |
| S1 position control | S1Strategy | 52-day high/low strategy |
| Risk management | RiskManager | Enhanced multi-layer protection |

## ⚠️ Important Notes

### Breaking Changes
1. **Configuration format changed** - Must migrate to YAML
2. **Notification system changed** - Must setup Telegram
3. **File structure changed** - Data files in new format
4. **API changes** - Internal APIs restructured

### Compatibility
- **Python version**: 3.8+ (same requirement)
- **Binance API**: Same API, enhanced usage
- **Trading logic**: Core logic preserved, enhanced

### Risk Considerations
1. **Test thoroughly** with testnet before live trading
2. **Start with small amounts** to verify behavior
3. **Monitor closely** during initial migration period
4. **Keep backups** of old system until confident

## 🚀 Post-Migration

### Verification Checklist
- [ ] Configuration loads without errors
- [ ] Telegram notifications working
- [ ] Testnet trading successful
- [ ] Web dashboard accessible
- [ ] Trade history migrated
- [ ] Risk limits configured correctly

### Optimization
1. **Adjust grid parameters** based on new volatility system
2. **Configure S1 strategy** if desired
3. **Set up monitoring** alerts
4. **Review risk parameters** for your trading style

### Monitoring
- Check logs regularly: `tail -f logs/gridtrading.log`
- Monitor web dashboard: `http://localhost:58181`
- Verify Telegram notifications
- Review trade performance

## 🆘 Troubleshooting

### Common Issues

#### Configuration Errors
```bash
# Validate configuration
python -c "from src.config.settings import Settings; Settings.load_from_file()"
```

#### Telegram Not Working
1. Verify bot token and chat ID
2. Check bot permissions
3. Test with simple message

#### Data Migration Issues
1. Check file permissions
2. Verify JSON format
3. Use migration scripts provided

#### Trading Issues
1. Start with testnet
2. Check API permissions
3. Verify balance and limits

### Getting Help
1. Check logs for detailed error messages
2. Verify configuration against examples
3. Test individual components
4. Use testnet for debugging

## 📈 Next Steps

After successful migration:

1. **Explore new features**:
   - Try futures trading (with caution)
   - Test different trading pairs
   - Experiment with leverage settings

2. **Optimize performance**:
   - Adjust grid parameters
   - Fine-tune risk settings
   - Monitor and analyze results

3. **Stay updated**:
   - Watch for updates
   - Join community discussions
   - Share feedback and suggestions

---

**Migration Support**: If you encounter issues during migration, please check the documentation and logs first. The new system is designed to be more robust and feature-rich while maintaining the core trading logic you're familiar with.
