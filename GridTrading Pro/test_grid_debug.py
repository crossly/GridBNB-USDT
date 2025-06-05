#!/usr/bin/env python3
"""
Test script to verify grid debug output
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import Settings
from src.utils.logger import setup_logger, get_logger
from src.core.grid_engine import GridState

class MockGridEngine:
    """Mock grid engine for testing"""
    def __init__(self, settings):
        self.settings = settings
        self.logger = get_logger("MockGridEngine")
        self.grid_state = None

    def _calculate_grid_bands(self):
        """Calculate grid upper and lower bands."""
        grid_decimal = self.grid_state.grid_size / 100

        self.grid_state.upper_band = self.grid_state.base_price * (1 + grid_decimal)
        self.grid_state.lower_band = self.grid_state.base_price * (1 - grid_decimal)

        # Calculate multiple grid levels for debug output
        self._log_grid_levels()

    def _log_grid_levels(self):
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
            self.logger.debug(f"GRID DEBUG INFO - BTC/USDT")
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

async def test_grid_debug():
    """Test grid debug output"""
    print("Testing grid debug output...")

    # Load settings
    settings = Settings.load_from_file("config.testnet.yaml")

    # Setup logger with DEBUG level
    setup_logger(settings.logging)

    # Create mock grid engine
    grid_engine = MockGridEngine(settings)
    
    # Initialize grid state manually for testing
    grid_engine.grid_state = GridState(
        base_price=100000.0,  # $100,000 BTC
        current_price=100500.0,  # Current price slightly higher
        grid_size=0.5,  # 0.5% grid
        upper_band=0,
        lower_band=0,
        volatility=0.15,
        price_history=[],
        last_adjustment_time=0
    )
    
    print("\n" + "="*80)
    print("TESTING GRID DEBUG OUTPUT")
    print("="*80)
    
    # Calculate and display grid bands
    grid_engine._calculate_grid_bands()
    
    print("\nGrid calculation completed!")
    print(f"Base Price: {grid_engine.grid_state.base_price:.4f}")
    print(f"Current Price: {grid_engine.grid_state.current_price:.4f}")
    print(f"Upper Band: {grid_engine.grid_state.upper_band:.4f}")
    print(f"Lower Band: {grid_engine.grid_state.lower_band:.4f}")
    
    # Test with different grid sizes
    print("\n" + "="*80)
    print("TESTING DIFFERENT GRID SIZES")
    print("="*80)
    
    for grid_size in [0.2, 0.5, 1.0, 2.0]:
        print(f"\n--- Testing Grid Size: {grid_size}% ---")
        grid_engine.grid_state.grid_size = grid_size
        grid_engine._calculate_grid_bands()
    
    print("\nGrid debug test completed!")

if __name__ == "__main__":
    asyncio.run(test_grid_debug())
