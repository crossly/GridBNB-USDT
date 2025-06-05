"""
S1 strategy implementation for GridTrading Pro.

This module implements the S1 strategy based on 52-day high/low breakouts
for position adjustment and rebalancing.
"""

import time
from typing import Dict, Any, Optional, List

from ..core.strategy_manager import BaseStrategy
from ..config.settings import Settings
from ..exchanges.base_exchange import BaseExchange
from ..notifications.base_notifier import BaseNotifier
from ..utils.helpers import calculate_percentage_change, safe_divide


class S1Strategy(BaseStrategy):
    """S1 strategy implementation based on 52-day high/low breakouts."""
    
    def __init__(
        self,
        name: str,
        settings: Settings,
        exchange: BaseExchange,
        notifier: Optional[BaseNotifier] = None
    ):
        """Initialize S1 strategy."""
        super().__init__(name, settings, exchange, notifier)
        
        # S1 parameters
        self.lookback_days = settings.s1_strategy.lookback_days
        self.sell_target_percent = settings.s1_strategy.sell_target_percent
        self.buy_target_percent = settings.s1_strategy.buy_target_percent
        
        # State tracking
        self.daily_high = None
        self.daily_low = None
        self.last_data_update = 0
        self.daily_update_interval = 23.9 * 60 * 60  # ~24 hours
        
        # Position tracking
        self.current_position_ratio = 0.0
        self.last_adjustment_time = 0
        self.min_adjustment_interval = 300  # 5 minutes
    
    async def initialize(self) -> bool:
        """Initialize S1 strategy."""
        try:
            self.logger.info(f"Initializing {self.name} strategy...")
            
            # Fetch initial high/low data
            await self._update_daily_levels()
            
            self.logger.info(
                f"{self.name} strategy initialized - "
                f"Lookback: {self.lookback_days} days, "
                f"Sell target: {self.sell_target_percent:.0%}, "
                f"Buy target: {self.buy_target_percent:.0%}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name} strategy: {str(e)}")
            return False
    
    async def execute(self, grid_state: Any) -> Dict[str, Any]:
        """Execute S1 strategy logic."""
        try:
            if not self.enabled:
                return {'action': 'NONE', 'reason': 'Strategy disabled'}
            
            current_time = time.time()
            
            # Update daily high/low levels if needed
            await self._check_and_update_levels()
            
            # Skip if no levels available
            if self.daily_high is None or self.daily_low is None:
                return {'action': 'NONE', 'reason': 'No daily levels available'}
            
            # Get current market state
            current_price = grid_state.current_price
            
            # Update current position ratio
            await self._update_position_ratio()
            
            # Check for S1 signals
            signal = await self._check_s1_signals(current_price)
            
            # Update last execution time
            self.last_execution_time = current_time
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error executing {self.name} strategy: {str(e)}")
            return {'action': 'ERROR', 'error': str(e)}
    
    async def _check_and_update_levels(self) -> None:
        """Check if daily levels need updating."""
        current_time = time.time()
        
        if current_time - self.last_data_update >= self.daily_update_interval:
            await self._update_daily_levels()
    
    async def _update_daily_levels(self) -> None:
        """Update daily high/low levels."""
        try:
            self.logger.info("Updating S1 daily levels...")
            
            # Get historical kline data
            symbol = self.settings.trading.symbol
            klines = await self.exchange.get_klines(
                symbol=symbol,
                interval='1d',
                limit=self.lookback_days + 2
            )
            
            if not klines or len(klines) < self.lookback_days + 1:
                self.logger.warning(f"Insufficient kline data: {len(klines) if klines else 0}")
                return
            
            # Use completed daily candles (exclude current incomplete day)
            relevant_klines = klines[-(self.lookback_days + 1):-1]
            
            if len(relevant_klines) < self.lookback_days:
                self.logger.warning(f"Not enough relevant klines: {len(relevant_klines)}")
                return
            
            # Calculate high and low (index 2=high, 3=low)
            highs = [float(kline[2]) for kline in relevant_klines]
            lows = [float(kline[3]) for kline in relevant_klines]
            
            self.daily_high = max(highs)
            self.daily_low = min(lows)
            self.last_data_update = time.time()
            
            self.logger.info(
                f"S1 levels updated - High: {self.daily_high:.4f}, Low: {self.daily_low:.4f}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update daily levels: {str(e)}")
    
    async def _update_position_ratio(self) -> None:
        """Update current position ratio."""
        try:
            # Get account balance
            balance = await self.exchange.get_balance()
            
            # Calculate position value and total assets
            if self.exchange.is_futures_mode():
                # Futures position
                symbol = self.settings.trading.symbol
                position = await self.exchange.get_position(symbol)
                position_value = abs(float(position.get('notional', 0)))
                total_balance = float(balance.get('total', {}).get('USDT', 0))
                
            else:
                # Spot position
                symbol = self.settings.trading.symbol
                base_asset = symbol.split('/')[0]
                base_balance = float(balance.get('total', {}).get(base_asset, 0))
                usdt_balance = float(balance.get('total', {}).get('USDT', 0))
                
                # Get current price
                ticker = await self.exchange.get_ticker(symbol)
                current_price = float(ticker['last'])
                
                position_value = base_balance * current_price
                total_balance = position_value + usdt_balance
            
            # Calculate position ratio
            self.current_position_ratio = safe_divide(position_value, total_balance)
            
        except Exception as e:
            self.logger.error(f"Failed to update position ratio: {str(e)}")
    
    async def _check_s1_signals(self, current_price: float) -> Dict[str, Any]:
        """Check for S1 trading signals."""
        try:
            current_time = time.time()
            
            # Check minimum interval between adjustments
            if current_time - self.last_adjustment_time < self.min_adjustment_interval:
                return {'action': 'NONE', 'reason': 'Too soon for adjustment'}
            
            # Check high breakout (sell signal)
            if current_price > self.daily_high and self.current_position_ratio > self.sell_target_percent:
                adjustment_needed = self.current_position_ratio - self.sell_target_percent
                
                return {
                    'action': 'SELL',
                    'reason': f'High breakout - reduce position to {self.sell_target_percent:.0%}',
                    'current_ratio': self.current_position_ratio,
                    'target_ratio': self.sell_target_percent,
                    'adjustment_needed': adjustment_needed,
                    'trigger_price': self.daily_high,
                    'current_price': current_price
                }
            
            # Check low breakout (buy signal)
            elif current_price < self.daily_low and self.current_position_ratio < self.buy_target_percent:
                adjustment_needed = self.buy_target_percent - self.current_position_ratio
                
                return {
                    'action': 'BUY',
                    'reason': f'Low breakout - increase position to {self.buy_target_percent:.0%}',
                    'current_ratio': self.current_position_ratio,
                    'target_ratio': self.buy_target_percent,
                    'adjustment_needed': adjustment_needed,
                    'trigger_price': self.daily_low,
                    'current_price': current_price
                }
            
            return {
                'action': 'NONE',
                'reason': 'No S1 signals',
                'current_ratio': self.current_position_ratio,
                'daily_high': self.daily_high,
                'daily_low': self.daily_low,
                'current_price': current_price
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check S1 signals: {str(e)}")
            return {'action': 'ERROR', 'error': str(e)}
    
    async def execute_adjustment(self, signal: Dict[str, Any]) -> bool:
        """Execute S1 position adjustment."""
        try:
            if signal['action'] not in ['BUY', 'SELL']:
                return False
            
            # Calculate adjustment amount
            adjustment_ratio = signal['adjustment_needed']
            
            # Get total balance for calculation
            balance = await self.exchange.get_balance()
            
            if self.exchange.is_futures_mode():
                total_balance = float(balance.get('total', {}).get('USDT', 0))
            else:
                # For spot, calculate total portfolio value
                total_balance = await self.exchange.get_account_value()
            
            adjustment_value = total_balance * adjustment_ratio
            adjustment_amount = adjustment_value / signal['current_price']
            
            # Adjust for precision
            symbol = self.settings.trading.symbol
            adjusted_amount = self.exchange.adjust_amount_precision(symbol, adjustment_amount)
            
            if adjusted_amount <= 0:
                self.logger.warning("Adjustment amount too small")
                return False
            
            # Execute market order
            order = await self.exchange.create_market_order(
                symbol=symbol,
                side=signal['action'].lower(),
                amount=adjusted_amount
            )
            
            self.last_adjustment_time = time.time()
            
            self.logger.info(
                f"S1 adjustment executed: {signal['action']} {adjusted_amount:.6f} "
                f"@ ~{signal['current_price']:.4f}"
            )
            
            if self.notifier:
                await self.notifier.notify_trade_execution(
                    signal['action'].lower(),
                    symbol,
                    signal['current_price'],
                    adjusted_amount,
                    adjusted_amount * signal['current_price'],
                    'S1'
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute S1 adjustment: {str(e)}")
            return False
    
    def get_s1_info(self) -> Dict[str, Any]:
        """Get current S1 strategy information."""
        return {
            'daily_high': self.daily_high,
            'daily_low': self.daily_low,
            'current_position_ratio': self.current_position_ratio,
            'sell_target_percent': self.sell_target_percent,
            'buy_target_percent': self.buy_target_percent,
            'lookback_days': self.lookback_days,
            'last_data_update': self.last_data_update,
            'last_adjustment': self.last_adjustment_time
        }
    
    async def close(self) -> None:
        """Close S1 strategy."""
        self.logger.info(f"{self.name} strategy closed")
