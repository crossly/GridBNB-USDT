#!/usr/bin/env python3
"""
Test script to verify configuration loading
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.config.settings import Settings
    print("✅ Successfully imported Settings")
    
    # Test loading testnet config
    settings = Settings.load_from_file("config.testnet.yaml")
    print("✅ Successfully loaded testnet configuration")
    
    print(f"Trading mode: {settings.trading.mode}")
    print(f"Symbol: {settings.trading.symbol}")
    print(f"Leverage: {settings.trading.leverage}")
    print(f"Testnet: {settings.trading.testnet}")
    print(f"Grid size: {settings.grid.initial_size}")
    
    print("✅ Configuration test passed!")
    
except Exception as e:
    print(f"❌ Configuration test failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
