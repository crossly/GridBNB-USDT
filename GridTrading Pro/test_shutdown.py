#!/usr/bin/env python3
"""
Test script to verify graceful shutdown
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_shutdown():
    """Test shutdown mechanism"""
    print("Testing shutdown mechanism...")
    
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, _):
        print(f"Received signal {signum}")
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(shutdown_event.set)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Press Ctrl+C to test shutdown...")
    
    try:
        # Simulate main loop
        while True:
            print("Running... (Press Ctrl+C to stop)")
            
            # Check for shutdown signal with timeout
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=2.0)
                print("Shutdown signal received!")
                break
            except asyncio.TimeoutError:
                continue
                
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught")
    
    print("Shutdown test completed")

if __name__ == "__main__":
    asyncio.run(test_shutdown())
