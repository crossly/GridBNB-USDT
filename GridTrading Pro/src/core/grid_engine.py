"""
Grid trading engine for GridTrading Pro.

This module implements the core grid trading logic with dynamic grid adjustment,
position management, and integration with multiple exchanges and strategies.
"""

import asyncio
import time
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..config.settings import Settings
from ..exchanges.base_exchange import BaseExchange
from ..notifications.base_notifier import BaseNotifier
from ..utils.logger import get_logger
from ..utils.helpers import (
    calculate_volatility, calculate_grid_levels, format_timestamp,
    calculate_percentage_change, adjust_precision, safe_divide
)
from ..data.data_manager import DataManager
from .strategy_manager import StrategyManager
from .position_manager import PositionManager


@dataclass
class GridState:
    """Grid trading state data."""
    base_price: float = 0.0
    current_price: float = 0.0
    grid_size: float = 2.0
    upper_band: float = 0.0
    lower_band: float = 0.0
    last_adjustment_time: float = 0.0
    volatility: float = 0.0
    price_history: List[float] = None
    
    def __post_init__(self):
        if self.price_history is None:
            self.price_history = []


class GridEngine:
    """Main grid trading engine."""
    
    def __init__(
        self,
        settings: Settings,
        exchange: BaseExchange,
        notifier: Optional[BaseNotifier] = None
    ):
        """Initialize grid trading engine."""
        self.settings = settings
        self.exchange = exchange
        self.notifier = notifier
        self.logger = get_logger("GridEngine")
        
        # Core components
        self.data_manager = DataManager(settings)
        self.strategy_manager = StrategyManager(settings, exchange, notifier)
        self.position_manager = PositionManager(settings, exchange, notifier)
        
        # Grid state
        self.grid_state = GridState()
        self.symbol = settings.trading.symbol
        self.is_running = False
        self.start_time = time.time()
        
        # Trading state
        self.active_orders = {}  # Dict[price_level: order_info]
        self.grid_levels = {}    # Dict[price_level: {'side': 'buy'/'sell', 'occupied': bool}]
        self.last_trade_time = 0
        self.last_trade_price = 0.0
        self.trade_count = 0
        self.last_failed_attempts = {}  # Dict[price_level: timestamp]
        self.failed_order_cooldown = 300  # 5 minutes cooldown after failed order
        
        # Performance tracking
        self.total_profit = 0.0
        self.max_drawdown = 0.0
        self.peak_value = 0.0
        
        self.logger.info(f"Grid engine initialized for {self.symbol}")
    
    async def initialize(self) -> bool:
        """Initialize the grid trading engine."""
        try:
            self.logger.info("Initializing grid trading engine...")
            
            # Initialize exchange
            if not await self.exchange.initialize():
                raise Exception("Failed to initialize exchange")
            
            # Initialize components
            await self.data_manager.initialize()
            await self.strategy_manager.initialize()
            await self.position_manager.initialize()
            
            # Load saved state
            await self._load_state()
            
            # Initialize grid parameters
            await self._initialize_grid()
            
            # Test notifications
            if self.notifier:
                await self.notifier.notify_system_status(
                    "INITIALIZED",
                    f"Grid engine ready for {self.symbol}",
                    self._get_uptime()
                )
            
            self.logger.info("Grid engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize grid engine: {str(e)}")
            return False
    
    async def start(self) -> None:
        """Start the grid trading engine."""
        if self.is_running:
            self.logger.warning("Grid engine is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting grid trading engine...")
        
        if self.notifier:
            await self.notifier.notify_system_status(
                "RUNNING",
                f"Grid trading started for {self.symbol}",
                self._get_uptime()
            )
        
        try:
            await self._main_loop()
        except Exception as e:
            self.logger.error(f"Grid engine error: {str(e)}")
            await self._handle_error(e)
        finally:
            self.is_running = False
    
    async def stop(self) -> None:
        """Stop the grid trading engine."""
        self.logger.info("Stopping grid trading engine...")
        self.is_running = False
        
        # Cancel all open orders
        await self._cancel_all_orders()
        
        # Save state
        await self._save_state()
        
        # Close components
        await self.strategy_manager.close()
        await self.position_manager.close()
        await self.data_manager.close()
        
        if self.notifier:
            await self.notifier.notify_system_status(
                "STOPPED",
                f"Grid trading stopped for {self.symbol}",
                self._get_uptime()
            )
        
        self.logger.info("Grid engine stopped")
    
    async def _main_loop(self) -> None:
        """Main trading loop."""
        while self.is_running:
            try:
                # Update market data
                await self._update_market_data()
                
                # Update grid state
                await self._update_grid_state()
                
                # Execute strategies (TEMPORARILY DISABLED FOR TESTING)
                # await self.strategy_manager.execute_strategies(self.grid_state)
                
                # Check and execute grid orders
                await self._check_grid_signals()
                
                # Update position management
                await self.position_manager.update_positions()
                
                # Save state periodically
                if time.time() - self.data_manager.last_save_time > self.settings.data.save_interval:
                    await self._save_state()
                
                # Sleep before next iteration
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(30)  # Longer sleep on error
    
    async def _update_market_data(self) -> None:
        """Update market data and price history."""
        try:
            # Get current price
            ticker = await self.exchange.get_ticker(self.symbol)
            current_price = float(ticker['last'])
            
            # Update grid state
            self.grid_state.current_price = current_price
            
            # Update price history
            self.grid_state.price_history.append(current_price)
            
            # Keep only recent prices (24 hours worth)
            max_history = 24 * 12  # 5-minute intervals for 24 hours
            if len(self.grid_state.price_history) > max_history:
                self.grid_state.price_history = self.grid_state.price_history[-max_history:]
            
            # Calculate volatility
            if len(self.grid_state.price_history) >= 2:
                self.grid_state.volatility = calculate_volatility(
                    self.grid_state.price_history,
                    window=min(len(self.grid_state.price_history), 24)
                )
            
        except Exception as e:
            self.logger.error(f"Failed to update market data: {str(e)}")
            raise
    
    async def _update_grid_state(self) -> None:
        """Update grid state and bands."""
        try:
            # Set base price if not set
            if self.grid_state.base_price == 0:
                self.grid_state.base_price = self.grid_state.current_price
                self.logger.info(f"Base price set to {self.grid_state.base_price:.4f}")
            
            # Adjust grid size based on volatility
            if self.settings.grid.dynamic_adjustment:
                await self._adjust_grid_size()
            
            # Calculate grid bands
            self._calculate_grid_bands()

            # Initialize grid levels only once or when base price changes significantly
            self._initialize_grid_levels()

        except Exception as e:
            self.logger.error(f"Failed to update grid state: {str(e)}")
            raise
    
    async def _adjust_grid_size(self) -> None:
        """Adjust grid size based on market volatility."""
        try:
            current_time = time.time()
            adjustment_interval = self._get_adjustment_interval()
            
            if current_time - self.grid_state.last_adjustment_time < adjustment_interval:
                return
            
            # Find appropriate grid size based on volatility
            new_grid_size = self._get_grid_size_for_volatility(self.grid_state.volatility)
            
            if abs(new_grid_size - self.grid_state.grid_size) > 0.1:
                old_size = self.grid_state.grid_size
                self.grid_state.grid_size = new_grid_size
                self.grid_state.last_adjustment_time = current_time
                
                self.logger.info(
                    f"Grid size adjusted: {old_size:.1f}% → {new_grid_size:.1f}% "
                    f"(volatility: {self.grid_state.volatility:.2%})"
                )
                
                if self.notifier:
                    await self.notifier.notify_strategy_signal(
                        "GRID",
                        "ADJUSTMENT",
                        self.grid_state.current_price,
                        f"Grid size: {old_size:.1f}% → {new_grid_size:.1f}%"
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to adjust grid size: {str(e)}")
    
    def _get_grid_size_for_volatility(self, volatility: float) -> float:
        """Get appropriate grid size based on volatility."""
        for threshold in self.settings.grid.volatility_thresholds:
            vol_range = threshold['range']
            if vol_range[0] <= volatility < vol_range[1]:
                return threshold['grid_size']
        
        # Default to max grid size for very high volatility
        return self.settings.grid.max_size
    
    def _get_adjustment_interval(self) -> float:
        """Get grid adjustment interval based on volatility."""
        base_interval = 3600  # 1 hour
        
        if self.grid_state.volatility > 0.8:
            return base_interval * 0.25  # 15 minutes
        elif self.grid_state.volatility > 0.4:
            return base_interval * 0.5   # 30 minutes
        elif self.grid_state.volatility > 0.2:
            return base_interval * 0.75  # 45 minutes
        else:
            return base_interval         # 1 hour
    
    def _calculate_grid_bands(self) -> None:
        """Calculate grid upper and lower bands."""
        grid_decimal = self.grid_state.grid_size / 100

        self.grid_state.upper_band = self.grid_state.base_price * (1 + grid_decimal)
        self.grid_state.lower_band = self.grid_state.base_price * (1 - grid_decimal)

        # Calculate multiple grid levels for debug output
        # Always log in debug mode since config is set to DEBUG
        self._log_grid_levels()

    def _initialize_grid_levels(self) -> None:
        """Initialize multiple grid levels."""
        # Only clear if grid levels are empty (first time initialization)
        if not self.grid_levels:
            base_price = self.grid_state.base_price
            grid_decimal = self.grid_state.grid_size / 100

            # Create 5 buy levels below base price and 5 sell levels above
            for i in range(-5, 6):
                if i == 0:
                    continue  # Skip base price level

                level_price = base_price * (1 + (i * grid_decimal))
                level_price = round(level_price, 4)  # Round to 4 decimal places

                self.grid_levels[level_price] = {
                    'side': 'buy' if i < 0 else 'sell',
                    'level': i,
                    'occupied': False,
                    'last_attempt': 0
                }

            self.logger.info(f"Initialized {len(self.grid_levels)} grid levels")
        else:
            # Grid levels already exist, just update prices if needed
            self._update_existing_grid_levels()

    def _update_existing_grid_levels(self) -> None:
        """Update existing grid levels with new prices if base price changed."""
        base_price = self.grid_state.base_price
        grid_decimal = self.grid_state.grid_size / 100

        # Check if we need to update prices (base price changed significantly)
        if len(self.grid_levels) > 0:
            first_level = list(self.grid_levels.keys())[0]
            expected_price = base_price * (1 + (-5 * grid_decimal))
            expected_price = round(expected_price, 4)

            # If prices are significantly different, recreate grid levels
            if abs(first_level - expected_price) > 1.0:
                self.logger.info("Base price changed significantly, recreating grid levels")
                self.grid_levels.clear()
                self._initialize_grid_levels()
    
    async def _check_grid_signals(self) -> None:
        """Check for grid trading signals and execute orders."""
        try:
            current_price = self.grid_state.current_price
            current_time = time.time()

            # Debug: Log grid levels status
            occupied_levels = [f"{price:.4f}" for price, info in self.grid_levels.items() if info['occupied']]
            if occupied_levels:
                self.logger.debug(f"Occupied grid levels: {', '.join(occupied_levels)}")

            # Check each grid level for trading opportunities
            for price_level, level_info in self.grid_levels.items():
                # Skip if level is already occupied by an active order
                if level_info['occupied']:
                    self.logger.debug(f"Skipping occupied level {price_level:.4f}")
                    continue

                # Skip if recently failed (cooldown period)
                if current_time - level_info['last_attempt'] < self.failed_order_cooldown:
                    remaining_cooldown = self.failed_order_cooldown - (current_time - level_info['last_attempt'])
                    self.logger.debug(f"Skipping level {price_level:.4f} - cooldown {remaining_cooldown:.0f}s remaining")
                    continue

                side = level_info['side']

                # CORRECT grid logic: only place orders when they make sense
                # Buy orders: ONLY when order price is BELOW current price (discount buying)
                # Sell orders: ONLY when order price is ABOVE current price (profit taking)

                if side == 'buy':
                    # Buy order: only if grid level is at least 0.1% below current price
                    if price_level < current_price * 0.999:
                        self.logger.debug(f"Placing buy order at {price_level:.4f} (current: {current_price:.4f}, discount: {((current_price - price_level) / current_price * 100):.2f}%)")
                        await self._execute_grid_order(price_level, 'buy')
                    else:
                        self.logger.debug(f"Skipping buy level {price_level:.4f} - too close to current price {current_price:.4f}")

                elif side == 'sell':
                    # Sell order: only if grid level is at least 0.1% above current price
                    if price_level > current_price * 1.001:
                        self.logger.debug(f"Placing sell order at {price_level:.4f} (current: {current_price:.4f}, premium: {((price_level - current_price) / current_price * 100):.2f}%)")
                        await self._execute_grid_order(price_level, 'sell')
                    else:
                        self.logger.debug(f"Skipping sell level {price_level:.4f} - too close to current price {current_price:.4f}")

            # Check order status
            await self._check_order_status()

        except Exception as e:
            self.logger.error(f"Failed to check grid signals: {str(e)}")
    
    async def _execute_grid_order(self, price_level: float, side: str) -> None:
        """Execute grid order at specific price level."""
        try:
            # Calculate order amount
            amount = await self._calculate_order_amount(side, price_level)
            if amount <= 0:
                self.logger.warning(f"Insufficient balance for {side} order at {price_level:.4f}")
                return

            # Create order
            order = await self.exchange.create_limit_order(
                symbol=self.symbol,
                side=side,
                amount=amount,
                price=price_level
            )

            # Mark this level as occupied
            self.grid_levels[price_level]['occupied'] = True
            self.active_orders[price_level] = order

            self.logger.info(
                f"Grid {side} order placed: {amount:.6f} @ {price_level:.4f} "
                f"(Level {self.grid_levels[price_level]['level']:+d})"
            )

            if self.notifier:
                await self.notifier.notify_trade_execution(
                    side, self.symbol, price_level, amount,
                    amount * price_level, 'GRID'
                )

        except Exception as e:
            self.logger.error(f"Failed to execute grid {side} at {price_level:.4f}: {str(e)}")
            # Record failed attempt time to prevent immediate retry
            self.grid_levels[price_level]['last_attempt'] = time.time()
    

    
    async def _calculate_order_amount(self, side: str, price: float = None) -> float:
        """Calculate order amount based on available balance and settings."""
        try:
            balance = await self.exchange.get_balance()

            # Use provided price or fallback to current price
            order_price = price if price is not None else self.grid_state.current_price

            if side == 'buy':
                # Use USDT balance for buying
                available = float(balance['free'].get('USDT', 0))
                max_amount = available * 0.1  # Use only 10% of available balance per order

                # Calculate amount based on price
                amount_usdt = min(max_amount, self.settings.trading.min_trade_amount)
                amount = amount_usdt / order_price

            else:  # sell
                # Use base asset balance for selling
                symbol_info = self.exchange.get_symbol_info(self.symbol)
                base_asset = symbol_info.get('base', self.symbol.split('/')[0])
                available = float(balance['free'].get(base_asset, 0))
                amount = available * 0.1  # Sell 10% of available per order

            # Adjust for precision
            amount = self.exchange.adjust_amount_precision(self.symbol, amount)

            # Check minimum trade amount
            min_notional = self.settings.trading.min_trade_amount
            if amount * order_price < min_notional:
                return 0.0

            return amount
            
        except Exception as e:
            self.logger.error(f"Failed to calculate order amount: {str(e)}")
            return 0.0

    async def _check_order_status(self) -> None:
        """Check status of active orders."""
        try:
            for price_level, order in list(self.active_orders.items()):
                if order is None:
                    continue

                # Get order status
                status = await self.exchange.get_order_status(order['id'], self.symbol)

                if status['status'] == 'closed':
                    # Order filled
                    await self._handle_order_filled(price_level, status)

                elif status['status'] == 'canceled':
                    # Order canceled
                    self.logger.info(f"Grid order canceled at {price_level:.4f}: {order['id']}")
                    self._release_grid_level(price_level)

        except Exception as e:
            self.logger.error(f"Failed to check order status: {str(e)}")

    def _release_grid_level(self, price_level: float) -> None:
        """Release a grid level (mark as unoccupied)."""
        if price_level in self.grid_levels:
            self.grid_levels[price_level]['occupied'] = False
            self.logger.debug(f"Released grid level {price_level:.4f}")
        if price_level in self.active_orders:
            del self.active_orders[price_level]
            self.logger.debug(f"Removed active order for level {price_level:.4f}")

    async def _handle_order_filled(self, price_level: float, order: Dict[str, Any]) -> None:
        """Handle filled order."""
        try:
            price = float(order['price'])
            amount = float(order['filled'])
            total = price * amount

            # Get side from grid level info
            side = self.grid_levels[price_level]['side']
            level = self.grid_levels[price_level]['level']

            # Update trade statistics
            self.trade_count += 1
            self.last_trade_time = time.time()
            self.last_trade_price = price

            # Calculate profit (simplified)
            if side == 'sell':
                profit = (price - self.grid_state.base_price) * amount
                self.total_profit += profit
            else:
                profit = 0  # Buy orders don't generate immediate profit

            # Log trade
            self.logger.info(
                f"Grid {side} order filled: {amount:.6f} @ {price:.4f} "
                f"(Level {level:+d}, Total: {total:.2f} USDT, Profit: {profit:+.2f} USDT)"
            )

            # Save trade data
            await self.data_manager.save_trade({
                'timestamp': time.time(),
                'side': side,
                'symbol': self.symbol,
                'price': price,
                'amount': amount,
                'total': total,
                'profit': profit,
                'strategy': 'GRID',
                'order_id': order['id'],
                'grid_level': level
            })

            # Send notification
            if self.notifier:
                await self.notifier.notify_trade_execution(
                    side, self.symbol, price, amount, total, 'GRID', profit
                )

            # Release this grid level
            self._release_grid_level(price_level)

        except Exception as e:
            self.logger.error(f"Failed to handle filled order: {str(e)}")

    async def _cancel_all_orders(self) -> None:
        """Cancel all active orders."""
        try:
            for price_level, order in list(self.active_orders.items()):
                if order is not None:
                    await self.exchange.cancel_order(order['id'], self.symbol)
                    self._release_grid_level(price_level)
                    self.logger.info(f"Canceled order at {price_level:.4f}: {order['id']}")

        except Exception as e:
            self.logger.error(f"Failed to cancel orders: {str(e)}")

    async def _initialize_grid(self) -> None:
        """Initialize grid parameters."""
        try:
            # Set initial grid size
            self.grid_state.grid_size = self.settings.grid.initial_size

            # Set base price from settings or current price
            if self.settings.initial_base_price > 0:
                self.grid_state.base_price = self.settings.initial_base_price
            else:
                ticker = await self.exchange.get_ticker(self.symbol)
                self.grid_state.base_price = float(ticker['last'])

            self.logger.info(
                f"Grid initialized: base_price={self.grid_state.base_price:.4f}, "
                f"grid_size={self.grid_state.grid_size:.1f}%"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize grid: {str(e)}")
            raise

    async def _load_state(self) -> None:
        """Load saved trading state."""
        try:
            state = await self.data_manager.load_state()
            if state:
                # Load state but allow config to override base_price if explicitly set
                saved_base_price = state.get('base_price', 0)

                # Check if user has explicitly set a new base price in config
                if self.settings.initial_base_price > 0:
                    # If config base price differs from saved state, use config (user wants to change it)
                    if abs(self.settings.initial_base_price - saved_base_price) > 1.0:  # Allow small differences
                        self.grid_state.base_price = self.settings.initial_base_price
                        self.logger.info(f"Using new base price from config: {self.grid_state.base_price:.4f} "
                                       f"(was {saved_base_price:.4f} in saved state)")
                    else:
                        self.grid_state.base_price = saved_base_price
                        self.logger.info(f"Using saved base price: {self.grid_state.base_price:.4f}")
                else:
                    # No explicit config, use saved state
                    self.grid_state.base_price = saved_base_price
                    self.logger.info(f"Using saved base price: {self.grid_state.base_price:.4f}")

                # Load other state data
                self.grid_state.grid_size = state.get('grid_size', self.settings.grid.initial_size)
                self.grid_state.last_adjustment_time = state.get('last_adjustment_time', 0)
                self.total_profit = state.get('total_profit', 0)
                self.trade_count = state.get('trade_count', 0)

                self.logger.info("Trading state loaded from file")

        except Exception as e:
            self.logger.error(f"Failed to load state: {str(e)}")

    async def _save_state(self) -> None:
        """Save current trading state."""
        try:
            state = {
                'base_price': self.grid_state.base_price,
                'current_price': self.grid_state.current_price,
                'grid_size': self.grid_state.grid_size,
                'last_adjustment_time': self.grid_state.last_adjustment_time,
                'volatility': self.grid_state.volatility,
                'total_profit': self.total_profit,
                'trade_count': self.trade_count,
                'last_save_time': time.time()
            }

            await self.data_manager.save_state(state)

        except Exception as e:
            self.logger.error(f"Failed to save state: {str(e)}")

    async def _handle_error(self, error: Exception) -> None:
        """Handle trading errors."""
        self.logger.error(f"Trading error: {str(error)}")

        if self.notifier:
            await self.notifier.notify_error(
                "TRADING_ERROR",
                str(error),
                f"Symbol: {self.symbol}"
            )

        # Cancel orders on critical errors
        await self._cancel_all_orders()

    def _get_uptime(self) -> str:
        """Get system uptime."""
        uptime_seconds = int(time.time() - self.start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        return {
            'is_running': self.is_running,
            'symbol': self.symbol,
            'base_price': self.grid_state.base_price,
            'current_price': self.grid_state.current_price,
            'grid_size': self.grid_state.grid_size,
            'upper_band': self.grid_state.upper_band,
            'lower_band': self.grid_state.lower_band,
            'volatility': self.grid_state.volatility,
            'total_profit': self.total_profit,
            'trade_count': self.trade_count,
            'uptime': self._get_uptime(),
            'active_orders': {
                f"{price_level:.4f}": order['id'] if order else None
                for price_level, order in self.active_orders.items()
            },
            'grid_levels_occupied': sum(1 for level in self.grid_levels.values() if level['occupied'])
        }

    def _log_grid_levels(self) -> None:
        """Log detailed grid levels for debugging."""
        try:
            base_price = self.grid_state.base_price
            current_price = self.grid_state.current_price
            grid_size = self.grid_state.grid_size

            # Calculate multiple grid levels (5 levels up and down)
            levels = []
            grid_decimal = grid_size / 100

            # Calculate grid levels
            for i in range(-5, 6):  # -5 to +5 levels
                if i == 0:
                    level_price = base_price
                    level_type = "BASE"
                else:
                    level_price = base_price * (1 + (i * grid_decimal))
                    level_type = "SELL" if i > 0 else "BUY"

                # Calculate distance from current price
                distance_pct = ((level_price - current_price) / current_price) * 100

                levels.append({
                    'level': i,
                    'type': level_type,
                    'price': level_price,
                    'distance_pct': distance_pct
                })

            # Log grid information
            self.logger.debug("=" * 80)
            self.logger.debug(f"GRID DEBUG INFO - {self.symbol}")
            self.logger.debug("=" * 80)
            self.logger.debug(f"Base Price:    {base_price:.4f} USDT")
            self.logger.debug(f"Current Price: {current_price:.4f} USDT")
            self.logger.debug(f"Grid Size:     {grid_size:.2f}%")
            self.logger.debug(f"Upper Band:    {self.grid_state.upper_band:.4f} USDT")
            self.logger.debug(f"Lower Band:    {self.grid_state.lower_band:.4f} USDT")
            self.logger.debug("-" * 80)
            self.logger.debug("GRID LEVELS:")
            self.logger.debug("-" * 80)

            for level in levels:
                status = ""
                if level['type'] == 'BASE':
                    status = " ← BASE"
                elif abs(level['distance_pct']) < 0.1:
                    status = " ← CURRENT"
                elif level['type'] == 'BUY' and level['distance_pct'] < 0:
                    status = " ← BUY ZONE"
                elif level['type'] == 'SELL' and level['distance_pct'] > 0:
                    status = " ← SELL ZONE"

                self.logger.debug(
                    f"Level {level['level']:+2d} | {level['type']:4s} | "
                    f"{level['price']:10.4f} USDT | "
                    f"{level['distance_pct']:+6.2f}%{status}"
                )

            self.logger.debug("=" * 80)

        except Exception as e:
            self.logger.error(f"Failed to log grid levels: {str(e)}")
