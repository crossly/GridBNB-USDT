"""
GridTrading Pro - Advanced Grid Trading System

A modular, high-performance grid trading system supporting:
- Binance Spot and USDT-M Futures trading
- Dynamic grid adjustment based on market volatility
- Advanced risk management with multi-layer protection
- S1 strategy for position optimization
- Telegram notifications
- Real-time web monitoring interface
- Testnet support for safe testing

Author: GridTrading Pro Team
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "GridTrading Pro Team"
__email__ = "support@gridtrading.pro"

# Core imports for easy access
from .config.settings import Settings
from .core.grid_engine import GridEngine
from .exchanges.base_exchange import BaseExchange

__all__ = [
    "Settings",
    "GridEngine", 
    "BaseExchange",
    "__version__",
    "__author__",
]
