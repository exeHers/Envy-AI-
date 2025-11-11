#!/usr/bin/env python3
"""Main entry point for Envy."""
import sys
import os
from pathlib import Path

# Add services to path
envy_dir = Path(__file__).parent
sys.path.insert(0, str(envy_dir))
sys.path.insert(0, str(envy_dir / "services"))
sys.path.insert(0, str(envy_dir / "skills"))

import logging
import uvicorn
import threading
from services.config_loader import Config
from services.orchestrator import EnvyOrchestrator
from web.dashboard import create_app


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Envy Personal Assistant")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--profile", type=str, default="balanced", 
                       choices=["low", "balanced", "power"],
                       help="Resource profile")
    parser.add_argument("--no-gui", action="store_true", 
                       help="Run without web dashboard")
    parser.add_argument("--port", type=int, default=8080,
                       help="Web dashboard port")
    
    args = parser.parse_args()
    
    # Change to envy directory
    os.chdir(envy_dir)
    
    # Create necessary directories
    Path("artifacts").mkdir(exist_ok=True)
    Path("workspace").mkdir(exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('artifacts/envy.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Load config
    config = Config(args.config)
    config.apply_profile(args.profile)
    
    # Create orchestrator
    orchestrator = EnvyOrchestrator(args.config, args.profile)
    
    # Start web dashboard if not disabled
    if not args.no_gui:
        app = create_app(config, orchestrator)
        web_port = args.port or config.get("web.port", 8080)
        
        def run_web():
            uvicorn.run(app, host=config.get("web.host", "127.0.0.1"), 
                       port=web_port, log_level="info")
        
        web_thread = threading.Thread(target=run_web, daemon=True)
        web_thread.start()
        logger.info(f"Web dashboard started on http://127.0.0.1:{web_port}")
    
    # Start orchestrator (blocks)
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        orchestrator.stop()


if __name__ == "__main__":
    main()
