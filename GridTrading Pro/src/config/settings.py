"""
Settings management for GridTrading Pro.

This module handles loading and validating configuration from YAML files
and environment variables using Pydantic for type safety and validation.
"""

import os
import yaml
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from dotenv import load_dotenv

from .constants import (
    TradingMode, DEFAULT_CONFIG, SUPPORTED_SYMBOLS, 
    MAX_LEVERAGE, MIN_LEVERAGE, BINANCE_ENDPOINTS
)


class TradingSettings(BaseModel):
    """Trading configuration settings."""
    mode: TradingMode = Field(default=TradingMode.SPOT)
    symbol: str = Field(default="BNB/USDT")
    leverage: int = Field(default=1, ge=MIN_LEVERAGE, le=MAX_LEVERAGE)
    testnet: bool = Field(default=False)
    min_trade_amount: float = Field(default=20.0, gt=0)
    order_timeout: int = Field(default=30, gt=0)
    min_trade_interval: int = Field(default=30, gt=0)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if v not in SUPPORTED_SYMBOLS:
            raise ValueError(f"Unsupported symbol: {v}. Supported: {SUPPORTED_SYMBOLS}")
        return v

    @model_validator(mode='after')
    def validate_leverage(self):
        if self.mode == TradingMode.SPOT and self.leverage != 1:
            raise ValueError("Leverage must be 1 for spot trading")
        return self


class GridSettings(BaseModel):
    """Grid trading configuration settings."""
    initial_size: float = Field(default=2.0, gt=0, le=10.0)
    min_size: float = Field(default=1.0, gt=0, le=10.0)
    max_size: float = Field(default=4.0, gt=0, le=10.0)
    dynamic_adjustment: bool = Field(default=True)
    volatility_thresholds: List[Dict[str, Union[List[float], float]]] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_grid_sizes(self):
        if self.min_size >= self.max_size:
            raise ValueError("min_size must be less than max_size")
        if not (self.min_size <= self.initial_size <= self.max_size):
            raise ValueError("initial_size must be between min_size and max_size")
        return self


class RiskSettings(BaseModel):
    """Risk management configuration settings."""
    max_drawdown: float = Field(default=-0.15, le=0)
    daily_loss_limit: float = Field(default=-0.05, le=0)
    max_position_ratio: float = Field(default=0.9, ge=0, le=1.0)
    min_position_ratio: float = Field(default=0.1, ge=0, le=1.0)
    risk_check_interval: int = Field(default=300, gt=0)

    @model_validator(mode='after')
    def validate_position_ratios(self):
        if self.min_position_ratio >= self.max_position_ratio:
            raise ValueError("min_position_ratio must be less than max_position_ratio")
        return self


class S1StrategySettings(BaseModel):
    """S1 strategy configuration settings."""
    enabled: bool = Field(default=True)
    lookback_days: int = Field(default=52, gt=0, le=365)
    sell_target_percent: float = Field(default=0.50, ge=0, le=1.0)
    buy_target_percent: float = Field(default=0.70, ge=0, le=1.0)


class TelegramSettings(BaseModel):
    """Telegram notification settings."""
    enabled: bool = Field(default=True)
    bot_token: Optional[str] = Field(default=None)
    chat_id: Optional[str] = Field(default=None)
    notification_levels: List[str] = Field(default=["trade", "risk", "system", "error"])

    @model_validator(mode='after')
    def validate_telegram_config(self):
        if self.enabled and not self.bot_token:
            raise ValueError("bot_token is required when Telegram is enabled")
        if self.enabled and not self.chat_id:
            raise ValueError("chat_id is required when Telegram is enabled")
        return self


class NotificationSettings(BaseModel):
    """Notification configuration settings."""
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)


class WebSettings(BaseModel):
    """Web interface configuration settings."""
    enabled: bool = Field(default=True)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=58181, ge=1024, le=65535)
    auto_refresh_interval: int = Field(default=2000, gt=0)


