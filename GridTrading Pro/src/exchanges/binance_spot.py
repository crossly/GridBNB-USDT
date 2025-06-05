"""
Binance Spot exchange implementation for GridTrading Pro.

This module provides Binance Spot trading functionality with support for
testnet environment and comprehensive error handling.
"""

import ccxt.async_support as ccxt
import os
from typing import Dict, List, Optional, Any
import asyncio

from .base_exchange import BaseExchange
from ..utils.logger import get_logger
from ..utils.validators import validate_order_response, validate_balance_response
from ..config.constants import BINANCE_ENDPOINTS


class BinanceSpotExchange(BaseExchange):
    """Binance Spot exchange implementation."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        timeout: int = 30000,
        **kwargs
    ):
        """Initialize Binance Spot exchange."""
        super().__init__(api_key, api_secret, testnet, timeout, **kwargs)
        
        self.logger = get_logger("BinanceSpot")
        self.exchange_name = "binance"
        
        # Setup proxy if provided
        proxy = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
        
        # Initialize CCXT exchange
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'timeout': self.timeout,
            'options': {
                'defaultType': 'spot',
                'fetchMarkets': {
                    'spot': True,
                    'margin': False,
                    'swap': False,
                    'future': False
                },
                'fetchCurrencies': False,
                'recvWindow': 5000,
                'adjustForTimeDifference': True,
                'warnOnFetchOpenOrdersWithoutSymbol': False,
                'createMarketBuyOrderRequiresPrice': False
            },
            'aiohttp_proxy': proxy,
            'verbose': False
        })
        
        # Set testnet if enabled
        if self.testnet:
            self.exchange.set_sandbox_mode(True)
            self.logger.info("Testnet mode enabled")
    
    async def initialize(self) -> bool:
        """Initialize exchange connection and load market data."""
        try:
            self.logger.info("Initializing Binance Spot exchange...")
            
            # Load markets
            await self.exchange.load_markets()
            
            # Store symbol information
            for symbol, market in self.exchange.markets.items():
                self.symbol_info[symbol] = {
                    'id': market['id'],
                    'symbol': market['symbol'],
                    'base': market['base'],
                    'quote': market['quote'],
                    'active': market['active'],
                    'precision': market['precision'],
                    'limits': market['limits'],
                    'info': market['info']
                }
            
            # Test connection
            balance = await self.exchange.fetch_balance()
            
            self.is_connected = True
            self.logger.info(f"Successfully connected to Binance Spot ({'Testnet' if self.testnet else 'Mainnet'})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Binance Spot: {str(e)}")
            self.is_connected = False
            return False
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        try:
            balance = await self.exchange.fetch_balance()
            
            if not validate_balance_response(balance):
                raise ValueError("Invalid balance response format")
            
            return balance
            
        except Exception as e:
            self.logger.error(f"Failed to get balance: {str(e)}")
            raise
    
    async def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position information for symbol (spot trading doesn't have positions)."""
        # For spot trading, return balance information
        balance = await self.get_balance()
        symbol_info = self.get_symbol_info(symbol)
        
        if not symbol_info:
            return {}
        
        base_asset = symbol_info['base']
        quote_asset = symbol_info['quote']
        
        base_balance = balance.get('total', {}).get(base_asset, 0)
        quote_balance = balance.get('total', {}).get(quote_asset, 0)
        
        return {
            'symbol': symbol,
            'base_asset': base_asset,
            'quote_asset': quote_asset,
            'base_balance': float(base_balance),
            'quote_balance': float(quote_balance),
            'side': 'long' if base_balance > 0 else 'none',
            'size': float(base_balance),
            'notional': 0,  # Not applicable for spot
            'leverage': 1,  # Always 1 for spot
            'unrealized_pnl': 0,  # Not applicable for spot
            'percentage': 0  # Not applicable for spot
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
        """Create a new order."""
        try:
            # Validate parameters
            if not self.validate_order_params(symbol, side, amount, price):
                raise ValueError("Invalid order parameters")
            
            # Adjust precision
            adjusted_amount = self.adjust_amount_precision(symbol, amount)
            adjusted_price = self.adjust_price_precision(symbol, price) if price else None
            
            self.logger.info(
                f"Creating {order_type} {side} order: "
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
            
            self.logger.info(f"Order created successfully: {order['id']}")
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to create order: {str(e)}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an existing order."""
        try:
            self.logger.info(f"Cancelling order {order_id} for {symbol}")
            
            order = await self.exchange.cancel_order(order_id, symbol)
            
            self.logger.info(f"Order cancelled successfully: {order_id}")
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            raise
    
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status."""
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to get order status {order_id}: {str(e)}")
            raise
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get open orders: {str(e)}")
            raise
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information."""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker
            
        except Exception as e:
            self.logger.error(f"Failed to get ticker for {symbol}: {str(e)}")
            raise
    
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[List]:
        """Get kline/candlestick data."""
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
            self.logger.error(f"Failed to get klines for {symbol}: {str(e)}")
            raise
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for symbol (not applicable for spot trading)."""
        if leverage != 1:
            raise ValueError("Leverage must be 1 for spot trading")
        
        return {"symbol": symbol, "leverage": 1, "message": "Spot trading always uses 1x leverage"}
    
    def is_futures_mode(self) -> bool:
        """Check if exchange is in futures mode."""
        return False
    
    async def get_funding_balance(self) -> Dict[str, float]:
        """Get funding/savings account balance (Binance specific)."""
        try:
            # This would require additional API endpoints for savings account
            # For now, return empty dict
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get funding balance: {str(e)}")
            return {}
    
    async def transfer_to_funding(self, asset: str, amount: float) -> Dict[str, Any]:
        """Transfer funds to savings account (Binance specific)."""
        try:
            # This would require additional API endpoints
            # For now, return success message
            return {
                "asset": asset,
                "amount": amount,
                "status": "success",
                "message": "Transfer to funding account (placeholder)"
            }

        except Exception as e:
            self.logger.error(f"Failed to transfer to funding: {str(e)}")
            raise
