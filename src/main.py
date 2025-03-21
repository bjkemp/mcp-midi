#!/usr/bin/env python3
"""
Main entry point for the MCP MIDI project
"""
import argparse
import logging
import multiprocessing
import os
import signal
import sys
import time
from typing import Dict, List, Optional, Any

from claude_client import ClaudeClient
import uvicorn
from server import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_midi_main")

# Global state
server_process = None
claude_client = None


def start_server(host: str, port: int, debug: bool = False):
    """Start the MCP MIDI server in a separate process
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    if debug:
        log_level = "debug"
    else:
        log_level = "info"
    
    uvicorn.run(app, host=host, port=port, log_level=log_level)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MCP MIDI Bridge for Claude")
    
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--server-only", action="store_true",
                        help="Run in server-only mode without Claude client")
    parser.add_argument("--mcp-mode", action="store_true",
                        help="Run in MCP mode for Claude Desktop integration")
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Run the server in a separate process
    server_process = multiprocessing.Process(
        target=start_server,
        args=(args.host, args.port, args.debug)
    )
    server_process.start()
    
    try:
        if args.mcp_mode:
            # MCP mode for Claude Desktop integration
            logger.info(f"MCP MIDI Server running in MCP mode at http://{args.host}:{args.port}")
            logger.info("Ready for Claude Desktop integration")
            server_process.join()
        elif not args.server_only:
            # Initialize Claude client
            claude_client = ClaudeClient(f"http://{args.host}:{args.port}")
            
            # Example of Claude client usage
            logger.info("MCP MIDI Bridge is running")
            logger.info("Claude can now send MIDI commands via formatted code blocks")
            
            # Keep the main process running
            while True:
                time.sleep(1)
        else:
            # Keep the main process running in server-only mode
            logger.info(f"MCP MIDI Server running at http://{args.host}:{args.port}")
            server_process.join()
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        if server_process and server_process.is_alive():
            server_process.terminate()
            server_process.join()


if __name__ == "__main__":
    # Note: For better compatibility, run with: uv run python -m src.main
    main()
