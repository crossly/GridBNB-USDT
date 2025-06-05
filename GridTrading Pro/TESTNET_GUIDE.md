# GridTrading Pro Testnet Guide

## 🧪 Testnet Configuration Overview

This guide covers the pre-configured testnet environment for GridTrading Pro, specifically set up for **BTC/USDT Futures trading with 50x leverage**.

## ⚠️ **IMPORTANT WARNINGS**

### **High Risk Configuration**
- **50x Leverage**: Extremely high leverage amplifies both profits and losses
- **Futures Trading**: More complex than spot trading with liquidation risks
- **BTC Volatility**: Bitcoin can be highly volatile, especially with leverage
- **Testnet Only**: This configuration is for testing purposes only

### **Risk Factors**
- **Liquidation Risk**: High leverage means positions can be liquidated quickly
- **Rapid Losses**: 50x leverage means 2% adverse price movement = 100% loss
- **Market Volatility**: BTC can move 5-10% in minutes during volatile periods
- **System Risk**: Software bugs or network issues can cause losses

## 📋 Testnet Configuration Details

### **Trading Parameters**
```yaml
Trading Mode: USDT-M Futures
Symbol: BTC/USDT
Leverage: 50x
Initial Grid Size: 0.5%
Min Grid Size: 0.2%
Max Grid Size: 2.0%
```

### **Risk Management**
```yaml
Max Drawdown: -10%
Daily Loss Limit: -5%
Max Position Ratio: 80%
Min Position Ratio: 10%
Risk Check Interval: 60 seconds
```

### **Grid Strategy**
- **Dynamic Adjustment**: Grid size adjusts based on BTC volatility
- **Smaller Grids**: 0.2%-2.0% range suitable for BTC price movements
- **Faster Execution**: Reduced intervals for testing responsiveness

## 🚀 Quick Start

### **1. Start Testnet Environment**

**Linux/macOS:**
```bash
./start_testnet.sh
```

**Windows:**
```cmd
start_testnet.bat
```

### **2. Manual Start (Alternative)**
```bash
# Copy testnet environment
cp .env.testnet .env

# Start with testnet config
python main.py --config config.testnet.yaml --testnet
```

## 🔧 Configuration Files

### **Environment Variables (.env.testnet)**
```env
# Pre-configured with your testnet API credentials
BINANCE_API_KEY=1ba07130ec33e1b61d6f86d627d7bc23f8e705fd393963b9804d53277b23cce2
BINANCE_API_SECRET=0b3212503f3656d2fadcefe9655752cb2a326cb141419356625f9016d452ae1f

# You need to add your Telegram credentials
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Testnet settings
INITIAL_PRINCIPAL=10000.0
INITIAL_BASE_PRICE=50000.0
ENVIRONMENT=testing
```

### **Trading Configuration (config.testnet.yaml)**
```yaml
trading:
  mode: "futures"
  symbol: "BTC/USDT"
  leverage: 50
  testnet: true
  min_trade_amount: 10.0

grid:
  initial_size: 0.5
  min_size: 0.2
  max_size: 2.0
  dynamic_adjustment: true

risk:
  max_drawdown: -0.10
  daily_loss_limit: -0.05
  max_position_ratio: 0.8
```

## 📊 Monitoring & Analysis

### **Web Dashboard**
- **URL**: http://localhost:58181
- **Features**: Real-time monitoring, trade history, performance metrics
- **Refresh Rate**: 1 second (faster for testing)

### **Key Metrics to Watch**
1. **Position Size**: Monitor leverage usage
2. **Unrealized PnL**: Track open position performance
3. **Drawdown**: Watch for approaching limits
4. **Grid Efficiency**: Observe buy/sell execution
5. **Risk Alerts**: Pay attention to risk notifications

### **Telegram Notifications**
- **Trade Execution**: Every buy/sell order
- **Risk Alerts**: Drawdown and position warnings
- **System Status**: Startup, shutdown, errors
- **Grid Adjustments**: Dynamic size changes

## 🎯 Testing Scenarios

### **1. Basic Grid Testing**
- Start with default settings
- Observe grid placement and execution
- Monitor position building
- Check risk management triggers

### **2. Volatility Testing**
- Wait for BTC price movements
- Observe grid size adjustments
- Test during high/low volatility periods
- Verify risk limits activation

### **3. Risk Management Testing**
- Monitor drawdown calculations
- Test emergency stop triggers
- Verify position limit enforcement
- Check daily loss limit functionality

