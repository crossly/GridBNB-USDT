#!/usr/bin/env python3
"""
GridTrading Pro - Advanced Grid Trading System

Main entry point for the GridTrading Pro application.
Supports both Binance Spot and USDT-M Futures trading with advanced
risk management, strategy execution, and Telegram notifications.

Usage:
    python main.py [--config CONFIG_FILE] [--testnet] [--dry-run]

Author: GridTrading Pro Team
Version: 2.0.0
"""

import asyncio
import argparse
import signal
import sys
import traceback
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import Settings
from src.utils.logger import setup_logger, get_logger
from src.exchanges import create_exchange
from src.notifications import create_notifier
from src.core.grid_engine import GridEngine
from src.web.server import WebServer


class GridTradingApp:
    """Main application class for GridTrading Pro."""
    
    def __init__(self, config_file: str = "config.yaml"):
        """Initialize the application."""
        self.config_file = config_file
        self.settings = None
        self.exchange = None
        self.notifier = None
        self.grid_engine = None
        self.web_server = None
        self.logger = None
        self.is_running = False
        
        # Signal handling
        self.shutdown_event = asyncio.Event()
        
    async def initialize(self) -> bool:
        """Initialize all components."""
        try:
            # Load settings
            self.settings = Settings.load_from_file(self.config_file)
            
            # Setup logging
            setup_logger(self.settings.logging)
            self.logger = get_logger("GridTradingApp")
            
            self.logger.info("="*60)
            self.logger.info("GridTrading Pro v2.0.0 - Initializing...")
            self.logger.info("="*60)
            
            # Validate API credentials
            if not self.settings.validate_api_credentials():
                raise ValueError("Invalid or missing API credentials")
            
            # Initialize exchange
            self.exchange = create_exchange(
                trading_mode=self.settings.trading.mode.value,
                api_key=self.settings.binance_api_key,
                api_secret=self.settings.binance_api_secret,
                testnet=self.settings.trading.testnet,
                timeout=self.settings.api.timeout
            )
            
            if not await self.exchange.initialize():
                raise Exception("Failed to initialize exchange")
            
            # Initialize notifier
            if self.settings.notifications.telegram.enabled:
                self.notifier = create_notifier(
                    platform="telegram",
                    bot_token=self.settings.notifications.telegram.bot_token,
                    chat_id=self.settings.notifications.telegram.chat_id,
                    notification_levels=self.settings.notifications.telegram.notification_levels
                )
                
                # Test notification connection
                if not await self.notifier.test_connection():
                    self.logger.warning("Telegram notification test failed")
                else:
                    self.logger.info("Telegram notifications enabled")
            
            # Set leverage for futures
            if self.exchange.is_futures_mode() and self.settings.trading.leverage > 1:
                await self.exchange.set_leverage(
                    self.settings.trading.symbol,
                    self.settings.trading.leverage
                )
                self.logger.info(f"Leverage set to {self.settings.trading.leverage}x")
            
            # Initialize grid engine
            self.grid_engine = GridEngine(
                settings=self.settings,
                exchange=self.exchange,
                notifier=self.notifier
            )
            
            if not await self.grid_engine.initialize():
                raise Exception("Failed to initialize grid engine")

            # Initialize web server
            if self.settings.web.enabled:
                self.web_server = WebServer(self.settings, self.grid_engine)
                await self.web_server.start()
                self.logger.info(f"Web server started on http://{self.settings.web.host}:{self.settings.web.port}")

            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Initialization failed: {str(e)}")
                self.logger.error(traceback.format_exc())
            else:
                print(f"Initialization failed: {str(e)}")
                print(traceback.format_exc())
            return False
    
    async def run(self) -> None:
        """Run the main application."""
        if not await self.initialize():
            return

        try:
            self.is_running = True

            # Setup signal handlers
            self._setup_signal_handlers()

            # Send startup notification
            if self.notifier:
                await self.notifier.notify_system_status(
                    "STARTED",
                    f"GridTrading Pro started for {self.settings.trading.symbol} "
                    f"({'Testnet' if self.settings.trading.testnet else 'Mainnet'})"
                )

            self.logger.info("GridTrading Pro started successfully")
            self.logger.info(f"Trading: {self.settings.trading.symbol}")
            self.logger.info(f"Mode: {self.settings.trading.mode.value}")
            self.logger.info(f"Exchange: {'Testnet' if self.settings.trading.testnet else 'Mainnet'}")

            # Start grid engine in background task
            grid_task = asyncio.create_task(self.grid_engine.start())

            # Wait for shutdown signal
            try:
                await self.shutdown_event.wait()
                self.logger.info("Shutdown signal received")
            except asyncio.CancelledError:
                self.logger.info("Application cancelled")

            # Stop grid engine gracefully
            if self.grid_engine and self.grid_engine.is_running:
                await self.grid_engine.stop()

            # Cancel grid engine task if still running
            if not grid_task.done():
                grid_task.cancel()
                try:
                    await grid_task
                except asyncio.CancelledError:
                    pass

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
            self.logger.error(traceback.format_exc())

            if self.notifier:
                await self.notifier.notify_error(
                    "APPLICATION_ERROR",
                    str(e),
                    "Main application loop"
                )
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        if not self.is_running:
            return
        
        self.logger.info("Shutting down GridTrading Pro...")
        self.is_running = False
        
        try:
            # Stop grid engine
            if self.grid_engine:
                await self.grid_engine.stop()
            
            # Close web server
            if self.web_server:
                await self.web_server.stop()

            # Close exchange connection
            if self.exchange:
                await self.exchange.close()

            # Send shutdown notification
            if self.notifier:
                await self.notifier.notify_system_status(
                    "STOPPED",
                    "GridTrading Pro shutdown completed"
                )
                await self.notifier.close()
            
            self.logger.info("Shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, _):
            self.logger.info(f"Received signal {signum}")
            # Use asyncio to set the event in a thread-safe way
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(self.shutdown_event.set)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def get_status(self) -> dict:
        """Get application status."""
        status = {
            'is_running': self.is_running,
            'config_file': self.config_file,
        }
        
        if self.settings:
            status['trading_symbol'] = self.settings.trading.symbol
            status['trading_mode'] = self.settings.trading.mode.value
            status['testnet'] = self.settings.trading.testnet
        
        if self.grid_engine:
            status['grid_engine'] = self.grid_engine.get_status()
        
        return status


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="GridTrading Pro - Advanced Grid Trading System"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Configuration file path (default: config.yaml)"
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Force testnet mode"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no actual trading)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="GridTrading Pro v2.0.0"
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not Path(args.config).exists():
        print(f"Error: Configuration file '{args.config}' not found")
        print("Please copy config.yaml.example to config.yaml and configure it")
        return 1
    
    # Create and run application
    app = GridTradingApp(config_file=args.config)
    
    try:
        await app.run()
        return 0
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    try:
        # Set event loop policy for Windows
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run the application
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
