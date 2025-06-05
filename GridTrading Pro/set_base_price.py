#!/usr/bin/env python3
"""
Script to set or update the base price for GridTrading Pro
"""

import sys
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import Settings

def update_config_file(config_file: str, new_base_price: float):
    """Update base price in configuration file"""
    try:
        import yaml
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        config['initial_base_price'] = new_base_price
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Updated {config_file}: initial_base_price = {new_base_price}")
        
    except Exception as e:
        print(f"❌ Failed to update {config_file}: {str(e)}")

def update_env_file(env_file: str, new_base_price: float):
    """Update base price in environment file"""
    try:
        lines = []
        updated = False
        
        if Path(env_file).exists():
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        # Update existing line or add new one
        for i, line in enumerate(lines):
            if line.startswith('INITIAL_BASE_PRICE='):
                lines[i] = f'INITIAL_BASE_PRICE={new_base_price}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'INITIAL_BASE_PRICE={new_base_price}\n')
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Updated {env_file}: INITIAL_BASE_PRICE = {new_base_price}")
        
    except Exception as e:
        print(f"❌ Failed to update {env_file}: {str(e)}")

def update_trading_state(new_base_price: float):
    """Update base price in existing trading state"""
    try:
        state_file = "data/trading_state.json"
        
        if Path(state_file).exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            state['base_price'] = new_base_price
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"✅ Updated {state_file}: base_price = {new_base_price}")
        else:
            print(f"ℹ️  No existing trading state file found")
            
    except Exception as e:
        print(f"❌ Failed to update trading state: {str(e)}")

def get_current_price():
    """Get current market price for reference"""
    try:
        import requests
        
        # Get current BTC price from Binance API
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data['price'])
    except:
        pass
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Set base price for GridTrading Pro')
    parser.add_argument('base_price', type=float, nargs='?', help='New base price (e.g., 104000.0)')
    parser.add_argument('--config', default='config.testnet.yaml', help='Config file to update')
    parser.add_argument('--env', default='.env.testnet', help='Environment file to update')
    parser.add_argument('--state', action='store_true', help='Also update existing trading state')
    parser.add_argument('--current', action='store_true', help='Use current market price')
    
    args = parser.parse_args()
    
    if args.current:
        current_price = get_current_price()
        if current_price:
            new_base_price = current_price
            print(f"📊 Current BTC/USDT price: {current_price:.2f}")
        else:
            print("❌ Failed to get current price")
            return
    elif args.base_price is not None:
        new_base_price = args.base_price
    else:
        print("❌ Please provide a base price or use --current flag")
        parser.print_help()
        return
    
    print(f"\n🎯 Setting base price to: {new_base_price:.2f} USDT")
    print("=" * 50)
    
    # Update configuration file
    if Path(args.config).exists():
        update_config_file(args.config, new_base_price)
    else:
        print(f"⚠️  Config file {args.config} not found")
    
    # Update environment file
    update_env_file(args.env, new_base_price)
    
    # Update trading state if requested
    if args.state:
        update_trading_state(new_base_price)
    
    print("\n✅ Base price update completed!")
    print("\n💡 Tips:")
    print("   - Restart GridTrading Pro to apply changes")
    print("   - Use --current flag to set to current market price")
    print("   - Use --state flag to update existing trading state")
    
    # Show current market price for reference
    current_price = get_current_price()
    if current_price:
        diff_pct = ((new_base_price - current_price) / current_price) * 100
        print(f"\n📊 Current market price: {current_price:.2f} USDT")
        print(f"📈 Your base price is {diff_pct:+.2f}% from current price")

if __name__ == "__main__":
    main()
