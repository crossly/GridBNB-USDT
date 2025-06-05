"""
Grid trading strategy implementation for GridTrading Pro.

This module implements the core grid trading strategy logic with dynamic
grid adjustment and position management.
"""

import time
from typing import Dict, Any, Optional

from ..core.strategy_manager import BaseStrategy
from ..config.settings import Settings
from ..exchanges.base_exchange import BaseExchange
from ..notifications.base_notifier import BaseNotifier
from ..utils.helpers import calculate_grid_levels, calculate_volatility


class GridStrategy(BaseStrategy):
    """Grid trading strategy implementation."""
    
    def __init__(
        self,
        name: str,
        settings: Settings,
        exchange: BaseExchange,
        notifier: Optional[BaseNotifier] = None
    ):
        """Initialize grid strategy."""
        super().__init__(name, settings, exchange, notifier)
        
        # Grid parameters
        self.grid_size = settings.grid.initial_size
        self.min_grid_size = settings.grid.min_size
        self.max_grid_size = settings.grid.max_size
        self.dynamic_adjustment = settings.grid.dynamic_adjustment
        
        # State tracking
        self.last_adjustment_time = 0
        self.adjustment_interval = 3600  # 1 hour default
        
        # Grid levels
        self.buy_levels = []
        self.sell_levels = []
        self.active_orders = {}
    
    async def initialize(self) -> bool:
        """Initialize grid strategy."""
        try:
            self.logger.info(f"Initializing {self.name} strategy...")
            
            # Load any saved state
            # This would typically load from persistent storage
            
            self.logger.info(f"{self.name} strategy initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name} strategy: {str(e)}")
            return False
    
    async def execute(self, grid_state: Any) -> Dict[str, Any]:
        """Execute grid strategy logic."""
        try:
            if not self.enabled:
                return {'action': 'NONE', 'reason': 'Strategy disabled'}
            
            current_time = time.time()
            
            # Update grid size if dynamic adjustment is enabled
            if self.dynamic_adjustment:
                await self._adjust_grid_size(grid_state)
            
            # Calculate grid levels
            self._calculate_grid_levels(grid_state.base_price)
            
            # Check for trading signals
            signal = await self._check_trading_signals(grid_state)
            
            # Update last execution time
            self.last_execution_time = current_time
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error executing {self.name} strategy: {str(e)}")
            return {'action': 'ERROR', 'error': str(e)}
    
    async def _adjust_grid_size(self, grid_state: Any) -> None:
        """Adjust grid size based on market volatility."""
        try:
            current_time = time.time()
            
            # Check if adjustment is needed
            if current_time - self.last_adjustment_time < self.adjustment_interval:
                return
            
            # Calculate new grid size based on volatility
            volatility = grid_state.volatility
            new_grid_size = self._get_optimal_grid_size(volatility)
            
            # Apply adjustment if significant change
            if abs(new_grid_size - self.grid_size) > 0.1:
                old_size = self.grid_size
                self.grid_size = new_grid_size
                self.last_adjustment_time = current_time
                
                self.logger.info(
                    f"Grid size adjusted: {old_size:.1f}% → {new_grid_size:.1f}% "
                    f"(volatility: {volatility:.2%})"
                )
                
                if self.notifier:
                    await self.notifier.notify_strategy_signal(
                        self.name,
                        "GRID_ADJUSTMENT",
                        grid_state.current_price,
                        f"Size: {old_size:.1f}% → {new_grid_size:.1f}%"
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to adjust grid size: {str(e)}")
    
    def _get_optimal_grid_size(self, volatility: float) -> float:
        """Get optimal grid size based on volatility."""
        # Use volatility thresholds from settings
        for threshold in self.settings.grid.volatility_thresholds:
            vol_range = threshold['range']
            if vol_range[0] <= volatility < vol_range[1]:
                return min(max(threshold['grid_size'], self.min_grid_size), self.max_grid_size)
        
        # Default to max grid size for very high volatility
        return self.max_grid_size
    
    def _calculate_grid_levels(self, base_price: float) -> None:
        """Calculate grid buy and sell levels."""
        try:
            grid_levels = calculate_grid_levels(base_price, self.grid_size, num_levels=10)
            self.buy_levels = grid_levels['buy_levels']
            self.sell_levels = grid_levels['sell_levels']
            
        except Exception as e:
            self.logger.error(f"Failed to calculate grid levels: {str(e)}")
    
    async def _check_trading_signals(self, grid_state: Any) -> Dict[str, Any]:
        """Check for grid trading signals."""
        try:
            current_price = grid_state.current_price
            
            # Check buy signals (price near buy levels)
            for i, buy_level in enumerate(self.buy_levels):
                if abs(current_price - buy_level) / buy_level < 0.001:  # Within 0.1%
                    return {
                        'action': 'BUY',
                        'price': buy_level,
                        'level': i + 1,
                        'reason': f'Price near buy level {i + 1}: {buy_level:.4f}'
                    }
            
            # Check sell signals (price near sell levels)
            for i, sell_level in enumerate(self.sell_levels):
                if abs(current_price - sell_level) / sell_level < 0.001:  # Within 0.1%
                    return {
                        'action': 'SELL',
                        'price': sell_level,
                        'level': i + 1,
                        'reason': f'Price near sell level {i + 1}: {sell_level:.4f}'
                    }
            
            return {'action': 'NONE', 'reason': 'No grid signals'}
            
        except Exception as e:
            self.logger.error(f"Failed to check trading signals: {str(e)}")
            return {'action': 'ERROR', 'error': str(e)}
    
    def get_grid_info(self) -> Dict[str, Any]:
        """Get current grid information."""
        return {
            'grid_size': self.grid_size,
            'buy_levels': self.buy_levels[:5],  # Show first 5 levels
            'sell_levels': self.sell_levels[:5],
            'last_adjustment': self.last_adjustment_time,
            'dynamic_adjustment': self.dynamic_adjustment
        }
    
    async def close(self) -> None:
        """Close grid strategy."""
        # Cancel any active orders
        # Save state if needed
        self.logger.info(f"{self.name} strategy closed")
