"""
Web server for GridTrading Pro dashboard.

This module provides a simple web interface for monitoring
the trading system status and performance.
"""

from aiohttp import web
import json
import time
from typing import Optional, Dict, Any

from ..utils.logger import get_logger
from ..config.settings import Settings


class WebServer:
    """Simple web server for monitoring dashboard."""
    
    def __init__(self, settings: Settings, grid_engine=None):
        """Initialize web server."""
        self.settings = settings
        self.grid_engine = grid_engine
        self.logger = get_logger("WebServer")
        
        self.app = web.Application()
        self.runner = None
        self.site = None
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup web routes."""
        self.app.router.add_get('/', self.handle_dashboard)
        self.app.router.add_get('/api/status', self.handle_api_status)
        self.app.router.add_get('/api/trades', self.handle_api_trades)
        self.app.router.add_get('/api/analytics', self.handle_api_analytics)
    
    async def start(self):
        """Start web server."""
        if not self.settings.web.enabled:
            self.logger.info("Web server disabled in configuration")
            return
        
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(
                self.runner,
                self.settings.web.host,
                self.settings.web.port
            )
            await self.site.start()
            
            self.logger.info(
                f"Web server started on http://{self.settings.web.host}:{self.settings.web.port}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start web server: {str(e)}")
    
    async def stop(self):
        """Stop web server."""
        if self.runner:
            await self.runner.cleanup()
        self.logger.info("Web server stopped")
    
    async def handle_dashboard(self, request):
        """Handle dashboard page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>GridTrading Pro Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header { text-align: center; color: #333; }
                .status { display: flex; justify-content: space-between; flex-wrap: wrap; }
                .metric { text-align: center; padding: 10px; }
                .metric-value { font-size: 24px; font-weight: bold; color: #2563eb; }
                .metric-label { color: #666; font-size: 14px; }
                .running { color: #10b981; }
                .stopped { color: #ef4444; }
                .trades-table { width: 100%; border-collapse: collapse; }
                .trades-table th, .trades-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                .trades-table th { background: #f8f9fa; }
                .buy { color: #10b981; }
                .sell { color: #ef4444; }
                .refresh-btn { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
                .refresh-btn:hover { background: #1d4ed8; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1 class="header">GridTrading Pro Dashboard</h1>
                    <p class="header">Advanced Grid Trading System v2.0.0</p>
                </div>
                
                <div class="card">
                    <h2>System Status</h2>
                    <div class="status" id="status-container">
                        <div class="metric">
                            <div class="metric-value" id="system-status">Loading...</div>
                            <div class="metric-label">System Status</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="current-price">--</div>
                            <div class="metric-label">Current Price</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="grid-size">--</div>
                            <div class="metric-label">Grid Size</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="total-profit">--</div>
                            <div class="metric-label">Total Profit</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Recent Trades</h2>
                    <button class="refresh-btn" onclick="loadData()">Refresh</button>
                    <table class="trades-table" id="trades-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Side</th>
                                <th>Price</th>
                                <th>Amount</th>
                                <th>Total</th>
                                <th>Profit</th>
                            </tr>
                        </thead>
                        <tbody id="trades-body">
                            <tr><td colspan="6">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h2>Performance Analytics</h2>
                    <div class="status" id="analytics-container">
                        <div class="metric">
                            <div class="metric-value" id="total-trades">--</div>
                            <div class="metric-label">Total Trades</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="win-rate">--</div>
                            <div class="metric-label">Win Rate</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="profit-factor">--</div>
                            <div class="metric-label">Profit Factor</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="max-drawdown">--</div>
                            <div class="metric-label">Max Drawdown</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                async function loadData() {
                    try {
                        // Load status
                        const statusResponse = await fetch('/api/status');
                        const status = await statusResponse.json();
                        
                        document.getElementById('system-status').textContent = status.is_running ? 'RUNNING' : 'STOPPED';
                        document.getElementById('system-status').className = 'metric-value ' + (status.is_running ? 'running' : 'stopped');
                        document.getElementById('current-price').textContent = status.current_price ? status.current_price.toFixed(4) : '--';
                        document.getElementById('grid-size').textContent = status.grid_size ? status.grid_size.toFixed(1) + '%' : '--';
                        document.getElementById('total-profit').textContent = status.total_profit ? status.total_profit.toFixed(2) + ' USDT' : '--';
                        
                        // Load trades
                        const tradesResponse = await fetch('/api/trades?limit=10');
                        const trades = await tradesResponse.json();
                        
                        const tbody = document.getElementById('trades-body');
                        tbody.innerHTML = '';
                        
                        if (trades.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="6">No trades yet</td></tr>';
                        } else {
                            trades.forEach(trade => {
                                const row = document.createElement('tr');
                                const time = new Date(trade.timestamp * 1000).toLocaleString();
                                const sideClass = trade.side === 'buy' ? 'buy' : 'sell';
                                
                                row.innerHTML = `
                                    <td>${time}</td>
                                    <td class="${sideClass}">${trade.side.toUpperCase()}</td>
                                    <td>${trade.price.toFixed(4)}</td>
                                    <td>${trade.amount.toFixed(6)}</td>
                                    <td>${trade.total.toFixed(2)}</td>
                                    <td>${trade.profit ? trade.profit.toFixed(2) : '0.00'}</td>
                                `;
                                tbody.appendChild(row);
                            });
                        }
                        
                        // Load analytics
                        const analyticsResponse = await fetch('/api/analytics');
                        const analytics = await analyticsResponse.json();
                        
                        document.getElementById('total-trades').textContent = analytics.total_trades || 0;
                        document.getElementById('win-rate').textContent = analytics.win_rate ? (analytics.win_rate * 100).toFixed(1) + '%' : '--';
                        document.getElementById('profit-factor').textContent = analytics.profit_factor ? analytics.profit_factor.toFixed(2) : '--';
                        document.getElementById('max-drawdown').textContent = analytics.max_drawdown ? (analytics.max_drawdown * 100).toFixed(1) + '%' : '--';
                        
                    } catch (error) {
                        console.error('Failed to load data:', error);
                    }
                }
                
                // Load data on page load
                loadData();
                
                // Auto-refresh every 5 seconds
                setInterval(loadData, 5000);
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def handle_api_status(self, request):
        """Handle status API endpoint."""
        try:
            if self.grid_engine:
                status = self.grid_engine.get_status()
            else:
                status = {
                    'is_running': False,
                    'symbol': self.settings.trading.symbol,
                    'current_price': 0,
                    'grid_size': 0,
                    'total_profit': 0,
                    'trade_count': 0
                }
            
            return web.json_response(status)
            
        except Exception as e:
            self.logger.error(f"Status API error: {str(e)}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_api_trades(self, request):
        """Handle trades API endpoint."""
        try:
            limit = int(request.query.get('limit', 10))
            
            if self.grid_engine and hasattr(self.grid_engine, 'data_manager'):
                trades = self.grid_engine.data_manager.get_trades(limit=limit)
            else:
                trades = []
            
            return web.json_response(trades)
            
        except Exception as e:
            self.logger.error(f"Trades API error: {str(e)}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_api_analytics(self, request):
        """Handle analytics API endpoint."""
        try:
            if self.grid_engine and hasattr(self.grid_engine, 'data_manager'):
                analytics = await self.grid_engine.data_manager.get_analytics()
                analytics_dict = {
                    'total_trades': analytics.total_trades,
                    'win_rate': analytics.win_rate,
                    'total_profit': analytics.total_profit,
                    'profit_factor': analytics.profit_factor,
                    'max_drawdown': analytics.max_loss / analytics.total_profit if analytics.total_profit != 0 else 0
                }
            else:
                analytics_dict = {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_profit': 0,
                    'profit_factor': 0,
                    'max_drawdown': 0
                }
            
            return web.json_response(analytics_dict)
            
        except Exception as e:
            self.logger.error(f"Analytics API error: {str(e)}")
            return web.json_response({'error': str(e)}, status=500)
