#!/usr/bin/env python3
"""
Stop the running scheduler
"""

import os
import signal
import sys
from pathlib import Path

PID_FILE = Path("logs/scheduler.pid")

def main():
    """Stop the scheduler process"""
    if not PID_FILE.exists():
        print("No scheduler PID file found. Scheduler may not be running.")
        return 1

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        print(f"Stopping scheduler (PID: {pid})...")

        # Send SIGTERM to gracefully stop
        os.kill(pid, signal.SIGTERM)

        # Remove PID file
        PID_FILE.unlink()

        print("Scheduler stop signal sent.")
        return 0

    except ProcessLookupError:
        print("Scheduler process not found. Cleaning up PID file.")
        PID_FILE.unlink()
        return 0
    except Exception as e:
        print(f"Error stopping scheduler: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())