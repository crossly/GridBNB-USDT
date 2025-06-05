#!/usr/bin/env python3
"""
Check if .env and .env.testnet are synchronized
"""

import os
from pathlib import Path

def read_env_file(file_path):
    """Read environment file and return as dict"""
    env_vars = {}
    if Path(file_path).exists():
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars

def main():
    print("🔍 Environment Files Sync Check")
    print("=" * 50)
    
    # Read both files
    env_testnet = read_env_file('.env.testnet')
    env_main = read_env_file('.env')
    
    if not env_testnet:
        print("❌ .env.testnet file not found or empty")
        return
    
    if not env_main:
        print("❌ .env file not found or empty")
        return
    
    # Check key parameters
    important_keys = [
        'INITIAL_BASE_PRICE',
        'INITIAL_PRINCIPAL', 
        'BINANCE_API_KEY',
        'BINANCE_API_SECRET',
        'ENVIRONMENT'
    ]
    
    all_synced = True
    
    for key in important_keys:
        testnet_value = env_testnet.get(key, 'NOT_SET')
        main_value = env_main.get(key, 'NOT_SET')
        
        if testnet_value == main_value:
            print(f"✅ {key}: {testnet_value}")
        else:
            print(f"❌ {key}: .env.testnet='{testnet_value}' vs .env='{main_value}'")
            all_synced = False
    
    print("-" * 50)
    
    if all_synced:
        print("✅ All important parameters are synchronized!")
    else:
        print("❌ Files are NOT synchronized!")
        print("\n💡 To fix this, run:")
        print("   python3 sync_env.py")
        print("   # or")
        print("   cp .env.testnet .env")
    
    # Show file modification times
    try:
        testnet_mtime = os.path.getmtime('.env.testnet')
        main_mtime = os.path.getmtime('.env')
        
        print(f"\n📅 File timestamps:")
        print(f"   .env.testnet: {time.ctime(testnet_mtime)}")
        print(f"   .env:         {time.ctime(main_mtime)}")
        
        if testnet_mtime > main_mtime:
            print("⚠️  .env.testnet is newer than .env - sync needed!")
        elif main_mtime > testnet_mtime:
            print("ℹ️  .env is newer than .env.testnet")
        else:
            print("✅ Files have same timestamp")
            
    except Exception as e:
        print(f"⚠️  Could not check file timestamps: {e}")

if __name__ == "__main__":
    import time
    main()
