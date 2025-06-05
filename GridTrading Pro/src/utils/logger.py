"""
Logging configuration and utilities for GridTrading Pro.

This module provides centralized logging configuration with support for
file rotation, different log levels, and structured logging.
"""

import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional
from pathlib import Path

from ..config.settings import LoggingSettings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


class GridTradingLogger:
    """Custom logger class for GridTrading Pro."""
    
    def __init__(self, name: str, settings: Optional[LoggingSettings] = None):
        self.name = name
        self.settings = settings or LoggingSettings()
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with file and console handlers."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, self.settings.level))
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler with rotation
        file_handler = TimedRotatingFileHandler(
            filename=log_dir / "gridtrading.log",
            when=self.settings.file_rotation,
            interval=1,
            backupCount=self.settings.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.settings.level))
        file_formatter = logging.Formatter(
            self.settings.format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.settings.level))
        console_formatter = ColoredFormatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)


# Global logger registry
_loggers = {}


def setup_logger(settings: Optional[LoggingSettings] = None) -> None:
    """Setup global logging configuration."""
    global _loggers
    
    # Setup root logger
    root_logger = GridTradingLogger("GridTradingPro", settings)
    _loggers["root"] = root_logger
    
    # Disable other loggers to reduce noise
    logging.getLogger("ccxt").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


def get_logger(name: str = "GridTradingPro") -> GridTradingLogger:
    """Get logger instance by name."""
    global _loggers
    
    if name not in _loggers:
        # Create new logger with same settings as root
        root_settings = _loggers.get("root")
        settings = root_settings.settings if root_settings else LoggingSettings()
        _loggers[name] = GridTradingLogger(name, settings)
    
    return _loggers[name]


def log_trade_execution(
    logger: GridTradingLogger,
    side: str,
    symbol: str,
    price: float,
    amount: float,
    total: float,
    strategy: str = "grid"
):
    """Log trade execution with structured format."""
    logger.info(
        f"🔄 TRADE EXECUTED | "
        f"Strategy: {strategy.upper()} | "
        f"Side: {side.upper()} | "
        f"Symbol: {symbol} | "
        f"Price: {price:.4f} | "
        f"Amount: {amount:.6f} | "
        f"Total: {total:.2f} USDT"
    )


def log_risk_alert(
    logger: GridTradingLogger,
    alert_type: str,
    current_value: float,
    threshold: float,
    action: str = "MONITOR"
):
    """Log risk management alerts."""
    logger.warning(
        f"⚠️ RISK ALERT | "
        f"Type: {alert_type} | "
        f"Current: {current_value:.4f} | "
        f"Threshold: {threshold:.4f} | "
        f"Action: {action}"
    )


def log_system_status(
    logger: GridTradingLogger,
    status: str,
    details: str = ""
):
    """Log system status updates."""
    emoji = "🟢" if status == "RUNNING" else "🔴" if status == "ERROR" else "🟡"
    logger.info(f"{emoji} SYSTEM {status} | {details}")


def log_strategy_signal(
    logger: GridTradingLogger,
    strategy: str,
    signal: str,
    price: float,
    reason: str = ""
):
    """Log strategy signals."""
    logger.info(
        f"📊 STRATEGY SIGNAL | "
        f"Strategy: {strategy.upper()} | "
        f"Signal: {signal.upper()} | "
        f"Price: {price:.4f} | "
        f"Reason: {reason}"
    )
