"""
Strategy manager for GridTrading Pro.

This module manages multiple trading strategies and coordinates their execution
with the main grid trading engine.
"""

import asyncio
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from ..config.settings import Settings
from ..exchanges.base_exchange import BaseExchange
from ..notifications.base_notifier import BaseNotifier
from ..utils.logger import get_logger


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""
    
    def __init__(
        self,
        name: str,
        settings: Settings,
        exchange: BaseExchange,
        notifier: Optional[BaseNotifier] = None
    ):
        """Initialize base strategy."""
        self.name = name
        self.settings = settings
        self.exchange = exchange
        self.notifier = notifier
        self.logger = get_logger(f"Strategy.{name}")
        self.enabled = True
        self.last_execution_time = 0
    
    @abstractmethod
    async def execute(self, grid_state: Any) -> Dict[str, Any]:
        """Execute strategy logic."""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize strategy."""
        pass
    
    async def close(self) -> None:
        """Close strategy and cleanup resources."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if strategy is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable strategy."""
        self.enabled = True
        self.logger.info(f"Strategy {self.name} enabled")
    
    def disable(self) -> None:
        """Disable strategy."""
        self.enabled = False
        self.logger.info(f"Strategy {self.name} disabled")


class StrategyManager:
    """Manager for multiple trading strategies."""
    
    def __init__(
        self,
        settings: Settings,
        exchange: BaseExchange,
        notifier: Optional[BaseNotifier] = None
    ):
        """Initialize strategy manager."""
        self.settings = settings
        self.exchange = exchange
        self.notifier = notifier
        self.logger = get_logger("StrategyManager")
        
        # Strategy registry
        self.strategies: Dict[str, BaseStrategy] = {}
        self.execution_order: List[str] = []
        
        # Execution control
        self.is_running = False
        self.execution_interval = 5  # seconds
    
    async def initialize(self) -> bool:
        """Initialize strategy manager and load strategies."""
        try:
            self.logger.info("Initializing strategy manager...")
            
            # Load and initialize strategies
            await self._load_strategies()
            
            # Initialize all strategies
            for strategy in self.strategies.values():
                if not await strategy.initialize():
                    self.logger.error(f"Failed to initialize strategy: {strategy.name}")
                    return False
            
            self.logger.info(f"Strategy manager initialized with {len(self.strategies)} strategies")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize strategy manager: {str(e)}")
            return False
    
    async def _load_strategies(self) -> None:
        """Load available strategies."""
        # Import strategy implementations
        from ..strategies.s1_strategy import S1Strategy
        
        # Load S1 strategy if enabled
        if self.settings.s1_strategy.enabled:
            s1_strategy = S1Strategy(
                "S1",
                self.settings,
                self.exchange,
                self.notifier
            )
            await self.add_strategy(s1_strategy)
    
    async def add_strategy(self, strategy: BaseStrategy) -> None:
        """Add a strategy to the manager."""
        self.strategies[strategy.name] = strategy
        self.execution_order.append(strategy.name)
        self.logger.info(f"Added strategy: {strategy.name}")
    
    async def remove_strategy(self, name: str) -> bool:
        """Remove a strategy from the manager."""
        if name in self.strategies:
            strategy = self.strategies[name]
            await strategy.close()
            del self.strategies[name]
            
            if name in self.execution_order:
                self.execution_order.remove(name)
            
            self.logger.info(f"Removed strategy: {name}")
            return True
        
        return False
    
    async def execute_strategies(self, grid_state: Any) -> Dict[str, Any]:
        """Execute all enabled strategies."""
        results = {}
        
        for strategy_name in self.execution_order:
            strategy = self.strategies.get(strategy_name)
            
            if not strategy or not strategy.is_enabled():
                continue
            
            try:
                result = await strategy.execute(grid_state)
                results[strategy_name] = result
                
                # Log strategy execution
                if result.get('action') != 'NONE':
                    self.logger.info(f"Strategy {strategy_name} executed: {result}")
                
            except Exception as e:
                self.logger.error(f"Strategy {strategy_name} execution failed: {str(e)}")
                results[strategy_name] = {'error': str(e)}
        
        return results
    
    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """Get strategy by name."""
        return self.strategies.get(name)
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """List all strategies with their status."""
        return [
            {
                'name': strategy.name,
                'enabled': strategy.is_enabled(),
                'last_execution': strategy.last_execution_time
            }
            for strategy in self.strategies.values()
        ]
    
    async def enable_strategy(self, name: str) -> bool:
        """Enable a strategy."""
        strategy = self.strategies.get(name)
        if strategy:
            strategy.enable()
            return True
        return False
    
    async def disable_strategy(self, name: str) -> bool:
        """Disable a strategy."""
        strategy = self.strategies.get(name)
        if strategy:
            strategy.disable()
            return True
        return False
    
    async def close(self) -> None:
        """Close strategy manager and all strategies."""
        self.logger.info("Closing strategy manager...")
        
        for strategy in self.strategies.values():
            try:
                await strategy.close()
            except Exception as e:
                self.logger.error(f"Error closing strategy {strategy.name}: {str(e)}")
        
        self.strategies.clear()
        self.execution_order.clear()
        
        self.logger.info("Strategy manager closed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get strategy manager status."""
        return {
            'total_strategies': len(self.strategies),
            'enabled_strategies': sum(1 for s in self.strategies.values() if s.is_enabled()),
            'strategies': self.list_strategies()
        }
