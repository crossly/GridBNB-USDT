#!/usr/bin/env python3
"""
Quick status check script for GridTrading Pro
"""

import requests
import json
import time
from datetime import datetime

def check_system_status():
    """Check system status via API"""
    try:
        # Check if web server is running
        response = requests.get("http://localhost:58181/api/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            
            print("=" * 60)
            print("GridTrading Pro Status Check")
            print("=" * 60)
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"System Status: {'🟢 RUNNING' if status.get('is_running') else '🔴 STOPPED'}")
            print(f"Symbol: {status.get('symbol', 'N/A')}")
            print(f"Current Price: {status.get('current_price', 0):.4f} USDT")
            print(f"Grid Size: {status.get('grid_size', 0):.1f}%")
            print(f"Total Profit: {status.get('total_profit', 0):.2f} USDT")
            print(f"Trade Count: {status.get('trade_count', 0)}")
            print(f"Uptime: {status.get('uptime', 'N/A')}")
            
            # Check active orders
            active_orders = status.get('active_orders', {})
            print(f"Active Buy Order: {'✅' if active_orders.get('buy') else '❌'}")
            print(f"Active Sell Order: {'✅' if active_orders.get('sell') else '❌'}")
            
            print("=" * 60)
            print("Web Dashboard: http://localhost:58181")
            print("=" * 60)
            
        else:
            print(f"❌ Failed to get status: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to GridTrading Pro")
        print("   Make sure the system is running")
    except Exception as e:
        print(f"❌ Error checking status: {str(e)}")

def check_recent_trades():
    """Check recent trades"""
    try:
        response = requests.get("http://localhost:58181/api/trades?limit=5", timeout=5)
        if response.status_code == 200:
            trades = response.json()
            
            print("\n📊 Recent Trades:")
            print("-" * 60)
            
            if not trades:
                print("No trades yet")
            else:
                for trade in trades:
                    trade_time = datetime.fromtimestamp(trade['timestamp']).strftime('%H:%M:%S')
                    side_emoji = "🟢" if trade['side'] == 'buy' else "🔴"
                    print(f"{side_emoji} {trade_time} | {trade['side'].upper()} | "
                          f"{trade['price']:.4f} | {trade['amount']:.6f} | "
                          f"{trade['total']:.2f} USDT")
            
    except Exception as e:
        print(f"❌ Error getting trades: {str(e)}")

if __name__ == "__main__":
    check_system_status()
    check_recent_trades()
