"""
Binance USDT-M Futures exchange implementation for GridTrading Pro.

This module provides Binance USDT-M Futures trading functionality with support for
leverage configuration, position management, and testnet environment.
"""

import ccxt.async_support as ccxt
import os
from typing import Dict, List, Optional, Any
import asyncio

from .base_exchange import BaseExchange
from ..utils.logger import get_logger
from ..utils.validators import validate_order_response, validate_balance_response
from ..config.constants import BINANCE_ENDPOINTS, MAX_LEVERAGE, MIN_LEVERAGE


class BinanceFuturesExchange(BaseExchange):
    """Binance USDT-M Futures exchange implementation."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        timeout: int = 30000,
        **kwargs
    ):
        """Initialize Binance Futures exchange."""
        super().__init__(api_key, api_secret, testnet, timeout, **kwargs)
        
        self.logger = get_logger("BinanceFutures")
        self.exchange_name = "binance"
        
        # Setup proxy if provided
        proxy = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
        
        # Initialize CCXT exchange for futures
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'timeout': self.timeout,
            'options': {
                'defaultType': 'future',  # Use futures
                'fetchMarkets': {
                    'spot': False,
                    'margin': False,
                    'swap': True,    # USDT-M futures
                    'future': True
                },
                'fetchCurrencies': False,
                'recvWindow': 5000,
                'adjustForTimeDifference': True,
                'warnOnFetchOpenOrdersWithoutSymbol': False,
            },
            'aiohttp_proxy': proxy,
            'verbose': False
        })
        
        # Set testnet if enabled
        if self.testnet:
            self.exchange.set_sandbox_mode(True)
            self.logger.info("Futures testnet mode enabled")
    
    async def initialize(self) -> bool:
        """Initialize exchange connection and load market data."""
        try:
            self.logger.info("Initializing Binance Futures exchange...")
            
            # Load markets
            await self.exchange.load_markets()
            
            # Store symbol information
            for symbol, market in self.exchange.markets.items():
                if market.get('type') == 'swap' and market.get('quote') == 'USDT':  # USDT-M futures only
                    self.symbol_info[symbol] = {
                        'id': market.get('id'),
                        'symbol': market.get('symbol'),
                        'base': market.get('base'),
                        'quote': market.get('quote'),
                        'active': market.get('active'),
                        'precision': market.get('precision', {}),
                        'limits': market.get('limits', {}),
                        'info': market.get('info', {}),
                        'contract_size': market.get('contractSize', 1),
                        'linear': market.get('linear', True),
                        'settle': market.get('settle', 'USDT')
                    }
            
            # Test connection
            balance = await self.exchange.fetch_balance()
            
            self.is_connected = True
            self.logger.info(f"Successfully connected to Binance Futures ({'Testnet' if self.testnet else 'Mainnet'})")
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"Failed to initialize Binance Futures: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.is_connected = False
            return False
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get futures account balance."""
        try:
            balance = await self.exchange.fetch_balance()
            
            if not validate_balance_response(balance):
                raise ValueError("Invalid balance response format")
            
            return balance
            
        except Exception as e:
            self.logger.error(f"Failed to get balance: {str(e)}")
            raise
    
    async def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position information for symbol."""
        try:
            positions = await self.exchange.fetch_positions([symbol])

            if not positions:
                return {
                    'symbol': symbol,
                    'side': 'none',
                    'size': 0,
                    'notional': 0,
                    'leverage': 1,
                    'unrealized_pnl': 0,
                    'percentage': 0,
                    'entry_price': 0,
                    'mark_price': 0
                }

            position = positions[0]

            # Debug log to see the actual structure
            self.logger.debug(f"Position data for {symbol}: {position}")

            # Safely extract values with fallbacks
            def safe_float(value, default=0.0):
                try:
                    return float(value) if value is not None else default
                except (ValueError, TypeError):
                    return default

            def safe_get(data, key, default=None):
                """Safely get value from dict with multiple possible keys"""
                if isinstance(data, dict):
                    # Try different possible key names
                    possible_keys = [key, key.lower(), key.upper()]
                    for k in possible_keys:
                        if k in data:
                            return data[k]
                return default

            return {
                'symbol': safe_get(position, 'symbol', symbol),
                'side': safe_get(position, 'side', 'none'),
                'size': safe_float(safe_get(position, 'size', 0)),
                'notional': safe_float(safe_get(position, 'notional', 0)),
                'leverage': safe_float(safe_get(position, 'leverage', 1)),
                'unrealized_pnl': safe_float(safe_get(position, 'unrealizedPnl', 0)),
                'percentage': safe_float(safe_get(position, 'percentage', 0)),
                'entry_price': safe_float(safe_get(position, 'entryPrice', 0)),
                'mark_price': safe_float(safe_get(position, 'markPrice', 0)),
                'contracts': safe_float(safe_get(position, 'contracts', 0))
            }

        except Exception as e:
            self.logger.error(f"Failed to get position for {symbol}: {str(e)}")
            # Return empty position instead of raising
            return {
                'symbol': symbol,
                'side': 'none',
                'size': 0,
                'notional': 0,
                'leverage': 1,
                'unrealized_pnl': 0,
                'percentage': 0,
                'entry_price': 0,
                'mark_price': 0
            }
    
    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new futures order."""
        try:
            # Validate parameters
            if not self.validate_order_params(symbol, side, amount, price):
                raise ValueError("Invalid order parameters")
            
            # Adjust precision
            adjusted_amount = self.adjust_amount_precision(symbol, amount)
            adjusted_price = self.adjust_price_precision(symbol, price) if price else None
            
            self.logger.info(
                f"Creating futures {order_type} {side} order: "
                f"{symbol} {adjusted_amount} @ {adjusted_price or 'market'}"
            )
            
            # Create order
            if order_type.lower() == 'market':
                order = await self.exchange.create_market_order(
                    symbol, side, adjusted_amount, **kwargs
                )
            else:  # limit order
                if adjusted_price is None:
                    raise ValueError("Price required for limit orders")

                order = await self.exchange.create_limit_order(
                    symbol, side, adjusted_amount, adjusted_price, **kwargs
                )
            
            if not validate_order_response(order):
                raise ValueError("Invalid order response format")
            
            self.logger.info(f"Futures order created successfully: {order['id']}")
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to create futures order: {str(e)}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an existing futures order."""
        try:
            self.logger.info(f"Cancelling futures order {order_id} for {symbol}")
            
            order = await self.exchange.cancel_order(order_id, symbol)
            
            self.logger.info(f"Futures order cancelled successfully: {order_id}")
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to cancel futures order {order_id}: {str(e)}")
            raise
    
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get futures order status."""
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to get futures order status {order_id}: {str(e)}")
            raise
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open futures orders."""
        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get open futures orders: {str(e)}")
            raise
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get futures ticker information."""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker
            
        except Exception as e:
            self.logger.error(f"Failed to get futures ticker for {symbol}: {str(e)}")
            raise
    
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[List]:
        """Get futures kline/candlestick data."""
        try:
            # Convert interval to CCXT format if needed
            timeframe_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
                '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
            }
            
            timeframe = timeframe_map.get(interval, interval)
            
            klines = await self.exchange.fetch_ohlcv(
                symbol, timeframe, start_time, limit
            )
            
            return klines
            
        except Exception as e:
            self.logger.error(f"Failed to get futures klines for {symbol}: {str(e)}")
            raise
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for futures symbol."""
        try:
            if not (MIN_LEVERAGE <= leverage <= MAX_LEVERAGE):
                raise ValueError(f"Leverage must be between {MIN_LEVERAGE} and {MAX_LEVERAGE}")
            
            self.logger.info(f"Setting leverage for {symbol} to {leverage}x")
            
            # Set leverage using CCXT
            result = await self.exchange.set_leverage(leverage, symbol)
            
            self.logger.info(f"Leverage set successfully for {symbol}: {leverage}x")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to set leverage for {symbol}: {str(e)}")
            raise
    
    def is_futures_mode(self) -> bool:
        """Check if exchange is in futures mode."""
        return True
    
    async def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """Get funding rate for futures symbol."""
        try:
            funding_rate = await self.exchange.fetch_funding_rate(symbol)
            return funding_rate
            
        except Exception as e:
            self.logger.error(f"Failed to get funding rate for {symbol}: {str(e)}")
            raise
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close all positions for symbol."""
        try:
            position = await self.get_position(symbol)
            
            if position['size'] == 0:
                return {"message": "No position to close", "symbol": symbol}
            
            # Determine opposite side
            side = 'sell' if position['side'] == 'long' else 'buy'
            amount = abs(position['size'])
            
            # Create market order to close position
            order = await self.create_market_order(symbol, side, amount)
            
            self.logger.info(f"Position closed for {symbol}")
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to close position for {symbol}: {str(e)}")
            raise
