"""
Position manager for GridTrading Pro.

This module manages trading positions, calculates portfolio metrics,
and handles position-related risk management.
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..config.settings import Settings
from ..exchanges.base_exchange import BaseExchange
from ..notifications.base_notifier import BaseNotifier
from ..utils.logger import get_logger
from ..utils.helpers import calculate_percentage_change, safe_divide


@dataclass
class PositionInfo:
    """Position information data class."""
    symbol: str
    side: str  # 'long', 'short', 'none'
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    percentage: float
    notional_value: float
    leverage: int = 1


@dataclass
class PortfolioMetrics:
    """Portfolio metrics data class."""
    total_balance: float
    available_balance: float
    position_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    position_ratio: float
    leverage_ratio: float
    margin_ratio: float = 0.0  # For futures


class PositionManager:
    """Position and portfolio management."""
    
    def __init__(
        self,
        settings: Settings,
        exchange: BaseExchange,
        notifier: Optional[BaseNotifier] = None
    ):
        """Initialize position manager."""
        self.settings = settings
        self.exchange = exchange
        self.notifier = notifier
        self.logger = get_logger("PositionManager")
        
        # Position tracking
        self.positions: Dict[str, PositionInfo] = {}
        self.portfolio_metrics = PortfolioMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        # Update intervals
        self.last_update_time = 0
        self.update_interval = 30  # seconds
        
        # Performance tracking
        self.peak_portfolio_value = 0
        self.max_drawdown = 0
        self.daily_pnl = 0
        self.daily_start_value = 0
        self.last_daily_reset = 0
    
    async def initialize(self) -> bool:
        """Initialize position manager."""
        try:
            self.logger.info("Initializing position manager...")
            
            # Load initial positions
            await self.update_positions()
            
            # Set initial portfolio value
            self.peak_portfolio_value = self.portfolio_metrics.total_balance
            self.daily_start_value = self.portfolio_metrics.total_balance
            self.last_daily_reset = time.time()
            
            self.logger.info("Position manager initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize position manager: {str(e)}")
            return False
    
    async def update_positions(self) -> None:
        """Update all positions and portfolio metrics."""
        current_time = time.time()
        
        # Check if update is needed
        if current_time - self.last_update_time < self.update_interval:
            return
        
        try:
            # Update positions
            await self._update_position_data()
            
            # Update portfolio metrics
            await self._update_portfolio_metrics()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Check daily reset
            self._check_daily_reset()
            
            self.last_update_time = current_time
            
        except Exception as e:
            self.logger.error(f"Failed to update positions: {str(e)}")
    
    async def _update_position_data(self) -> None:
        """Update position data from exchange."""
        try:
            symbol = self.settings.trading.symbol
            
            if self.exchange.is_futures_mode():
                # Get futures position
                position_data = await self.exchange.get_position(symbol)
                
                if position_data and position_data.get('size', 0) != 0:
                    self.positions[symbol] = PositionInfo(
                        symbol=symbol,
                        side=position_data.get('side', 'none'),
                        size=float(position_data.get('size', 0)),
                        entry_price=float(position_data.get('entry_price', 0)),
                        current_price=float(position_data.get('mark_price', 0)),
                        unrealized_pnl=float(position_data.get('unrealized_pnl', 0)),
                        realized_pnl=0,  # Would need separate tracking
                        percentage=float(position_data.get('percentage', 0)),
                        notional_value=float(position_data.get('notional', 0)),
                        leverage=int(position_data.get('leverage', 1))
                    )
                else:
                    # No position
                    if symbol in self.positions:
                        del self.positions[symbol]
            
            else:
                # Get spot "position" (balance)
                balance = await self.exchange.get_balance()
                ticker = await self.exchange.get_ticker(symbol)
                current_price = float(ticker['last'])
                
                # Get base asset balance
                base_asset = symbol.split('/')[0]
                base_balance = float(balance.get('total', {}).get(base_asset, 0))
                
                if base_balance > 0:
                    # Calculate average entry price (simplified)
                    entry_price = current_price  # Would need trade history for accurate calculation
                    notional_value = base_balance * current_price
                    unrealized_pnl = (current_price - entry_price) * base_balance
                    
                    self.positions[symbol] = PositionInfo(
                        symbol=symbol,
                        side='long' if base_balance > 0 else 'none',
                        size=base_balance,
                        entry_price=entry_price,
                        current_price=current_price,
                        unrealized_pnl=unrealized_pnl,
                        realized_pnl=0,
                        percentage=0,  # Would need calculation
                        notional_value=notional_value,
                        leverage=1
                    )
                else:
                    # No position
                    if symbol in self.positions:
                        del self.positions[symbol]
        
        except Exception as e:
            self.logger.error(f"Failed to update position data: {str(e)}")
            # Don't raise - continue with other operations
    
    async def _update_portfolio_metrics(self) -> None:
        """Update portfolio metrics."""
        try:
            # Get account balance
            balance = await self.exchange.get_balance()
            
            if self.exchange.is_futures_mode():
                # Futures account metrics
                total_balance = float(balance.get('total', {}).get('USDT', 0))
                available_balance = float(balance.get('free', {}).get('USDT', 0))
                
                # Calculate position value and PnL
                position_value = sum(pos.notional_value for pos in self.positions.values())
                unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
                
                # Calculate ratios
                position_ratio = safe_divide(position_value, total_balance)
                leverage_ratio = safe_divide(position_value, available_balance)
                margin_ratio = safe_divide(position_value - available_balance, total_balance)
                
            else:
                # Spot account metrics
                usdt_balance = float(balance.get('total', {}).get('USDT', 0))
                
                # Calculate total portfolio value
                total_value = usdt_balance
                for asset, amount in balance.get('total', {}).items():
                    if asset != 'USDT' and float(amount) > 0:
                        try:
                            ticker = await self.exchange.get_ticker(f"{asset}/USDT")
                            price = float(ticker['last'])
                            total_value += float(amount) * price
                        except:
                            continue  # Skip if can't get price
                
                position_value = sum(pos.notional_value for pos in self.positions.values())
                unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
                
                total_balance = total_value
                available_balance = usdt_balance
                position_ratio = safe_divide(position_value, total_balance)
                leverage_ratio = 1.0  # Always 1 for spot
                margin_ratio = 0.0
            
            # Update portfolio metrics
            self.portfolio_metrics = PortfolioMetrics(
                total_balance=total_balance,
                available_balance=available_balance,
                position_value=position_value,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=self.portfolio_metrics.realized_pnl,  # Keep existing
                total_pnl=unrealized_pnl + self.portfolio_metrics.realized_pnl,
                position_ratio=position_ratio,
                leverage_ratio=leverage_ratio,
                margin_ratio=margin_ratio
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update portfolio metrics: {str(e)}")
            # Don't raise - continue with other operations
    
    def _update_performance_metrics(self) -> None:
        """Update performance tracking metrics."""
        try:
            current_value = self.portfolio_metrics.total_balance
            
            # Update peak value and drawdown
            if current_value > self.peak_portfolio_value:
                self.peak_portfolio_value = current_value
            
            # Calculate current drawdown
            if self.peak_portfolio_value > 0:
                current_drawdown = (current_value - self.peak_portfolio_value) / self.peak_portfolio_value
                self.max_drawdown = min(self.max_drawdown, current_drawdown)
            
            # Update daily PnL
            if self.daily_start_value > 0:
                self.daily_pnl = (current_value - self.daily_start_value) / self.daily_start_value
        
        except Exception as e:
            self.logger.error(f"Failed to update performance metrics: {str(e)}")
    
    def _check_daily_reset(self) -> None:
        """Check if daily metrics should be reset."""
        current_time = time.time()
        
        # Reset daily metrics at midnight UTC
        if current_time - self.last_daily_reset > 86400:  # 24 hours
            self.daily_start_value = self.portfolio_metrics.total_balance
            self.daily_pnl = 0
            self.last_daily_reset = current_time
            
            self.logger.info("Daily metrics reset")
    
    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """Get position information for symbol."""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, PositionInfo]:
        """Get all positions."""
        return self.positions.copy()
    
    def get_portfolio_metrics(self) -> PortfolioMetrics:
        """Get current portfolio metrics."""
        return self.portfolio_metrics
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics."""
        return {
            'peak_value': self.peak_portfolio_value,
            'max_drawdown': self.max_drawdown,
            'daily_pnl': self.daily_pnl,
            'total_pnl_percentage': safe_divide(
                self.portfolio_metrics.total_pnl,
                self.daily_start_value
            ) * 100
        }
    
    async def check_risk_limits(self) -> List[str]:
        """Check position against risk limits."""
        warnings = []
        
        try:
            # Check position ratio
            if self.portfolio_metrics.position_ratio > self.settings.risk.max_position_ratio:
                warnings.append(f"Position ratio exceeded: {self.portfolio_metrics.position_ratio:.2%}")
            
            if self.portfolio_metrics.position_ratio < self.settings.risk.min_position_ratio:
                warnings.append(f"Position ratio below minimum: {self.portfolio_metrics.position_ratio:.2%}")
            
            # Check drawdown
            if self.max_drawdown < self.settings.risk.max_drawdown:
                warnings.append(f"Max drawdown exceeded: {self.max_drawdown:.2%}")
            
            # Check daily loss
            if self.daily_pnl < self.settings.risk.daily_loss_limit:
                warnings.append(f"Daily loss limit exceeded: {self.daily_pnl:.2%}")
            
            # Send notifications for warnings
            if warnings and self.notifier:
                for warning in warnings:
                    await self.notifier.notify_risk_alert(
                        "POSITION_RISK",
                        self.portfolio_metrics.position_ratio,
                        self.settings.risk.max_position_ratio,
                        "MONITOR"
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to check risk limits: {str(e)}")
        
        return warnings
    
    async def close(self) -> None:
        """Close position manager."""
        self.logger.info("Position manager closed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get position manager status."""
        return {
            'total_positions': len(self.positions),
            'portfolio_value': self.portfolio_metrics.total_balance,
            'position_ratio': self.portfolio_metrics.position_ratio,
            'unrealized_pnl': self.portfolio_metrics.unrealized_pnl,
            'daily_pnl': self.daily_pnl,
            'max_drawdown': self.max_drawdown,
            'positions': {
                symbol: {
                    'side': pos.side,
                    'size': pos.size,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'percentage': pos.percentage
                }
                for symbol, pos in self.positions.items()
            }
        }
