"""
Configuration management for AlgoOptions scheduler
Loads and validates configuration from JSON files
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import time

logger = logging.getLogger(__name__)


class SchedulerConfig:
    """Manages scheduler configuration"""
    
    DEFAULT_CONFIG = {
        "scheduler": {
            "enabled": True,
            "interval_minutes": 15,
            "start_time": "09:15",
            "end_time": "15:30",
            "skip_weekends": True,
            "max_retries": 3,
            "retry_delay_seconds": 30
        },
        "screener": {
            "universes": ["nifty100"],
            "mode": "swing",
            "force_yf": True,
            "parallel_workers": 8,
            "output_formats": ["html", "csv"]
        },
        "logging": {
            "level": "INFO",
            "max_backup_days": 7,
            "log_file": "logs/scheduler.log"
        }
    }
    
    def __init__(self, config_file: str = None):
        """Initialize configuration from file or defaults"""
        self.config_file = config_file or "config/scheduler_config.json"
        self.config = self.load_config()
        self.validate()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {self.config_file}. Using defaults.")
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_file}")
            return self._merge_defaults(config)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_file}: {e}")
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_defaults(self, config: Dict) -> Dict:
        """Merge provided config with defaults"""
        merged = self.DEFAULT_CONFIG.copy()
        if "scheduler" in config:
            merged["scheduler"].update(config["scheduler"])
        if "screener" in config:
            merged["screener"].update(config["screener"])
        if "logging" in config:
            merged["logging"].update(config["logging"])
        return merged
    
    def validate(self):
        """Validate configuration values"""
        errors = []
        
        # Validate interval
        interval = self.config["scheduler"]["interval_minutes"]
        if not (5 <= interval <= 1440):
            errors.append(f"interval_minutes must be 5-1440, got {interval}")
        
        # Validate time format
        try:
            start = self.config["scheduler"]["start_time"]
            end = self.config["scheduler"]["end_time"]
            time.fromisoformat(start)
            time.fromisoformat(end)
        except ValueError as e:
            errors.append(f"Invalid time format (use HH:MM): {e}")
        
        # Validate universes
        valid_universes = ["nifty", "nifty50", "nifty100", "nifty200", "nifty500", "banknifty"]
        universes = self.config["screener"]["universes"]
        for u in universes:
            if u not in valid_universes:
                errors.append(f"Invalid universe: {u}. Must be one of {valid_universes}")
        
        # Validate output formats
        valid_formats = ["html", "csv"]
        formats = self.config["screener"]["output_formats"]
        for fmt in formats:
            if fmt not in valid_formats:
                errors.append(f"Invalid output format: {fmt}. Must be 'html' or 'csv'")
        
        # Validate parallel workers
        workers = self.config["screener"]["parallel_workers"]
        if not (1 <= workers <= 32):
            errors.append(f"parallel_workers must be 1-32, got {workers}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        level = self.config["logging"]["level"]
        if level not in valid_levels:
            errors.append(f"Invalid log level: {level}. Must be one of {valid_levels}")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        logger.info("Configuration validation passed")
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """Get scheduler settings"""
        return self.config["scheduler"]
    
    def get_screener_config(self) -> Dict[str, Any]:
        """Get screener settings"""
        return self.config["screener"]
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging settings"""
        return self.config["logging"]
    
    def get_cli_args(self) -> List[str]:
        """Build CLI arguments for screener from config"""
        args = ["nifty_bearnness_v2.py"]
        
        screener = self.config["screener"]
        
        # Add first universe (handle multiple in loop)
        if screener["universes"]:
            args.extend(["--universe", screener["universes"][0]])
        
        # Add mode
        args.extend(["--mode", screener["mode"]])
        
        # Add optional flags
        if screener["force_yf"]:
            args.append("--force-yf")
        
        if "html" in screener["output_formats"]:
            args.extend(["--screener-format", "html"])
        
        if screener["parallel_workers"] > 1:
            args.extend(["--parallel", str(screener["parallel_workers"])])
        
        return args
    
    def to_dict(self) -> Dict[str, Any]:
        """Get entire configuration as dictionary"""
        return self.config.copy()
    
    def save(self, path: str = None):
        """Save current configuration to file"""
        save_path = path or self.config_file
        try:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise


if __name__ == "__main__":
    # Test configuration
    config = SchedulerConfig()
    print("✅ Configuration loaded successfully")
    print(f"Interval: {config.get_scheduler_config()['interval_minutes']} minutes")
    print(f"Universes: {config.get_screener_config()['universes']}")
    print(f"CLI args: {' '.join(config.get_cli_args())}")
