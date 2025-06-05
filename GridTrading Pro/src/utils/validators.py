"""
Validation utilities for GridTrading Pro.

This module contains various validation functions for trading parameters,
API responses, and data integrity checks.
"""

import re
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal


def validate_api_credentials(api_key: str, api_secret: str) -> bool:
    """Validate API credentials format."""
    if not api_key or not api_secret:
        return False
    
    # Basic format validation
    if len(api_key) < 10 or len(api_secret) < 10:
        return False
    
    # Check for valid characters (alphanumeric)
    if not re.match(r'^[a-zA-Z0-9]+$', api_key):
        return False
    
    if not re.match(r'^[a-zA-Z0-9]+$', api_secret):
        return False
    
    return True


def validate_trading_symbol(symbol: str, supported_symbols: List[str]) -> bool:
    """Validate trading symbol."""
    if not symbol:
        return False
    
    # Check format (BASE/QUOTE)
    if '/' not in symbol:
        return False
    
    parts = symbol.split('/')
    if len(parts) != 2:
        return False
    
    base, quote = parts
    if not base or not quote:
        return False
    
    # Check if symbol is supported
    return symbol in supported_symbols


def validate_price(price: Union[float, str]) -> bool:
    """Validate price value."""
    try:
        price_val = float(price)
        return price_val > 0
    except (ValueError, TypeError):
        return False


def validate_amount(amount: Union[float, str], min_amount: float = 0.0) -> bool:
    """Validate amount value."""
    try:
        amount_val = float(amount)
        return amount_val >= min_amount
    except (ValueError, TypeError):
        return False


def validate_percentage(percentage: Union[float, str], min_val: float = 0.0, max_val: float = 100.0) -> bool:
    """Validate percentage value."""
    try:
        pct_val = float(percentage)
        return min_val <= pct_val <= max_val
    except (ValueError, TypeError):
        return False


def validate_leverage(leverage: Union[int, str], min_leverage: int = 1, max_leverage: int = 125) -> bool:
    """Validate leverage value."""
    try:
        lev_val = int(leverage)
        return min_leverage <= lev_val <= max_leverage
    except (ValueError, TypeError):
        return False


def validate_grid_size(grid_size: Union[float, str], min_size: float = 0.1, max_size: float = 10.0) -> bool:
    """Validate grid size value."""
    try:
        size_val = float(grid_size)
        return min_size <= size_val <= max_size
    except (ValueError, TypeError):
        return False


def validate_order_response(order: Dict[str, Any]) -> bool:
    """Validate exchange order response."""
    required_fields = ['id', 'symbol', 'side', 'amount', 'price', 'status']
    
    if not isinstance(order, dict):
        return False
    
    for field in required_fields:
        if field not in order:
            return False
    
    # Validate specific fields
    if not validate_price(order.get('price', 0)):
        return False
    
    if not validate_amount(order.get('amount', 0)):
        return False
    
    if order.get('side') not in ['buy', 'sell']:
        return False
    
    return True


def validate_balance_response(balance: Dict[str, Any]) -> bool:
    """Validate exchange balance response."""
    if not isinstance(balance, dict):
        return False
    
    # Check for required structure
    required_keys = ['free', 'used', 'total']
    for key in required_keys:
        if key not in balance:
            return False
        
        if not isinstance(balance[key], dict):
            return False
    
    return True


def validate_kline_data(klines: List[List]) -> bool:
    """Validate kline/candlestick data."""
    if not isinstance(klines, list) or len(klines) == 0:
        return False
    
    for kline in klines:
        if not isinstance(kline, list) or len(kline) < 6:
            return False
        
        # Validate OHLCV data
        try:
            timestamp = float(kline[0])
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            
            # Basic sanity checks
            if not all(p > 0 for p in [open_price, high_price, low_price, close_price]):
                return False
            
            if high_price < max(open_price, close_price):
                return False
            
            if low_price > min(open_price, close_price):
                return False
            
            if volume < 0:
                return False
                
        except (ValueError, TypeError, IndexError):
            return False
    
    return True


def validate_telegram_config(bot_token: str, chat_id: str) -> bool:
    """Validate Telegram configuration."""
    if not bot_token or not chat_id:
        return False
    
    # Validate bot token format (should be like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
    bot_token_pattern = r'^\d+:[a-zA-Z0-9_-]+$'
    if not re.match(bot_token_pattern, bot_token):
        return False
    
    # Validate chat ID (can be negative for groups)
    try:
        int(chat_id)
        return True
    except ValueError:
        return False


def validate_risk_parameters(
    max_drawdown: float,
    daily_loss_limit: float,
    max_position_ratio: float,
    min_position_ratio: float
) -> bool:
    """Validate risk management parameters."""
    # Drawdown and loss limits should be negative
    if max_drawdown >= 0 or daily_loss_limit >= 0:
        return False
    
    # Position ratios should be between 0 and 1
    if not (0 <= min_position_ratio <= 1):
        return False
    
    if not (0 <= max_position_ratio <= 1):
        return False
    
    # Min should be less than max
    if min_position_ratio >= max_position_ratio:
        return False
    
    return True


def validate_grid_parameters(
    initial_size: float,
    min_size: float,
    max_size: float
) -> bool:
    """Validate grid trading parameters."""
    # All sizes should be positive
    if not all(size > 0 for size in [initial_size, min_size, max_size]):
        return False
    
    # Min should be less than max
    if min_size >= max_size:
        return False
    
    # Initial should be between min and max
    if not (min_size <= initial_size <= max_size):
        return False
    
    return True


def validate_s1_parameters(
    lookback_days: int,
    sell_target_percent: float,
    buy_target_percent: float
) -> bool:
    """Validate S1 strategy parameters."""
    # Lookback days should be positive
    if lookback_days <= 0:
        return False
    
    # Target percentages should be between 0 and 1
    if not (0 <= sell_target_percent <= 1):
        return False
    
    if not (0 <= buy_target_percent <= 1):
        return False
    
    return True


def sanitize_float(value: Union[float, str, int], default: float = 0.0) -> float:
    """Sanitize and convert value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def sanitize_int(value: Union[int, str, float], default: int = 0) -> int:
    """Sanitize and convert value to int."""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def sanitize_string(value: Any, default: str = "") -> str:
    """Sanitize and convert value to string."""
    try:
        return str(value).strip()
    except (ValueError, TypeError):
        return default


def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Validate JSON data structure."""
    if not isinstance(data, dict):
        return False
    
    for field in required_fields:
        if field not in data:
            return False
    
    return True


def validate_timestamp(timestamp: Union[int, float, str]) -> bool:
    """Validate timestamp value."""
    try:
        ts = float(timestamp)
        # Check if timestamp is reasonable (between 2020 and 2030)
        return 1577836800 <= ts <= 1893456000  # 2020-01-01 to 2030-01-01
    except (ValueError, TypeError):
        return False


def validate_order_side(side: str) -> bool:
    """Validate order side."""
    return side.lower() in ['buy', 'sell']


def validate_order_type(order_type: str) -> bool:
    """Validate order type."""
    return order_type.lower() in ['market', 'limit']


def validate_trading_mode(mode: str) -> bool:
    """Validate trading mode."""
    return mode.lower() in ['spot', 'futures']
