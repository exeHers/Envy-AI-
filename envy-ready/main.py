"""
Main entry point that starts both the assistant and web dashboard.
"""
import asyncio
import logging
import yaml
import os
import sys
from pathlib import Path
import uvicorn
from multiprocessing import Process

from envy import EnvyAssistant
from web.dashboard import WebDashboard

logger = logging.getLogger(__name__)


async def run_assistant(config_path: str):
    """Run the assistant in async mode."""
    assistant = EnvyAssistant(config_path)
    await assistant.start()


def run_web_dashboard(config_path: str, host: str = '127.0.0.1', port: int = 8080):
    """Run web dashboard in separate process."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize services
    from services.llm_adapter import LLMAdapter
    from services.router import Router
    from services.skill_manager import SkillManager
    from services.tts_service import TTSService
    
    async def init_services():
        llm_adapter = LLMAdapter(config)
        await llm_adapter.start()
        
        skills_dir = os.path.join(os.path.dirname(__file__), 'skills')
        skill_manager = SkillManager(config, skills_dir)
        skill_manager.load_skills()
        
        router = Router(config, llm_adapter, skill_manager)
        await router.start()
        
        tts_service = TTSService(config)
        await tts_service.start()
        
        dashboard = WebDashboard(config, router, tts_service, skill_manager)
        return dashboard
    
    # Run dashboard
    async def start_dashboard():
        dashboard = await init_services()
        app = dashboard.get_app()
        config_obj = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config_obj)
        await server.serve()
    
    asyncio.run(start_dashboard())


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Envy Personal Assistant')
    parser.add_argument('--config', default='config/envy.yaml', help='Config file path')
    parser.add_argument('--profile', choices=['low', 'balanced', 'power'], help='Resource profile')
    parser.add_argument('--no-gui', action='store_true', help='Run without web dashboard')
    parser.add_argument('--web-only', action='store_true', help='Run only web dashboard')
    parser.add_argument('--host', default='127.0.0.1', help='Web dashboard host')
    parser.add_argument('--port', type=int, default=8080, help='Web dashboard port')
    args = parser.parse_args()
    
    if args.web_only:
        # Run only web dashboard
        logger.info("Starting web dashboard only...")
        run_web_dashboard(args.config, args.host, args.port)
    else:
        # Run assistant (and optionally web dashboard)
        if not args.no_gui:
            # Start web dashboard in background
            web_process = Process(target=run_web_dashboard, args=(args.config, args.host, args.port))
            web_process.start()
            logger.info(f"Web dashboard started at http://{args.host}:{args.port}")
        
        # Run assistant
        try:
            asyncio.run(run_assistant(args.config))
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            if not args.no_gui:
                web_process.terminate()


if __name__ == '__main__':
    main()
