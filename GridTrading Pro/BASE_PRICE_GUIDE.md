# Base Price 设置指南

Base Price（基础价格）是网格交易的核心参考点，所有网格级别都基于这个价格计算。

## 🎯 什么是Base Price？

Base Price是网格交易的中心价格，系统会在这个价格上下创建买卖网格：
- **买入网格**: Base Price以下的价格级别
- **卖出网格**: Base Price以上的价格级别

## 📍 修改Base Price的方法

### ⚠️ 重要：配置优先级说明

配置加载优先级（从高到低）：
1. **环境变量** (`.env` 文件) - 最高优先级
2. **YAML配置文件** (`config.testnet.yaml`)
3. **默认值**

**关键问题**：`start_testnet.sh` 脚本会将 `.env.testnet` 复制到 `.env`，所以需要同时更新两个文件！

### 方法1: 使用同步脚本 (推荐)

```bash
# 设置base price并同步所有文件
python3 sync_env.py INITIAL_BASE_PRICE 104000.0

# 只同步文件（如果手动修改了.env.testnet）
python3 sync_env.py
```

### 方法2: 手动修改环境变量

**必须同时修改两个文件**：
1. 修改 `.env.testnet`：
```bash
INITIAL_BASE_PRICE=104000.0
```

2. 修改 `.env`：
```bash
INITIAL_BASE_PRICE=104000.0
```

### 方法3: 配置文件 (需要清空环境变量)

在 `config.testnet.yaml` 中设置：
```yaml
# Initial Settings
initial_base_price: 104000.0
```

**但是**，还需要在环境变量文件中设置为0或删除该行：
```bash
INITIAL_BASE_PRICE=0  # 或者删除这一行
```

## 🔧 脚本使用示例

```bash
# 基本用法 - 设置base price为104000
python3 set_base_price.py 104000.0

# 使用当前市场价格作为base price
python3 set_base_price.py --current

# 更新所有配置文件和交易状态
python3 set_base_price.py 105000.0 --state

# 指定特定的配置文件
python3 set_base_price.py 104000.0 --config config.yaml --env .env
```

## 📊 Base Price 策略建议

### 1. 当前价格策略
```bash
python3 set_base_price.py --current
```
- 适合：刚开始交易或市场稳定时
- 优点：立即开始交易
- 缺点：可能错过更好的入场点

### 2. 支撑位策略
```bash
python3 set_base_price.py 103000.0  # 假设103000是支撑位
```
- 适合：技术分析确定的支撑位
- 优点：在好价位建仓
- 缺点：可能需要等待价格回调

### 3. 平均价格策略
```bash
# 设置为24小时平均价格
python3 set_base_price.py 104500.0
```
- 适合：长期持有策略
- 优点：避免极端价格影响
- 缺点：需要手动计算平均价格

## ⚠️ 重要注意事项

1. **重启生效**: 修改base price后需要重启GridTrading Pro
2. **现有订单**: 修改base price不会影响已存在的订单
3. **风险管理**: 确保base price符合您的风险承受能力
4. **市场分析**: 建议结合技术分析设置合理的base price

## 🔍 查看当前设置

```bash
# 查看当前配置
cat config.testnet.yaml | grep initial_base_price

# 查看环境变量
cat .env.testnet | grep INITIAL_BASE_PRICE

# 查看交易状态
cat data/trading_state.json | grep base_price
```

## 📈 网格级别预览

设置base price后，您可以运行测试脚本查看网格级别：
```bash
python3 test_grid_debug.py
```

这将显示详细的网格价格级别，帮助您验证设置是否合理。

## 🚀 快速开始

1. 查看当前BTC价格并设置base price：
```bash
python3 set_base_price.py --current
```

2. 重启系统：
```bash
python3 main.py --config config.testnet.yaml --testnet
```

3. 查看网格级别（在DEBUG模式下会自动显示）

## 💡 高级技巧

- 使用稍低于当前价格的base price可以优先建立买入仓位
- 使用稍高于当前价格的base price可以优先建立卖出仓位
- 定期根据市场趋势调整base price以优化收益
