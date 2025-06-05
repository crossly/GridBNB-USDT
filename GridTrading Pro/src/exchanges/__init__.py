"""
Exchange integration module for GridTrading Pro.

This module provides unified interfaces for different exchanges and trading modes,
currently supporting Binance Spot and USDT-M Futures trading.
"""

from .base_exchange import BaseExchange
from .binance_spot import BinanceSpotExchange
from .binance_futures import BinanceFuturesExchange

__all__ = [
    "BaseExchange",
    "BinanceSpotExchange", 
    "BinanceFuturesExchange",
]


def create_exchange(trading_mode: str, **kwargs) -> BaseExchange:
    """Factory function to create exchange instance based on trading mode."""
    if trading_mode.lower() == "spot":
        return BinanceSpotExchange(**kwargs)
    elif trading_mode.lower() == "futures":
        return BinanceFuturesExchange(**kwargs)
    else:
        raise ValueError(f"Unsupported trading mode: {trading_mode}")
