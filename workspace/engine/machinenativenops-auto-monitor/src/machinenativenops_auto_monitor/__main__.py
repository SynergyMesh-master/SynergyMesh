"""
MachineNativeOps Auto-Monitor - Main Entry Point

Usage:
    python -m machinenativenops_auto_monitor [options]
    
Options:
    --config PATH       Configuration file path (default: /etc/machinenativeops/auto-monitor.yaml)
    --verbose           Enable verbose logging
    --dry-run           Run without actually sending alerts or storing data
    --daemon            Run as daemon process
    
Examples:
    python -m machinenativenops_auto_monitor --config config.yaml
    python -m machinenativenops_auto_monitor --daemon --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

from .app import AutoMonitorApp
from .config import AutoMonitorConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MachineNativeOps Auto-Monitor"
    )
    parser.add_argument(
        "--config",
        default="config/auto-monitor.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode",
        choices=["collect", "alert", "monitor"],
        default="monitor",
        help="Operation mode"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Collection interval in seconds"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    try:
        config = AutoMonitorConfig.from_file(args.config)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {args.config}, using defaults")
        config = AutoMonitorConfig()
    
    # Create and run application
    app = AutoMonitorApp(config)
    
    try:
        if args.daemon:
            logger.info("Running in daemon mode...")
            # TODO: Implement daemon mode
        app.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
