#!/usr/bin/env python3
"""
Script to update base price in existing trading state
"""

import json
import sys
from pathlib import Path

def update_base_price_in_state(new_base_price: float):
    """Update base price in trading state file"""
    
    state_file = Path("data/trading_state.json")
    
    if not state_file.exists():
        print("ℹ️  No trading state file found - new base price will be used from config")
        return True
    
    try:
        # Read current state
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        old_base_price = state.get('base_price', 0)
        
        # Update base price
        state['base_price'] = new_base_price
        
        # Write back
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"✅ Updated trading state:")
        print(f"   Old base price: {old_base_price:.2f} USDT")
        print(f"   New base price: {new_base_price:.2f} USDT")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update trading state: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 update_base_price_in_state.py <new_base_price>")
        print("Example: python3 update_base_price_in_state.py 108000.0")
        return
    
    try:
        new_base_price = float(sys.argv[1])
        update_base_price_in_state(new_base_price)
    except ValueError:
        print("❌ Invalid base price. Please provide a number.")

if __name__ == "__main__":
    main()
