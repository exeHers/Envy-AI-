"""
Base service class for Envy microservices.
"""
import asyncio
import logging
import signal
import sys
from abc import ABC, abstractmethod
from typing import Optional
import psutil
import os

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all Envy services."""
    
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.running = False
        self.process = None
        
    @abstractmethod
    async def start(self):
        """Start the service."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the service."""
        pass
    
    def check_resource_limits(self):
        """Check if service is within resource limits."""
        profile = self.config.get('profile', 'balanced')
        limits = self.config.get('limits', {}).get(profile, {})
        
        if not limits:
            return True
        
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        max_cpu = limits.get('max_cpu_percent', 100)
        max_ram = limits.get('max_ram_mb', 8192)
        
        if cpu_percent > max_cpu:
            logger.warning(f"{self.name} CPU usage {cpu_percent:.1f}% exceeds limit {max_cpu}%")
            return False
        
        if memory_mb > max_ram:
            logger.warning(f"{self.name} RAM usage {memory_mb:.1f}MB exceeds limit {max_ram}MB")
            return False
        
        return True
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        def signal_handler(sig, frame):
            logger.info(f"{self.name} received shutdown signal")
            asyncio.create_task(self.stop())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
