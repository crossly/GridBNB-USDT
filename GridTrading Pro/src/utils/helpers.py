"""
Helper functions and utilities for GridTrading Pro.

This module contains various utility functions for mathematical calculations,
data formatting, time handling, and other common operations.
"""

import time
import math
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal, ROUND_DOWN
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential


def format_timestamp(timestamp: Optional[float] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp to readable string."""
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).strftime(format_str)


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def calculate_volatility(prices: List[float], window: int = 24) -> float:
    """Calculate price volatility using standard deviation."""
    if len(prices) < 2:
        return 0.0
    
    # Use only the last 'window' prices
    recent_prices = prices[-window:] if len(prices) > window else prices
    
    if len(recent_prices) < 2:
        return 0.0
    
    # Calculate returns
    returns = []
    for i in range(1, len(recent_prices)):
        ret = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
        returns.append(ret)
    
    if not returns:
        return 0.0
    
    # Calculate standard deviation and annualize
    std_dev = np.std(returns)
    # Annualize assuming hourly data (24 hours * 365 days)
    volatility = std_dev * math.sqrt(24 * 365)
    
    return volatility


def adjust_precision(amount: float, precision: int = 8) -> float:
    """Adjust amount to specified decimal precision."""
    if precision <= 0:
        return float(int(amount))
    
    factor = 10 ** precision
    return math.floor(amount * factor) / factor


def calculate_grid_levels(
    base_price: float,
    grid_size: float,
    num_levels: int = 10
) -> Dict[str, List[float]]:
    """Calculate grid buy and sell levels."""
    grid_decimal = grid_size / 100
    
    buy_levels = []
    sell_levels = []
    
    for i in range(1, num_levels + 1):
        buy_price = base_price * (1 - grid_decimal * i)
        sell_price = base_price * (1 + grid_decimal * i)
        
        buy_levels.append(buy_price)
        sell_levels.append(sell_price)
    
    return {
        "buy_levels": buy_levels,
        "sell_levels": sell_levels
    }


def calculate_position_size(
    total_balance: float,
    price: float,
    position_ratio: float,
    min_amount: float = 0.0
) -> float:
    """Calculate position size based on balance and ratio."""
    target_value = total_balance * position_ratio
    position_size = target_value / price
    
    return max(position_size, min_amount)


def calculate_profit_loss(
    entry_price: float,
    current_price: float,
    amount: float,
    side: str
) -> float:
    """Calculate profit/loss for a position."""
    if side.lower() == "buy":
        return (current_price - entry_price) * amount
    elif side.lower() == "sell":
        return (entry_price - current_price) * amount
    else:
        return 0.0


def format_currency(amount: float, currency: str = "USDT", decimals: int = 2) -> str:
    """Format currency amount with proper decimals."""
    return f"{amount:.{decimals}f} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage value."""
    return f"{value:.{decimals}f}%"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp value between min and max."""
    return max(min_value, min(value, max_value))


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay."""
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def safe_async_call(func, *args, **kwargs):
    """Safely call async function with retry logic."""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        raise e


def calculate_moving_average(prices: List[float], period: int) -> Optional[float]:
    """Calculate simple moving average."""
    if len(prices) < period:
        return None
    
    recent_prices = prices[-period:]
    return sum(recent_prices) / len(recent_prices)


def calculate_ema(prices: List[float], period: int, alpha: Optional[float] = None) -> Optional[float]:
    """Calculate exponential moving average."""
    if len(prices) < period:
        return None
    
    if alpha is None:
        alpha = 2 / (period + 1)
    
    ema = prices[0]
    for price in prices[1:]:
        ema = alpha * price + (1 - alpha) * ema
    
    return ema


def is_market_hours() -> bool:
    """Check if it's market hours (crypto markets are 24/7, so always True)."""
    return True


def get_next_grid_adjustment_time(
    last_adjustment: float,
    volatility: float,
    base_interval: int = 3600
) -> float:
    """Calculate next grid adjustment time based on volatility."""
    # Higher volatility = more frequent adjustments
    if volatility > 0.8:
        interval = base_interval * 0.25  # 15 minutes
    elif volatility > 0.4:
        interval = base_interval * 0.5   # 30 minutes
    elif volatility > 0.2:
        interval = base_interval * 0.75  # 45 minutes
    else:
        interval = base_interval         # 1 hour
    
    return last_adjustment + interval


def validate_trading_pair(symbol: str) -> bool:
    """Validate trading pair format."""
    if not symbol or "/" not in symbol:
        return False
    
    parts = symbol.split("/")
    if len(parts) != 2:
        return False
    
    base, quote = parts
    return len(base) > 0 and len(quote) > 0


def calculate_leverage_margin(
    position_size: float,
    price: float,
    leverage: int
) -> float:
    """Calculate required margin for leveraged position."""
    notional_value = position_size * price
    return notional_value / leverage


def format_trade_message(
    side: str,
    symbol: str,
    price: float,
    amount: float,
    total: float,
    strategy: str = "GRID",
    profit: float = 0.0
) -> str:
    """Format trade execution message."""
    emoji = "🟢" if side.upper() == "BUY" else "🔴"
    profit_text = f" | Profit: {profit:+.2f} USDT" if profit != 0 else ""
    
    return (
        f"{emoji} {strategy} {side.upper()} {symbol}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price: {price:.4f} USDT\n"
        f"📊 Amount: {amount:.6f}\n"
        f"💵 Total: {total:.2f} USDT{profit_text}\n"
        f"⏰ Time: {format_timestamp()}"
    )


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def wait_with_timeout(coro, timeout: float):
    """Wait for coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout} seconds")


def get_system_uptime(start_time: float) -> str:
    """Get system uptime in human readable format."""
    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
