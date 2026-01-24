"""
AlgoOptions Background Scheduler
Automatically runs the screener at configured intervals
"""

import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime, time
from typing import Optional
import subprocess
import json

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from config_manager import SchedulerConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/scheduler.log')
    ]
)
logger = logging.getLogger(__name__)


class ScreenerScheduler:
    """Manages background screener execution"""
    
    def __init__(self, config_file: str = "config/scheduler_config.json"):
        """Initialize scheduler with configuration"""
        self.config = SchedulerConfig(config_file)
        self.scheduler = BackgroundScheduler()
        self.run_count = 0
        self.last_run_time = None
        self.last_run_status = None
        self.state_file = "logs/scheduler_state.json"
        
        # Setup logging
        Path("logs").mkdir(exist_ok=True)
        log_level = self.config.get_logging_config()["level"]
        logger.setLevel(log_level)
        
        # Add job event listeners
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        
        logger.info("Scheduler initialized")
    
    def _on_job_executed(self, event):
        """Callback when job completes successfully"""
        self.last_run_status = "SUCCESS"
        self.run_count += 1
        self.last_run_time = datetime.now()
        self._save_state()
        logger.info(f"Run #{self.run_count} completed successfully")
    
    def _on_job_error(self, event):
        """Callback when job fails"""
        self.last_run_status = "FAILED"
        self.last_run_time = datetime.now()
        self._save_state()
        logger.error(f"Run #{self.run_count} failed: {event.exception}")
    
    def _save_state(self):
        """Save scheduler state to file"""
        state = {
            "run_count": self.run_count,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_run_status": self.last_run_status,
            "timestamp": datetime.now().isoformat()
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _load_state(self):
        """Load scheduler state from file"""
        if not Path(self.state_file).exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            self.run_count = state.get("run_count", 0)
            self.last_run_status = state.get("last_run_status")
            if state.get("last_run_time"):
                self.last_run_time = datetime.fromisoformat(state["last_run_time"])
            logger.info(f"Loaded previous state: {self.run_count} runs, last status: {self.last_run_status}")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def _is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        config = self.config.get_scheduler_config()
        
        if config["skip_weekends"]:
            if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
        
        current_time = datetime.now().time()
        start_time = datetime.strptime(config["start_time"], "%H:%M").time()
        end_time = datetime.strptime(config["end_time"], "%H:%M").time()
        
        return start_time <= current_time <= end_time
    
    def _run_screener(self):
        """Execute the screener"""
        logger.info("=" * 60)
        logger.info(f"Run #{self.run_count + 1} started")
        
        if not self._is_market_hours():
            logger.info("Outside market hours, skipping run")
            self.run_count += 1
            return
        
        try:
            config = self.config.get_screener_config()
            args = self.config.get_cli_args()
            
            # Build full command
            cmd = f".venv\\Scripts\\python.exe {' '.join(args)}"
            logger.info(f"Executing: {cmd}")
            
            # Run screener
            start_time = datetime.now()
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent)
            )
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                logger.info(f"Run completed successfully in {duration:.1f}s")
                # Log output summary
                if "Actionable picks" in result.stdout:
                    logger.info("Generated actionable picks report")
            else:
                logger.error(f"Screener failed with code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr[:200]}")
        
        except Exception as e:
            logger.error(f"Exception running screener: {e}")
            raise
    
    def start(self):
        """Start the background scheduler"""
        config = self.config.get_scheduler_config()
        
        if not config["enabled"]:
            logger.warning("Scheduler is disabled in configuration")
            return
        
        self._load_state()
        
        try:
            interval = config["interval_minutes"]
            
            # Add job with interval trigger
            self.scheduler.add_job(
                self._run_screener,
                IntervalTrigger(minutes=interval),
                id='screener_job',
                name='Stock Screener',
                replace_existing=True
            )
            
            logger.info(f"Scheduler starting - interval: {interval} minutes")
            logger.info(f"Market hours: {config['start_time']} - {config['end_time']}")
            logger.info(f"Skip weekends: {config['skip_weekends']}")
            
            self.scheduler.start()
            logger.info(f"[OK] Scheduler is now running")
            
            # Keep alive
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                self.stop()
        
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler gracefully"""
        if self.scheduler.running:
            logger.info("Stopping scheduler...")
            self.scheduler.shutdown(wait=True)
            logger.info("[OK] Scheduler stopped")
    
    def get_status(self) -> dict:
        """Get current scheduler status"""
        next_run_time = None
        if self.scheduler.running and self.scheduler.get_jobs():
            job = self.scheduler.get_jobs()[0]
            next_run_time = str(job.next_run_time) if job.next_run_time else None
        
        return {
            "status": "RUNNING" if self.scheduler.running else "STOPPED",
            "run_count": self.run_count,
            "last_run_time": str(self.last_run_time) if self.last_run_time else None,
            "last_run_status": self.last_run_status,
            "next_run_time": next_run_time,
            "config": self.config.to_dict()
        }
    
    def validate_config(self):
        """Validate configuration without running"""
        try:
            self.config.validate()
            logger.info("[OK] Configuration is valid")
            return True
        except ValueError as e:
            logger.error(f"[ERROR] Configuration error: {e}")
            return False
    
    def run_once(self):
        """Run screener once immediately"""
        logger.info("Running screener once (not scheduled)")
        self._run_screener()
        logger.info("Single run completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AlgoOptions Screener Scheduler")
    parser.add_argument("--start", action="store_true", help="Start background scheduler")
    parser.add_argument("--stop", action="store_true", help="Stop background scheduler")
    parser.add_argument("--status", action="store_true", help="Show scheduler status")
    parser.add_argument("--run-once", action="store_true", help="Run screener once immediately")
    parser.add_argument("--config-validate", action="store_true", help="Validate configuration")
    parser.add_argument("--config", default="config/scheduler_config.json", help="Configuration file path")
    parser.add_argument("--test", action="store_true", help="Test configuration without running")
    
    args = parser.parse_args()
    
    try:
        scheduler = ScreenerScheduler(args.config)
        
        if args.test:
            logger.info("Testing configuration...")
            if scheduler.validate_config():
                logger.info("[OK] All checks passed. Ready to run!")
            sys.exit(0)
        
        elif args.config_validate:
            scheduler.validate_config()
            sys.exit(0)
        
        elif args.start:
            scheduler.start()
        
        elif args.stop:
            # Note: Can't stop running scheduler from another process easily
            # This is for demonstration
            logger.info("To stop scheduler: press Ctrl+C in the running window")
            sys.exit(1)
        
        elif args.status:
            status = scheduler.get_status()
            print("\n" + "=" * 60)
            print("SCHEDULER STATUS")
            print("=" * 60)
            print(f"Status:        {status['status']}")
            print(f"Run Count:     {status['run_count']}")
            print(f"Last Run:      {status['last_run_time']}")
            print(f"Last Status:   {status['last_run_status']}")
            print(f"Next Run:      {status['next_run_time']}")
            print("=" * 60 + "\n")
        
        elif args.run_once:
            scheduler.run_once()
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
