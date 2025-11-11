"""Utility functions for Envy."""
import logging
import sys
from pathlib import Path
from typing import Optional
import psutil


def setup_logging(config) -> logging.Logger:
    """Set up logging based on configuration."""
    log_file = Path(config.logging.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("envy")
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def check_resources(config) -> dict:
    """Check current resource usage."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    resources = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_mb': memory.used / (1024 * 1024),
        'gpu_available': False,
        'gpu_memory_mb': 0
    }
    
    # Try to detect GPU
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            resources['gpu_available'] = True
            resources['gpu_memory_mb'] = float(result.stdout.strip().split('\n')[0])
    except:
        pass
    
    return resources


def ensure_model_path(model_path: str) -> Path:
    """Ensure model path exists, create if needed."""
    path = Path(model_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def format_response(text: str, persona_config) -> str:
    """Format response based on persona configuration."""
    name = persona_config.name
    
    if persona_config.verbosity == "concise":
        # Keep it short
        if len(text) > 200:
            text = text[:197] + "..."
    
    # Add sardonic touch if enabled
    if persona_config.sardonic_level > 0.5:
        # Add slight sarcasm (keep it minimal and safe)
        pass  # Implement if needed, but keep it professional
    
    return text
