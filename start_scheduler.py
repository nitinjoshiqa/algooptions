#!/usr/bin/env python3
"""
Simple scheduler launcher for AlgoOptions
Runs the screener every 15 minutes during market hours
"""

import sys
import os
from pathlib import Path

# Add scripts to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

def main():
    """Launch the scheduler"""
    try:
        from scheduling.scheduler import main as scheduler_main
        # Pass --start argument to scheduler
        sys.argv = ["scheduler.py", "--start"]
        scheduler_main()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
    except Exception as e:
        print(f"Error starting scheduler: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())