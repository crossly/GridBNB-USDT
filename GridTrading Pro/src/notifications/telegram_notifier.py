"""
Telegram notifier implementation for GridTrading Pro.

This module provides Telegram Bot integration for sending trading notifications,
alerts, and system status updates with support for message formatting and
error handling.
"""

import asyncio
import aiohttp
from typing import Dict, Optional, Any
import json
from urllib.parse import quote

from .base_notifier import BaseNotifier, NotificationPriority
from ..utils.logger import get_logger
from ..utils.validators import validate_telegram_config
from ..config.constants import MAX_MESSAGE_LENGTH, NOTIFICATION_RETRY_ATTEMPTS


class TelegramNotifier(BaseNotifier):
    """Telegram notification implementation."""
    
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        enabled: bool = True,
        notification_levels: list = None,
        rate_limit: int = 20,  # Telegram allows 30 messages per second
        **kwargs
    ):
        """Initialize Telegram notifier."""
        super().__init__(enabled, notification_levels, rate_limit, **kwargs)
        
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = get_logger("TelegramNotifier")
        
        # Validate configuration
        if not validate_telegram_config(bot_token, chat_id):
            raise ValueError("Invalid Telegram configuration")
        
        # Telegram API settings
        self.api_base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.timeout = 30
        self.session = None
        
        # Message formatting
        self.parse_mode = "HTML"  # HTML or Markdown
        self.disable_web_page_preview = True
        
        self.logger.info("Telegram notifier initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _send_telegram_message(
        self,
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Send message via Telegram API."""
        session = await self._get_session()
        
        # Prepare message data
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode or self.parse_mode,
            'disable_web_page_preview': disable_web_page_preview
        }
        
        # Add any additional parameters
        data.update(kwargs)
        
        url = f"{self.api_base_url}/sendMessage"
        
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                
                if response.status == 200 and result.get('ok'):
                    return result
                else:
                    error_msg = result.get('description', 'Unknown error')
                    raise Exception(f"Telegram API error: {error_msg}")
                    
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}")
            raise
    
    def _format_message_html(self, text: str) -> str:
        """Format message for HTML parsing."""
        # Escape HTML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        # Apply basic formatting
        text = text.replace('**', '<b>').replace('**', '</b>')  # Bold
        text = text.replace('*', '<i>').replace('*', '</i>')    # Italic
        text = text.replace('`', '<code>').replace('`', '</code>')  # Code
        
        return text
    
    def _split_long_message(self, text: str) -> list:
        """Split long messages into chunks."""
        if len(text) <= MAX_MESSAGE_LENGTH:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        for line in text.split('\n'):
            if len(current_chunk) + len(line) + 1 <= MAX_MESSAGE_LENGTH:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.rstrip())
        
        return chunks
    
    async def send_message(
        self,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> bool:
        """Send a notification message."""
        if not self.is_enabled():
            return False
        
        if not self._check_rate_limit():
            return False
        
        try:
            # Format message
            formatted_message = self._format_message_html(message)
            
            # Split if too long
            message_chunks = self._split_long_message(formatted_message)
            
            # Send each chunk
            for i, chunk in enumerate(message_chunks):
                if i > 0:
                    # Add small delay between chunks
                    await asyncio.sleep(1)
                
                # Add chunk indicator for multi-part messages
                if len(message_chunks) > 1:
                    chunk_header = f"📄 Part {i+1}/{len(message_chunks)}\n"
                    chunk = chunk_header + chunk
                
                # Retry logic
                for attempt in range(NOTIFICATION_RETRY_ATTEMPTS):
                    try:
                        await self._send_telegram_message(chunk, **kwargs)
                        break
                    except Exception as e:
                        if attempt == NOTIFICATION_RETRY_ATTEMPTS - 1:
                            self.logger.error(f"Failed to send message after {NOTIFICATION_RETRY_ATTEMPTS} attempts: {str(e)}")
                            return False
                        
                        # Exponential backoff
                        await asyncio.sleep(2 ** attempt)
            
            self.logger.debug(f"Telegram message sent successfully (priority: {priority.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}")
            return False
    
    async def send_formatted_message(
        self,
        title: str,
        content: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> bool:
        """Send a formatted notification message."""
        # Create formatted message
        priority_emoji = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.NORMAL: "📢",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.CRITICAL: "🚨"
        }
        
        emoji = priority_emoji.get(priority, "📢")
        
        formatted_message = (
            f"{emoji} <b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{content}\n"
            f"⏰ {self._get_timestamp()}"
        )
        
        return await self.send_message(formatted_message, priority, **kwargs)
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp."""
        import time
        return time.strftime('%Y-%m-%d %H:%M:%S')
    
    async def send_photo(
        self,
        photo_path: str,
        caption: str = "",
        **kwargs
    ) -> bool:
        """Send photo with optional caption."""
        if not self.is_enabled():
            return False
        
        try:
            session = await self._get_session()
            
            with open(photo_path, 'rb') as photo:
                data = aiohttp.FormData()
                data.add_field('chat_id', self.chat_id)
                data.add_field('photo', photo, filename='chart.png')
                
                if caption:
                    data.add_field('caption', caption)
                    data.add_field('parse_mode', self.parse_mode)
                
                url = f"{self.api_base_url}/sendPhoto"
                
                async with session.post(url, data=data) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get('ok'):
                        self.logger.debug("Photo sent successfully")
                        return True
                    else:
                        error_msg = result.get('description', 'Unknown error')
                        self.logger.error(f"Failed to send photo: {error_msg}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send photo: {str(e)}")
            return False
    
    async def send_document(
        self,
        document_path: str,
        caption: str = "",
        **kwargs
    ) -> bool:
        """Send document with optional caption."""
        if not self.is_enabled():
            return False
        
        try:
            session = await self._get_session()
            
            with open(document_path, 'rb') as document:
                data = aiohttp.FormData()
                data.add_field('chat_id', self.chat_id)
                data.add_field('document', document)
                
                if caption:
                    data.add_field('caption', caption)
                    data.add_field('parse_mode', self.parse_mode)
                
                url = f"{self.api_base_url}/sendDocument"
                
                async with session.post(url, data=data) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get('ok'):
                        self.logger.debug("Document sent successfully")
                        return True
                    else:
                        error_msg = result.get('description', 'Unknown error')
                        self.logger.error(f"Failed to send document: {error_msg}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send document: {str(e)}")
            return False
    
    async def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information."""
        try:
            session = await self._get_session()
            url = f"{self.api_base_url}/getMe"
            
            async with session.get(url) as response:
                result = await response.json()
                
                if response.status == 200 and result.get('ok'):
                    return result.get('result', {})
                else:
                    error_msg = result.get('description', 'Unknown error')
                    raise Exception(f"Failed to get bot info: {error_msg}")
                    
        except Exception as e:
            self.logger.error(f"Failed to get bot info: {str(e)}")
            return {}
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        try:
            bot_info = await self.get_bot_info()
            if bot_info:
                self.logger.info(f"Telegram bot connected: {bot_info.get('username', 'Unknown')}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Telegram connection test failed: {str(e)}")
            return False
    
    async def close(self):
        """Close Telegram notifier."""
        await super().close()
        
        if self.session and not self.session.closed:
            await self.session.close()
        
        self.logger.info("Telegram notifier closed")
