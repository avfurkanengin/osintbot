#!/usr/bin/env python3
"""
Combined startup script for Railway deployment
Runs both the API server and Telegram bot worker
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for process management
api_process = None
bot_process = None
shutdown_flag = False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_flag
    logger.info(f"Received signal {signum}, shutting down...")
    shutdown_flag = True
    
    if api_process:
        logger.info("Terminating API server...")
        api_process.terminate()
        try:
            api_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("API server didn't terminate gracefully, killing...")
            api_process.kill()
    
    if bot_process:
        logger.info("Terminating Telegram bot...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("Telegram bot didn't terminate gracefully, killing...")
            bot_process.kill()
    
    logger.info("Shutdown complete")
    sys.exit(0)

def run_api_server():
    """Run the API server"""
    global api_process
    try:
        logger.info("Starting API server...")
        api_process = subprocess.Popen(
            [sys.executable, 'api_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Log API server output
        for line in iter(api_process.stdout.readline, ''):
            if line.strip():
                logger.info(f"[API] {line.strip()}")
            if shutdown_flag:
                break
                
        api_process.wait()
        
    except Exception as e:
        logger.error(f"Error running API server: {e}")
        if api_process:
            api_process.terminate()

def run_telegram_bot():
    """Run the Telegram bot"""
    global bot_process
    try:
        # Wait a bit for API server to start
        time.sleep(5)
        
        logger.info("Starting Telegram bot...")
        bot_process = subprocess.Popen(
            [sys.executable, 'main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Log bot output
        for line in iter(bot_process.stdout.readline, ''):
            if line.strip():
                logger.info(f"[BOT] {line.strip()}")
            if shutdown_flag:
                break
                
        bot_process.wait()
        
    except Exception as e:
        logger.error(f"Error running Telegram bot: {e}")
        if bot_process:
            bot_process.terminate()

def main():
    """Main function to start both services"""
    logger.info("Starting OSINT Bot services...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start API server in a separate thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Start Telegram bot in a separate thread
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    try:
        # Keep main thread alive
        while not shutdown_flag:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process and api_process.poll() is not None:
                logger.error("API server process died, restarting...")
                api_thread = threading.Thread(target=run_api_server, daemon=True)
                api_thread.start()
            
            if bot_process and bot_process.poll() is not None:
                logger.error("Telegram bot process died, restarting...")
                bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
                bot_thread.start()
                
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main() 