"""
Risk manager for GridTrading Pro.

This module implements comprehensive risk management including position limits,
drawdown protection, daily loss limits, and emergency stop mechanisms.
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..config.settings import Settings
from ..exchanges.base_exchange import BaseExchange
from ..notifications.base_notifier import BaseNotifier
from ..utils.logger import get_logger
from ..utils.helpers import safe_divide


@dataclass
class RiskAlert:
    """Risk alert data structure."""
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    current_value: float
    threshold: float
    timestamp: float
    action_required: bool = False


class RiskManager:
    """Comprehensive risk management system."""
    
    def __init__(
        self,
        settings: Settings,
        exchange: BaseExchange,
        notifier: Optional[BaseNotifier] = None
    ):
        """Initialize risk manager."""
        self.settings = settings
        self.exchange = exchange
        self.notifier = notifier
        self.logger = get_logger("RiskManager")
        
        # Risk tracking
        self.active_alerts: List[RiskAlert] = []
        self.risk_history: List[RiskAlert] = []
        self.emergency_stop_triggered = False
        
        # Performance tracking
        self.peak_portfolio_value = 0
        self.current_drawdown = 0
        self.daily_start_value = 0
        self.daily_pnl = 0
        self.last_daily_reset = 0
        
        # Check intervals
        self.last_risk_check = 0
        self.risk_check_interval = settings.risk.risk_check_interval
        
        # Position tracking
        self.current_position_ratio = 0
        self.last_position_check = 0
    
    async def initialize(self) -> bool:
        """Initialize risk manager."""
        try:
            self.logger.info("Initializing risk manager...")
            
            # Get initial portfolio value
            account_value = await self.exchange.get_account_value()
            self.peak_portfolio_value = account_value
            self.daily_start_value = account_value
            self.last_daily_reset = time.time()
            
            self.logger.info(f"Risk manager initialized - Initial value: {account_value:.2f} USDT")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize risk manager: {str(e)}")
            return False
    
    async def check_all_risks(self) -> List[RiskAlert]:
        """Perform comprehensive risk check."""
        current_time = time.time()
        
        # Check if risk check is needed
        if current_time - self.last_risk_check < self.risk_check_interval:
            return []
        
        alerts = []
        
        try:
            # Update portfolio metrics
            await self._update_portfolio_metrics()
            
            # Check position limits
            position_alerts = await self._check_position_limits()
            alerts.extend(position_alerts)
            
            # Check drawdown limits
            drawdown_alerts = await self._check_drawdown_limits()
            alerts.extend(drawdown_alerts)
            
            # Check daily loss limits
            daily_alerts = await self._check_daily_limits()
            alerts.extend(daily_alerts)
            
            # Check emergency conditions
            emergency_alerts = await self._check_emergency_conditions()
            alerts.extend(emergency_alerts)
            
            # Process alerts
            await self._process_alerts(alerts)
            
            self.last_risk_check = current_time
            
        except Exception as e:
            self.logger.error(f"Risk check failed: {str(e)}")
            
            # Create error alert
            error_alert = RiskAlert(
                alert_type="SYSTEM_ERROR",
                severity="high",
                message=f"Risk check failed: {str(e)}",
                current_value=0,
                threshold=0,
                timestamp=current_time,
                action_required=True
            )
            alerts.append(error_alert)
        
        return alerts
    
    async def _update_portfolio_metrics(self) -> None:
        """Update portfolio performance metrics."""
        try:
            current_value = await self.exchange.get_account_value()
            
            # Update peak value and drawdown
            if current_value > self.peak_portfolio_value:
                self.peak_portfolio_value = current_value
            
            # Calculate current drawdown
            if self.peak_portfolio_value > 0:
                self.current_drawdown = (current_value - self.peak_portfolio_value) / self.peak_portfolio_value
            
            # Update daily PnL
            if self.daily_start_value > 0:
                self.daily_pnl = (current_value - self.daily_start_value) / self.daily_start_value
            
            # Check for daily reset
            if time.time() - self.last_daily_reset > 86400:  # 24 hours
                self.daily_start_value = current_value
                self.daily_pnl = 0
                self.last_daily_reset = time.time()
                self.logger.info("Daily metrics reset")
            
        except Exception as e:
            self.logger.error(f"Failed to update portfolio metrics: {str(e)}")
            raise
    
    async def _check_position_limits(self) -> List[RiskAlert]:
        """Check position ratio limits."""
        alerts = []
        
        try:
            # Get current position ratio
            balance = await self.exchange.get_balance()
            symbol = self.settings.trading.symbol
            
            if self.exchange.is_futures_mode():
                # Futures position
                position = await self.exchange.get_position(symbol)
                position_value = abs(float(position.get('notional', 0)))
                total_balance = float(balance.get('total', {}).get('USDT', 0))
            else:
                # Spot position
                base_asset = symbol.split('/')[0]
                base_balance = float(balance.get('total', {}).get(base_asset, 0))
                usdt_balance = float(balance.get('total', {}).get('USDT', 0))
                
                ticker = await self.exchange.get_ticker(symbol)
                current_price = float(ticker['last'])
                
                position_value = base_balance * current_price
                total_balance = position_value + usdt_balance
            
            self.current_position_ratio = safe_divide(position_value, total_balance)
            
            # Check maximum position ratio
            if self.current_position_ratio > self.settings.risk.max_position_ratio:
                alerts.append(RiskAlert(
                    alert_type="POSITION_LIMIT_EXCEEDED",
                    severity="high",
                    message=f"Position ratio {self.current_position_ratio:.2%} exceeds maximum {self.settings.risk.max_position_ratio:.2%}",
                    current_value=self.current_position_ratio,
                    threshold=self.settings.risk.max_position_ratio,
                    timestamp=time.time(),
                    action_required=True
                ))
            
            # Check minimum position ratio
            if self.current_position_ratio < self.settings.risk.min_position_ratio:
                alerts.append(RiskAlert(
                    alert_type="POSITION_BELOW_MINIMUM",
                    severity="medium",
                    message=f"Position ratio {self.current_position_ratio:.2%} below minimum {self.settings.risk.min_position_ratio:.2%}",
                    current_value=self.current_position_ratio,
                    threshold=self.settings.risk.min_position_ratio,
                    timestamp=time.time(),
                    action_required=False
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to check position limits: {str(e)}")
        
        return alerts
    
    async def _check_drawdown_limits(self) -> List[RiskAlert]:
        """Check drawdown limits."""
        alerts = []
        
        try:
            # Check maximum drawdown
            if self.current_drawdown < self.settings.risk.max_drawdown:
                severity = "critical" if self.current_drawdown < self.settings.risk.max_drawdown * 1.5 else "high"
                
                alerts.append(RiskAlert(
                    alert_type="MAX_DRAWDOWN_EXCEEDED",
                    severity=severity,
                    message=f"Drawdown {self.current_drawdown:.2%} exceeds limit {self.settings.risk.max_drawdown:.2%}",
                    current_value=self.current_drawdown,
                    threshold=self.settings.risk.max_drawdown,
                    timestamp=time.time(),
                    action_required=True
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to check drawdown limits: {str(e)}")
        
        return alerts
    
    async def _check_daily_limits(self) -> List[RiskAlert]:
        """Check daily loss limits."""
        alerts = []
        
        try:
            # Check daily loss limit
            if self.daily_pnl < self.settings.risk.daily_loss_limit:
                severity = "critical" if self.daily_pnl < self.settings.risk.daily_loss_limit * 1.5 else "high"
                
                alerts.append(RiskAlert(
                    alert_type="DAILY_LOSS_LIMIT_EXCEEDED",
                    severity=severity,
                    message=f"Daily PnL {self.daily_pnl:.2%} exceeds loss limit {self.settings.risk.daily_loss_limit:.2%}",
                    current_value=self.daily_pnl,
                    threshold=self.settings.risk.daily_loss_limit,
                    timestamp=time.time(),
                    action_required=True
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to check daily limits: {str(e)}")
        
        return alerts
    
    async def _check_emergency_conditions(self) -> List[RiskAlert]:
        """Check for emergency stop conditions."""
        alerts = []
        
        try:
            # Check for extreme conditions that require immediate action
            emergency_conditions = [
                (self.current_drawdown < self.settings.risk.max_drawdown * 2, "EXTREME_DRAWDOWN"),
                (self.daily_pnl < self.settings.risk.daily_loss_limit * 2, "EXTREME_DAILY_LOSS"),
                (self.current_position_ratio > 0.95, "EXTREME_POSITION_RATIO")
            ]
            
            for condition, alert_type in emergency_conditions:
                if condition:
                    alerts.append(RiskAlert(
                        alert_type=alert_type,
                        severity="critical",
                        message=f"Emergency condition detected: {alert_type}",
                        current_value=0,
                        threshold=0,
                        timestamp=time.time(),
                        action_required=True
                    ))
                    
                    # Trigger emergency stop
                    if not self.emergency_stop_triggered:
                        await self._trigger_emergency_stop(alert_type)
            
        except Exception as e:
            self.logger.error(f"Failed to check emergency conditions: {str(e)}")
        
        return alerts
    
    async def _process_alerts(self, alerts: List[RiskAlert]) -> None:
        """Process and handle risk alerts."""
        for alert in alerts:
            # Add to active alerts
            self.active_alerts.append(alert)
            self.risk_history.append(alert)
            
            # Log alert
            log_method = getattr(self.logger, alert.severity if alert.severity != 'critical' else 'error')
            log_method(f"RISK ALERT: {alert.message}")
            
            # Send notification
            if self.notifier:
                await self.notifier.notify_risk_alert(
                    alert.alert_type,
                    alert.current_value,
                    alert.threshold,
                    "EMERGENCY_STOP" if alert.action_required else "MONITOR"
                )
        
        # Clean old alerts (keep last 100)
        if len(self.risk_history) > 100:
            self.risk_history = self.risk_history[-100:]
    
    async def _trigger_emergency_stop(self, reason: str) -> None:
        """Trigger emergency stop."""
        try:
            self.emergency_stop_triggered = True
            
            self.logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")
            
            # Cancel all open orders
            await self.exchange.cancel_all_orders()
            
            # Send critical notification
            if self.notifier:
                await self.notifier.notify_error(
                    "EMERGENCY_STOP",
                    f"Trading halted due to: {reason}",
                    "All orders cancelled, manual intervention required"
                )
            
        except Exception as e:
            self.logger.error(f"Failed to trigger emergency stop: {str(e)}")
    
    def is_emergency_stop_active(self) -> bool:
        """Check if emergency stop is active."""
        return self.emergency_stop_triggered
    
    def reset_emergency_stop(self) -> None:
        """Reset emergency stop (manual intervention required)."""
        self.emergency_stop_triggered = False
        self.logger.info("Emergency stop reset")
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status."""
        return {
            'emergency_stop_active': self.emergency_stop_triggered,
            'current_drawdown': self.current_drawdown,
            'daily_pnl': self.daily_pnl,
            'position_ratio': self.current_position_ratio,
            'peak_value': self.peak_portfolio_value,
            'active_alerts': len(self.active_alerts),
            'last_risk_check': self.last_risk_check
        }
    
    def get_active_alerts(self) -> List[RiskAlert]:
        """Get active risk alerts."""
        return self.active_alerts.copy()
    
    async def close(self) -> None:
        """Close risk manager."""
        self.logger.info("Risk manager closed")
