"""
Notification system for GridTrading Pro.

This module provides unified notification interfaces for different platforms,
currently supporting Telegram notifications for trade alerts, risk warnings,
and system status updates.
"""

from .base_notifier import BaseNotifier
from .telegram_notifier import TelegramNotifier

__all__ = [
    "BaseNotifier",
    "TelegramNotifier",
]


def create_notifier(platform: str, **kwargs) -> BaseNotifier:
    """Factory function to create notifier instance based on platform."""
    if platform.lower() == "telegram":
        return TelegramNotifier(**kwargs)
    else:
        raise ValueError(f"Unsupported notification platform: {platform}")
