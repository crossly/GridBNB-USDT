"""
Base notifier class for GridTrading Pro.

This module defines the abstract base class for all notification implementations,
providing a unified interface for sending different types of notifications.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import time

from ..utils.logger import get_logger
from ..config.constants import NotificationLevel


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class BaseNotifier(ABC):
    """Abstract base class for notification implementations."""
    
    def __init__(
        self,
        enabled: bool = True,
        notification_levels: List[str] = None,
        rate_limit: int = 10,  # Max notifications per minute
        **kwargs
    ):
        """Initialize base notifier."""
        self.enabled = enabled
        self.notification_levels = notification_levels or ["trade", "risk", "system", "error"]
        self.rate_limit = rate_limit
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # Rate limiting
        self.notification_history = []
        self.rate_limit_window = 60  # 1 minute
        
        # Message queue for batch sending
        self.message_queue = []
        self.batch_size = 5
        self.batch_timeout = 30  # seconds
        
    @abstractmethod
    async def send_message(
        self,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> bool:
        """Send a notification message."""
        pass
    
    @abstractmethod
    async def send_formatted_message(
        self,
        title: str,
        content: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> bool:
        """Send a formatted notification message."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self.enabled
    
    def should_notify(self, level: str) -> bool:
        """Check if notification level is enabled."""
        return self.enabled and level.lower() in [l.lower() for l in self.notification_levels]
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limit allows sending notification."""
        current_time = time.time()
        
        # Remove old notifications outside the window
        self.notification_history = [
            timestamp for timestamp in self.notification_history
            if current_time - timestamp < self.rate_limit_window
        ]
        
        # Check if we're under the rate limit
        if len(self.notification_history) >= self.rate_limit:
            self.logger.warning(f"Rate limit exceeded: {len(self.notification_history)}/{self.rate_limit}")
            return False
        
        # Add current notification to history
        self.notification_history.append(current_time)
        return True
    
    async def notify_trade_execution(
        self,
        side: str,
        symbol: str,
        price: float,
        amount: float,
        total: float,
        strategy: str = "GRID",
        profit: float = 0.0
    ) -> bool:
        """Send trade execution notification."""
        if not self.should_notify("trade"):
            return False
        
        emoji = "🟢" if side.upper() == "BUY" else "🔴"
        profit_text = f"\n💰 Profit: {profit:+.2f} USDT" if profit != 0 else ""
        
        message = (
            f"{emoji} {strategy} {side.upper()} {symbol}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 Price: {price:.4f} USDT\n"
            f"📊 Amount: {amount:.6f}\n"
            f"💸 Total: {total:.2f} USDT{profit_text}\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}"
        )
        
        return await self.send_message(message, NotificationPriority.NORMAL)
    
    async def notify_risk_alert(
        self,
        alert_type: str,
        current_value: float,
        threshold: float,
        action: str = "MONITOR"
    ) -> bool:
        """Send risk management alert."""
        if not self.should_notify("risk"):
            return False
        
        priority = NotificationPriority.HIGH if action != "MONITOR" else NotificationPriority.NORMAL
        
        message = (
            f"⚠️ RISK ALERT\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 Type: {alert_type}\n"
            f"📊 Current: {current_value:.4f}\n"
            f"🎯 Threshold: {threshold:.4f}\n"
            f"🎬 Action: {action}\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}"
        )
        
        return await self.send_message(message, priority)
    
    async def notify_system_status(
        self,
        status: str,
        details: str = "",
        uptime: str = ""
    ) -> bool:
        """Send system status notification."""
        if not self.should_notify("system"):
            return False
        
        emoji = "🟢" if status == "RUNNING" else "🔴" if status == "ERROR" else "🟡"
        uptime_text = f"\n⏱️ Uptime: {uptime}" if uptime else ""
        
        message = (
            f"{emoji} SYSTEM {status}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 Details: {details}{uptime_text}\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}"
        )
        
        priority = NotificationPriority.CRITICAL if status == "ERROR" else NotificationPriority.NORMAL
        return await self.send_message(message, priority)
    
    async def notify_strategy_signal(
        self,
        strategy: str,
        signal: str,
        price: float,
        reason: str = ""
    ) -> bool:
        """Send strategy signal notification."""
        if not self.should_notify("trade"):
            return False
        
        message = (
            f"📊 STRATEGY SIGNAL\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Strategy: {strategy.upper()}\n"
            f"📈 Signal: {signal.upper()}\n"
            f"💵 Price: {price:.4f}\n"
            f"💭 Reason: {reason}\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}"
        )
        
        return await self.send_message(message, NotificationPriority.NORMAL)
    
    async def notify_error(
        self,
        error_type: str,
        error_message: str,
        context: str = ""
    ) -> bool:
        """Send error notification."""
        if not self.should_notify("error"):
            return False
        
        context_text = f"\n🔍 Context: {context}" if context else ""
        
        message = (
            f"🚨 ERROR ALERT\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ Type: {error_type}\n"
            f"📝 Message: {error_message}{context_text}\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}"
        )
        
        return await self.send_message(message, NotificationPriority.CRITICAL)
    
    async def notify_position_update(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        current_price: float,
        pnl: float
    ) -> bool:
        """Send position update notification."""
        if not self.should_notify("trade"):
            return False
        
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        pnl_color = "🟢" if pnl >= 0 else "🔴"
        
        message = (
            f"📊 POSITION UPDATE\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Symbol: {symbol}\n"
            f"📍 Side: {side.upper()}\n"
            f"📊 Size: {size:.6f}\n"
            f"💵 Entry: {entry_price:.4f}\n"
            f"💰 Current: {current_price:.4f}\n"
            f"{pnl_emoji} PnL: {pnl_color} {pnl:+.2f} USDT\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}"
        )
        
        return await self.send_message(message, NotificationPriority.NORMAL)
    
    async def send_batch_notifications(self) -> bool:
        """Send queued notifications in batch."""
        if not self.message_queue:
            return True
        
        try:
            # Combine messages
            combined_message = "\n\n".join(self.message_queue)
            success = await self.send_message(combined_message, NotificationPriority.NORMAL)
            
            if success:
                self.message_queue.clear()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send batch notifications: {str(e)}")
            return False
    
    def queue_message(self, message: str):
        """Add message to queue for batch sending."""
        self.message_queue.append(message)
        
        if len(self.message_queue) >= self.batch_size:
            # Schedule immediate batch send
            asyncio.create_task(self.send_batch_notifications())
    
    async def close(self):
        """Close notifier and send any remaining queued messages."""
        if self.message_queue:
            await self.send_batch_notifications()
        
        self.logger.info("Notifier closed")
