#!/usr/bin/env python3
"""
Auto-sync .env.testnet to .env when modified
"""

import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class EnvFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_sync = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('.env.testnet'):
            # Avoid rapid successive syncs
            current_time = time.time()
            if current_time - self.last_sync < 1:
                return
                
            self.sync_files()
            self.last_sync = current_time
    
    def sync_files(self):
        try:
            shutil.copy2('.env.testnet', '.env')
            print(f"✅ {time.strftime('%H:%M:%S')} - Synced .env.testnet to .env")
            
            # Show the updated INITIAL_BASE_PRICE
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('INITIAL_BASE_PRICE='):
                        base_price = line.strip().split('=')[1]
                        print(f"📊 Base price updated to: {base_price} USDT")
                        break
                        
        except Exception as e:
            print(f"❌ Failed to sync: {str(e)}")

def main():
    print("🔄 Auto-sync monitor started")
    print("📝 Watching .env.testnet for changes...")
    print("💡 Edit .env.testnet and changes will auto-sync to .env")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    # Initial sync
    handler = EnvFileHandler()
    handler.sync_files()
    
    # Start monitoring
    observer = Observer()
    observer.schedule(handler, '.', recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Auto-sync monitor stopped")
    
    observer.join()

if __name__ == "__main__":
    main()
