"""
Base exchange class for GridTrading Pro.

This module defines the abstract base class for all exchange implementations,
providing a unified interface for trading operations across different exchanges.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import asyncio
import time
from decimal import Decimal

from ..utils.logger import get_logger
from ..utils.validators import validate_order_response, validate_balance_response
from ..config.constants import OrderSide, OrderType


class BaseExchange(ABC):
    """Abstract base class for exchange implementations."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        timeout: int = 30000,
        **kwargs
    ):
        """Initialize base exchange."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.timeout = timeout
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # Exchange instance will be set by subclasses
        self.exchange = None
        self.symbol_info = {}
        self.is_connected = False
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize exchange connection and load market data."""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position information for symbol."""
        pass
    
    @abstractmethod
    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an existing order."""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status."""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information."""
        pass
    
    @abstractmethod
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[List]:
        """Get kline/candlestick data."""
        pass
    
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for symbol (futures only)."""
        pass
    
    async def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    async def _safe_request(self, method, *args, **kwargs):
        """Safely execute exchange request with error handling and rate limiting."""
        await self._rate_limit()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await method(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt == max_retries - 1:
                    raise e
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information."""
        return self.symbol_info.get(symbol, {})
    
    def adjust_amount_precision(self, symbol: str, amount: float) -> float:
        """Adjust amount to symbol precision."""
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            return amount
        
        precision = symbol_info.get('precision', {}).get('amount', 8)
        factor = 10 ** precision
        return int(amount * factor) / factor
    
    def adjust_price_precision(self, symbol: str, price: float) -> float:
        """Adjust price to symbol precision."""
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            return price
        
        precision = symbol_info.get('precision', {}).get('price', 8)
        factor = 10 ** precision
        return int(price * factor) / factor
    
    def validate_order_params(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float] = None
    ) -> bool:
        """Validate order parameters against symbol limits."""
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            return True  # Skip validation if no symbol info
        
        limits = symbol_info.get('limits', {})
        
        # Check amount limits
        amount_limits = limits.get('amount', {})
        min_amount = amount_limits.get('min', 0)
        max_amount = amount_limits.get('max', float('inf'))
        
        if not (min_amount <= amount <= max_amount):
            self.logger.error(f"Amount {amount} outside limits [{min_amount}, {max_amount}]")
            return False
        
        # Check price limits (if provided)
        if price is not None:
            price_limits = limits.get('price', {})
            min_price = price_limits.get('min', 0)
            max_price = price_limits.get('max', float('inf'))
            
            if not (min_price <= price <= max_price):
                self.logger.error(f"Price {price} outside limits [{min_price}, {max_price}]")
                return False
        
        return True
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price for symbol."""
        ticker = await self.get_ticker(symbol)
        return float(ticker.get('last', 0))
    
    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Create market order."""
        return await self.create_order(
            symbol=symbol,
            order_type=OrderType.MARKET.value,
            side=side,
            amount=amount,
            **kwargs
        )
    
    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Create limit order."""
        return await self.create_order(
            symbol=symbol,
            order_type=OrderType.LIMIT.value,
            side=side,
            amount=amount,
            price=price,
            **kwargs
        )
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Cancel all open orders."""
        open_orders = await self.get_open_orders(symbol)
        cancelled_orders = []
        
        for order in open_orders:
            try:
                cancelled = await self.cancel_order(order['id'], order['symbol'])
                cancelled_orders.append(cancelled)
            except Exception as e:
                self.logger.error(f"Failed to cancel order {order['id']}: {str(e)}")
        
        return cancelled_orders
    
    async def get_account_value(self) -> float:
        """Get total account value in USDT."""
        balance = await self.get_balance()
        total_value = 0.0
        
        for asset, amounts in balance.get('total', {}).items():
            if asset == 'USDT':
                total_value += float(amounts)
            else:
                # Convert to USDT value
                try:
                    symbol = f"{asset}/USDT"
                    price = await self.get_current_price(symbol)
                    total_value += float(amounts) * price
                except Exception:
                    # Skip if can't get price
                    continue
        
        return total_value
    
    def is_futures_mode(self) -> bool:
        """Check if exchange is in futures mode."""
        return False  # Override in futures implementation
    
    def is_spot_mode(self) -> bool:
        """Check if exchange is in spot mode."""
        return not self.is_futures_mode()
    
    async def close(self):
        """Close exchange connection."""
        if self.exchange and hasattr(self.exchange, 'close'):
            await self.exchange.close()
        self.is_connected = False
        self.logger.info("Exchange connection closed")
