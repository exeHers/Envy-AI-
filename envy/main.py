"""Main entry point for Envy."""
import sys
import argparse
import logging
import threading
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.orchestrator import EnvyOrchestrator
from web.dashboard import WebDashboard


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Envy Personal Assistant")
    parser.add_argument("--config", default="config/envy.yaml", help="Config file path")
    parser.add_argument("--profile", choices=["low", "balanced", "power"], help="Resource profile")
    parser.add_argument("--no-gui", action="store_true", help="Run without web dashboard")
    parser.add_argument("--web-only", action="store_true", help="Run only web dashboard")
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        print("Using default configuration...")
    
    orchestrator = EnvyOrchestrator(str(config_path))
    
    if args.profile:
        orchestrator.config.profile = args.profile
    
    if args.web_only:
        # Web dashboard only mode
        dashboard = WebDashboard(orchestrator.config, orchestrator)
        dashboard.run()
    else:
        # Start orchestrator
        if not orchestrator.start():
            print("Failed to start Envy")
            sys.exit(1)
        
        # Start web dashboard in background if not disabled
        if not args.no_gui:
            dashboard = WebDashboard(orchestrator.config, orchestrator)
            dashboard_thread = threading.Thread(target=dashboard.run, daemon=True)
            dashboard_thread.start()
            print(f"Web dashboard available at http://localhost:{orchestrator.config.web.port}")
        
        print("Envy is running. Press Ctrl+C to stop.")
        
        try:
            # Keep running
            while orchestrator.is_running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping Envy...")
            orchestrator.stop()
            print("Envy stopped.")


if __name__ == "__main__":
    main()