class LoggingSettings(BaseModel):
    """Logging configuration settings."""
    level: str = Field(default="INFO")
    file_rotation: str = Field(default="midnight")
    backup_count: int = Field(default=7, ge=1)
    format: str = Field(default="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    @field_validator('level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Valid levels: {valid_levels}")
        return v.upper()


class DataSettings(BaseModel):
    """Data persistence configuration settings."""
    save_interval: int = Field(default=60, gt=0)
    backup_count: int = Field(default=10, ge=1)
    history_limit: int = Field(default=1000, gt=0)


class APISettings(BaseModel):
    """API configuration settings."""
    timeout: int = Field(default=30000, gt=0)
    recv_window: int = Field(default=5000, gt=0)
    rate_limit: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=1)


class Settings(BaseModel):
    """Main settings class that combines all configuration sections."""
    trading: TradingSettings = Field(default_factory=TradingSettings)
    grid: GridSettings = Field(default_factory=GridSettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)
    s1_strategy: S1StrategySettings = Field(default_factory=S1StrategySettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    web: WebSettings = Field(default_factory=WebSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    api: APISettings = Field(default_factory=APISettings)

    # Environment variables
    binance_api_key: Optional[str] = Field(default=None)
    binance_api_secret: Optional[str] = Field(default=None)
    initial_principal: float = Field(default=0.0, ge=0)
    initial_base_price: float = Field(default=0.0, ge=0)
    environment: str = Field(default="production")

    class Config:
        env_prefix = ""
        case_sensitive = False

    @classmethod
    def load_from_file(cls, config_path: str = "config.yaml") -> "Settings":
        """Load settings from YAML file and environment variables."""
        # Load environment variables
        load_dotenv()
        
        # Load YAML configuration
        config_data = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        
        # Merge with environment variables (only if not already set in config)
        env_vars = {
            'binance_api_key': os.getenv('BINANCE_API_KEY'),
            'binance_api_secret': os.getenv('BINANCE_API_SECRET'),
            'initial_principal': float(os.getenv('INITIAL_PRINCIPAL', 0)),
            'initial_base_price': float(os.getenv('INITIAL_BASE_PRICE', 0)),
            'environment': os.getenv('ENVIRONMENT', 'production'),
        }

        # Update Telegram settings from environment
        if 'notifications' not in config_data:
            config_data['notifications'] = {}
        if 'telegram' not in config_data['notifications']:
            config_data['notifications']['telegram'] = {}

        telegram_config = config_data['notifications']['telegram']
        telegram_config['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN', telegram_config.get('bot_token'))
        telegram_config['chat_id'] = os.getenv('TELEGRAM_CHAT_ID', telegram_config.get('chat_id'))

        # Merge configurations - YAML config takes precedence over env vars for non-sensitive data
        for key, value in env_vars.items():
            if value is not None and value != 0:
                # Always use env vars for sensitive data and initial_base_price
                if key in ['binance_api_key', 'binance_api_secret', 'initial_base_price']:
                    config_data[key] = value
                # Only use env var if not already set in YAML config for other values
                elif key not in config_data or config_data[key] == 0:
                    config_data[key] = value
        
        return cls(**config_data)

    def get_exchange_endpoint(self) -> str:
        """Get the appropriate exchange endpoint based on trading mode and testnet setting."""
        mode = self.trading.mode.value
        env = "testnet" if self.trading.testnet else "production"
        return BINANCE_ENDPOINTS[mode][env]

    def validate_api_credentials(self) -> bool:
        """Validate that required API credentials are present."""
        return bool(self.binance_api_key and self.binance_api_secret)

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.dict()

    def save_to_file(self, config_path: str = "config.yaml") -> None:
        """Save current settings to YAML file (excluding sensitive data)."""
        config_dict = self.dict(exclude={'binance_api_key', 'binance_api_secret'})
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
