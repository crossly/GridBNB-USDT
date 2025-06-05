# 环境变量同步指南

## 🔍 问题说明

当您修改了 `.env.testnet` 文件后，程序没有使用最新参数的原因：

1. **程序读取的是 `.env` 文件**，不是 `.env.testnet`
2. **`start_testnet.sh` 脚本只在启动时复制一次** `.env.testnet` 到 `.env`
3. **如果您直接修改 `.env.testnet`**，需要手动同步到 `.env`

## 🛠️ 解决方案

### 方法1: 使用同步脚本（推荐）

```bash
# 检查同步状态
python3 check_env_sync.py

# 同步文件
python3 sync_env.py

# 或者更新特定参数并同步
python3 sync_env.py INITIAL_BASE_PRICE 105000.0
```

### 方法2: 手动复制

```bash
# 将 .env.testnet 复制到 .env
cp .env.testnet .env

# 验证复制成功
diff .env .env.testnet
```

### 方法3: 重新运行启动脚本

```bash
# 启动脚本会自动同步
./start_testnet.sh
```

### 方法4: 自动监控（开发时使用）

```bash
# 在一个终端运行自动同步监控
python3 auto_sync_env.py

# 在另一个终端修改 .env.testnet
# 修改会自动同步到 .env
```

## 📋 工作流程

### 正确的修改流程：

1. **修改参数**：
```bash
# 编辑 .env.testnet 文件
nano .env.testnet
```

2. **同步文件**：
```bash
python3 sync_env.py
```

3. **验证同步**：
```bash
python3 check_env_sync.py
```

4. **重启程序**：
```bash
python3 main.py --config config.testnet.yaml --testnet
```

### 快速修改特定参数：

```bash
# 一步完成：修改并同步
python3 sync_env.py INITIAL_BASE_PRICE 105000.0

# 重启程序
python3 main.py --config config.testnet.yaml --testnet
```

## 🔧 实用脚本

### 检查同步状态
```bash
python3 check_env_sync.py
```
显示两个文件的关键参数对比和时间戳。

### 同步文件
```bash
# 基本同步
python3 sync_env.py

# 修改参数并同步
python3 sync_env.py KEY VALUE
```

### 自动监控
```bash
python3 auto_sync_env.py
```
实时监控 `.env.testnet` 的修改并自动同步。

## ⚠️ 重要提醒

1. **修改 `.env.testnet` 后必须同步到 `.env`**
2. **程序重启后才会读取新的环境变量**
3. **敏感信息（API密钥）建议只在环境变量中设置**
4. **非敏感配置可以在YAML文件中设置**

## 🎯 最佳实践

### 开发时：
```bash
# 启动自动同步监控
python3 auto_sync_env.py &

# 修改配置文件
nano .env.testnet

# 重启程序（自动同步已完成）
python3 main.py --config config.testnet.yaml --testnet
```

### 生产时：
```bash
# 修改配置
nano .env.testnet

# 手动同步
python3 sync_env.py

# 验证
python3 check_env_sync.py

# 重启
./start_testnet.sh
```

## 🔍 故障排除

### 问题：参数没有生效
```bash
# 1. 检查同步状态
python3 check_env_sync.py

# 2. 如果不同步，执行同步
python3 sync_env.py

# 3. 重启程序
```

### 问题：不确定哪个文件被使用
```bash
# 检查程序实际读取的值
grep INITIAL_BASE_PRICE .env

# 检查源文件
grep INITIAL_BASE_PRICE .env.testnet
```

### 问题：修改后立即生效
```bash
# 使用自动监控模式
python3 auto_sync_env.py
```

## 📊 配置优先级

1. **环境变量** (`.env` 文件) - 最高优先级
2. **YAML配置** (`config.testnet.yaml`)
3. **默认值**

因此，确保 `.env` 文件是最新的非常重要！