### **4. Performance Analysis**
- Track profit/loss over time
- Analyze trade frequency
- Monitor grid efficiency
- Review risk-adjusted returns

## 🛡️ Safety Measures

### **Built-in Protections**
1. **Testnet Environment**: No real money at risk
2. **Position Limits**: Maximum 80% portfolio exposure
3. **Drawdown Protection**: Auto-stop at -10% loss
4. **Daily Limits**: Maximum -5% daily loss
5. **Emergency Stop**: Critical condition protection

### **Manual Safety Checks**
1. **Regular Monitoring**: Check system every few hours
2. **Log Review**: Examine logs for errors or warnings
3. **Performance Analysis**: Track key metrics
4. **Risk Assessment**: Evaluate if settings are appropriate

## 📈 Expected Behavior

### **Normal Operation**
- Grid orders placed above/below current price
- Automatic position adjustments
- Regular profit taking from grid trades
- Dynamic grid size based on volatility

### **High Volatility Periods**
- Larger grid sizes (up to 2%)
- More frequent trades
- Higher profit potential
- Increased risk exposure

### **Risk Events**
- Position size warnings
- Drawdown alerts
- Emergency stop activation
- Automatic order cancellation

## 🔍 Troubleshooting

### **Common Issues**

**1. Connection Problems**
```bash
# Check testnet connectivity
curl -X GET "https://testnet.binancefuture.com/fapi/v1/ping"
```

**2. API Errors**
- Verify API keys are correct
- Check testnet permissions
- Ensure futures trading enabled

**3. Insufficient Balance**
- Get testnet USDT from Binance testnet faucet
- Check account balance in web interface

**4. Leverage Issues**
- Verify 50x leverage is available for BTC/USDT
- Check margin requirements

### **Debug Mode**
```bash
# Start with debug logging
LOG_LEVEL=DEBUG python main.py --config config.testnet.yaml --testnet
```

## 📝 Testing Checklist

### **Pre-Start Checklist**
- [ ] Testnet API keys configured
- [ ] Telegram bot setup (optional but recommended)
- [ ] Sufficient testnet USDT balance
- [ ] Understanding of 50x leverage risks
- [ ] Web dashboard accessible

### **During Testing**
- [ ] Monitor position sizes
- [ ] Watch for risk alerts
- [ ] Check grid execution
- [ ] Verify profit/loss calculations
- [ ] Test emergency stop if needed

### **Post-Testing Analysis**
- [ ] Review trade history
- [ ] Analyze performance metrics
- [ ] Check risk management effectiveness
- [ ] Document lessons learned
- [ ] Adjust settings if needed

## 🎓 Learning Objectives

### **Understanding Grid Trading**
- How grid orders are placed and executed
- Impact of grid size on trading frequency
- Relationship between volatility and grid performance

### **Futures Trading Concepts**
- Leverage mechanics and margin requirements
- Position sizing and risk management
- Liquidation risks and prevention

### **Risk Management**
- Importance of position limits
- Drawdown monitoring and control
- Emergency procedures and stops

## 🚨 Before Live Trading

### **Requirements for Live Trading**
1. **Successful Testnet Operation**: At least 1 week of stable testing
2. **Understanding of Risks**: Full comprehension of leverage and liquidation
3. **Risk Tolerance**: Comfortable with potential losses
4. **Capital Management**: Only risk what you can afford to lose
5. **Monitoring Setup**: Reliable monitoring and alert systems

### **Recommended Adjustments for Live Trading**
- **Reduce Leverage**: Start with 2-5x instead of 50x
- **Smaller Position Sizes**: Use 20-50% of available capital
- **Tighter Risk Limits**: Lower drawdown and daily loss limits
- **Conservative Grid Sizes**: Start with smaller, more conservative grids

## 📞 Support

### **Getting Help**
1. **Check Logs**: Review `logs/gridtrading.log` for errors
2. **Web Dashboard**: Monitor system status at http://localhost:58181
3. **Configuration**: Verify settings in `config.testnet.yaml`
4. **Documentation**: Review README.md and other guides

### **Emergency Procedures**
1. **Stop Trading**: Ctrl+C to stop the application
2. **Cancel Orders**: Use exchange interface to cancel open orders
3. **Close Positions**: Manually close positions if needed
4. **Review Logs**: Check what went wrong

---

**Remember**: This is a high-risk configuration designed for testing. Always understand the risks before proceeding to live trading with real funds.
