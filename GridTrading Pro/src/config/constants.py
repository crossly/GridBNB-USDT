"""
Constants and enums for GridTrading Pro.
"""

from enum import Enum


class TradingMode(Enum):
    """Trading mode enumeration."""
    SPOT = "spot"
    FUTURES = "futures"


class NotificationLevel(Enum):
    """Notification level enumeration."""
    TRADE = "trade"
    RISK = "risk"
    SYSTEM = "system"
    ERROR = "error"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"


class StrategyType(Enum):
    """Strategy type enumeration."""
    GRID = "grid"
    S1 = "s1"


# Default configuration values
DEFAULT_CONFIG = {
    "trading": {
        "mode": TradingMode.SPOT.value,
        "symbol": "BNB/USDT",
        "leverage": 1,
        "testnet": False,
        "min_trade_amount": 20.0,
        "order_timeout": 30,
        "min_trade_interval": 30,
    },
    "grid": {
        "initial_size": 2.0,
        "min_size": 1.0,
        "max_size": 4.0,
        "dynamic_adjustment": True,
    },
    "risk": {
        "max_drawdown": -0.15,
        "daily_loss_limit": -0.05,
        "max_position_ratio": 0.9,
        "min_position_ratio": 0.1,
        "risk_check_interval": 300,
    },
    "web": {
        "enabled": True,
        "host": "0.0.0.0",
        "port": 58181,
        "auto_refresh_interval": 2000,
    },
    "logging": {
        "level": "INFO",
        "file_rotation": "midnight",
        "backup_count": 7,
    },
    "api": {
        "timeout": 30000,
        "recv_window": 5000,
        "rate_limit": True,
        "max_retries": 3,
    },
}

# API endpoints
BINANCE_ENDPOINTS = {
    "spot": {
        "production": "https://api.binance.com",
        "testnet": "https://testnet.binance.vision",
    },
    "futures": {
        "production": "https://fapi.binance.com",
        "testnet": "https://testnet.binancefuture.com",
    },
}

# Supported trading pairs (can be extended)
SUPPORTED_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "DOT/USDT",
    "LINK/USDT", "LTC/USDT", "BCH/USDT", "XRP/USDT", "EOS/USDT",
    "TRX/USDT", "ETC/USDT", "XLM/USDT", "ATOM/USDT", "NEO/USDT",
]

# Risk management constants
MAX_LEVERAGE = 125
MIN_LEVERAGE = 1
MAX_POSITION_RATIO = 1.0
MIN_POSITION_RATIO = 0.0

# Grid trading constants
MIN_GRID_SIZE = 0.1
MAX_GRID_SIZE = 10.0
DEFAULT_VOLATILITY_WINDOW = 24

# Notification constants
MAX_MESSAGE_LENGTH = 4096  # Telegram message limit
NOTIFICATION_RETRY_ATTEMPTS = 3
NOTIFICATION_RETRY_DELAY = 5  # seconds

# Data persistence constants
MAX_TRADE_HISTORY = 10000
BACKUP_INTERVAL = 3600  # 1 hour
STATE_SAVE_INTERVAL = 60  # 1 minute
