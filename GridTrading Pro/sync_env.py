#!/usr/bin/env python3
"""
Script to synchronize environment variables between .env.testnet and .env
"""

import os
import shutil
from pathlib import Path

def sync_env_files():
    """Synchronize .env.testnet to .env"""
    
    env_testnet = Path('.env.testnet')
    env_file = Path('.env')
    
    if not env_testnet.exists():
        print("❌ .env.testnet file not found!")
        return False
    
    try:
        # Copy .env.testnet to .env
        shutil.copy2(env_testnet, env_file)
        print(f"✅ Copied {env_testnet} to {env_file}")
        
        # Read and display the INITIAL_BASE_PRICE
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if line.startswith('INITIAL_BASE_PRICE='):
                base_price = line.strip().split('=')[1]
                print(f"📊 Base price set to: {base_price} USDT")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to sync environment files: {str(e)}")
        return False

def update_env_value(key: str, value: str):
    """Update a specific value in .env files"""
    
    files_to_update = ['.env', '.env.testnet']
    
    for file_path in files_to_update:
        if not Path(file_path).exists():
            continue
            
        try:
            # Read current content
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Update the specific key
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f'{key}='):
                    lines[i] = f'{key}={value}\n'
                    updated = True
                    break
            
            # Add the key if it doesn't exist
            if not updated:
                lines.append(f'{key}={value}\n')
            
            # Write back
            with open(file_path, 'w') as f:
                f.writelines(lines)
            
            print(f"✅ Updated {file_path}: {key}={value}")
            
        except Exception as e:
            print(f"❌ Failed to update {file_path}: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # Just sync files
        sync_env_files()
    elif len(sys.argv) == 3:
        # Update specific key-value
        key = sys.argv[1]
        value = sys.argv[2]
        update_env_value(key, value)
        sync_env_files()
    else:
        print("Usage:")
        print("  python3 sync_env.py                    # Sync .env.testnet to .env")
        print("  python3 sync_env.py KEY VALUE          # Update KEY=VALUE in both files")
        print("")
        print("Examples:")
        print("  python3 sync_env.py INITIAL_BASE_PRICE 104000.0")
        print("  python3 sync_env.py INITIAL_PRINCIPAL 5000.0")
