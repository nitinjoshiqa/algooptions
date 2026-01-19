# AlgoOptions Automation Guide

## Overview
This guide covers automating the screener to run at regular intervals (5-60 minutes) with configurable settings, monitoring, and logging.

---

## Architecture

### Components
1. **Main Screener** (`nifty_bearnness_v2.py`)
   - Core logic: scoring, HTML generation, CSV export
   - Command-line interface for manual runs
   
2. **Configuration System** (`config/scheduler_config.json`)
   - Interval settings (5-60 minutes)
   - Universe selection (nifty100, banknifty, nifty)
   - Output formats (html, csv, both)
   - Logging level

3. **Scheduler** (`scheduler.py`)
   - APScheduler for background jobs
   - Auto-starts on system boot (Windows Task Scheduler)
   - Graceful shutdown
   - Error handling & retry logic

4. **Logging System**
   - Output: `logs/scheduler.log`
   - Rotation: daily with 7-day retention
   - Levels: DEBUG, INFO, WARNING, ERROR

---

## Installation

### Step 1: Install Dependencies
```bash
pip install apscheduler
```

### Step 2: Create Configuration File
```bash
# Already created at config/scheduler_config.json
```

### Step 3: Verify Setup
```bash
# Test screener manual run
python nifty_bearnness_v2.py --universe nifty100 --mode swing --screener-format html --force-yf

# Test scheduler
python scheduler.py --test
```

---

## Configuration

### `config/scheduler_config.json`

```json
{
    "scheduler": {
        "enabled": true,
        "interval_minutes": 15,
        "start_time": "09:15",
        "end_time": "15:30",
        "skip_weekends": true,
        "max_retries": 3,
        "retry_delay_seconds": 30
    },
    "screener": {
        "universes": ["nifty100"],
        "mode": "swing",
        "force_yf": true,
        "parallel_workers": 8,
        "output_formats": ["html", "csv"]
    },
    "logging": {
        "level": "INFO",
        "max_backup_days": 7,
        "log_file": "logs/scheduler.log"
    }
}
```

### Configuration Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `interval_minutes` | int | 15 | Run screener every N minutes |
| `start_time` | string | "09:15" | Only run after market open (HH:MM format) |
| `end_time` | string | "15:30" | Stop running after market close |
| `skip_weekends` | bool | true | Don't run on Saturday/Sunday |
| `enabled` | bool | true | Enable/disable scheduler globally |
| `parallel_workers` | int | 8 | Concurrent stock processing |
| `output_formats` | list | ["html"] | Export formats: html, csv, or both |

---

## Usage

### Manual Run (One-Time)
```bash
# Run screener once
python nifty_bearnness_v2.py --universe nifty100 --mode swing --screener-format html --force-yf
```

### Start Scheduler
```bash
# Start background scheduler (runs indefinitely)
python scheduler.py --start

# Start with custom config
python scheduler.py --start --config config/scheduler_config.json
```

### Stop Scheduler
```bash
# Gracefully shutdown
python scheduler.py --stop

# Kill immediately (not recommended)
python scheduler.py --kill
```

### Check Status
```bash
python scheduler.py --status

# Output:
# Scheduler Status: RUNNING
# Next run: 2026-01-19 16:30:00
# Total runs: 42
# Last run: 2026-01-19 16:15:00 (SUCCESS)
# Last error: None
```

### View Logs
```bash
# View recent activity
tail -50 logs/scheduler.log

# Watch real-time
python -c "import subprocess; subprocess.run(['tail', '-f', 'logs/scheduler.log'])"
```

---

## Setting Up Windows Task Scheduler (Production)

For production, use Windows Task Scheduler to ensure the screener runs even if VS Code is closed.

### Create Scheduled Task (PowerShell as Administrator)

```powershell
# Define task properties
$TaskName = "AlgoOptions-Screener"
$TaskDescription = "Automated stock screener - runs every 15 minutes"
$PythonPath = "D:\DreamProject\algooptions\.venv\Scripts\python.exe"
$ScriptPath = "D:\DreamProject\algooptions\scheduler.py"
$WorkDir = "D:\DreamProject\algooptions"

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "scheduler.py --start" `
    -WorkingDirectory $WorkDir

# Create trigger (run at system startup)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 24)

# Create principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

# Register task
Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description $TaskDescription `
    -Force
```

### Verify Task
```powershell
# List task
Get-ScheduledTask -TaskName "AlgoOptions-Screener"

# Run immediately
Start-ScheduledTask -TaskName "AlgoOptions-Screener"

# View history
Get-ScheduledTaskInfo -TaskName "AlgoOptions-Screener"
```

### Remove Task
```powershell
Unregister-ScheduledTask -TaskName "AlgoOptions-Screener" -Confirm:$false
```

---

## Monitoring

### Log Files
- **Location:** `logs/scheduler.log`
- **Format:** `[TIMESTAMP] [LEVEL] [EVENT] [DETAILS]`
- **Rotation:** Daily, kept for 7 days

### Example Log Output
```
[2026-01-19 09:15:00] [INFO] Scheduler started
[2026-01-19 09:15:00] [INFO] Config loaded: interval=15min, universes=['nifty100']
[2026-01-19 09:30:00] [INFO] Run #1 started
[2026-01-19 09:34:23] [INFO] Processed 106 stocks
[2026-01-19 09:34:23] [INFO] Generated HTML: nifty_bearnness_20260119_093423.html
[2026-01-19 09:34:23] [INFO] Run #1 completed (4m 23s)
[2026-01-19 09:45:00] [INFO] Run #2 started
```

### Performance Tracking
Each run generates a performance summary:
```
{
    "run_id": 1,
    "timestamp": "2026-01-19T09:30:00Z",
    "duration_seconds": 263,
    "stocks_processed": 106,
    "bullish_picks": 42,
    "bearish_picks": 28,
    "neutral_picks": 36,
    "status": "SUCCESS",
    "files_generated": ["nifty_bearnness.html", "nifty_bearnness.csv"]
}
```

---

## Troubleshooting

### Issue: "Port already in use" or "Address already in use"
**Cause:** Scheduler already running
```bash
python scheduler.py --stop
python scheduler.py --start
```

### Issue: Permission Denied (Windows)
**Cause:** Running without admin privileges
```bash
# Run PowerShell as Administrator
python scheduler.py --start
```

### Issue: Data is stale (older than interval)
**Cause:** Network connectivity issues or API timeouts
```bash
# Check logs for errors
tail -20 logs/scheduler.log

# Verify internet connection
ping www.google.com
```

### Issue: No HTML files being generated
**Cause:** Output directory permissions or config error
```bash
# Verify config
python scheduler.py --config-validate

# Check directory permissions
ls -la reports/
```

### Issue: Memory usage keeps growing
**Cause:** Too many workers or intervals too short
```bash
# Reduce workers in config
"parallel_workers": 4

# Increase interval
"interval_minutes": 30
```

---

## Best Practices

1. **Market Hours Only:** Set `start_time` and `end_time` to market hours
   - NSE market: 09:15 - 15:30

2. **Interval Timing:** 15-30 minutes recommended
   - Too frequent: 5 min (high API load)
   - Too infrequent: 60+ min (stale data)

3. **Backup Strategy:**
   - HTML reports auto-saved to `reports/` with timestamps
   - CSV exports saved alongside HTML
   - Keep 30 days of backups

4. **Monitoring:**
   - Check logs daily for errors
   - Monitor disk space (reports accumulate)
   - Track performance metrics

5. **Updating Configuration:**
   - Edit `config/scheduler_config.json`
   - Restart scheduler: `python scheduler.py --stop && python scheduler.py --start`
   - No code changes needed

---

## Advanced Features

### Run Multiple Universes in Sequence
```json
{
    "screener": {
        "universes": ["nifty100", "banknifty", "nifty"],
        "mode": "swing"
    }
}
```
Will run: NIFTY100 → BANKNIFTY → NIFTY, each every 15 minutes

### Custom Time Ranges
```json
{
    "scheduler": {
        "start_time": "09:30",
        "end_time": "15:00",
        "interval_minutes": 30
    }
}
```
Runs at: 09:30, 10:00, 10:30, ..., 14:30, 15:00

### Error Recovery
Automatic retry with exponential backoff:
- Retry 1: 30 seconds later
- Retry 2: 60 seconds later  
- Retry 3: 120 seconds later

---

## FAQ

**Q: Can I run screener every 5 minutes?**
A: Technically yes, but not recommended. Yahoo Finance has rate limits (~2000 requests/day). 106 stocks × 3 timeframes = 318 requests per run. Every 5 min = 288 runs/day ≈ 91K requests. Better: use 15-30 minute interval.

**Q: Does scheduler survive reboot?**
A: Only with Windows Task Scheduler setup. Python scheduler terminates on shutdown.

**Q: Can I modify config while running?**
A: No, restart scheduler to apply changes. Edit config → `python scheduler.py --stop` → `python scheduler.py --start`

**Q: How much disk space do reports use?**
A: ~200-300 KB per run (HTML + CSV). 15-min interval = 4 runs/hour = 0.8-1.2 MB/hour = 20-30 MB/day. Keep 30 days = ~600-900 MB.

**Q: Can I run on Linux/Mac?**
A: Yes! APScheduler is cross-platform. Use cron instead of Task Scheduler:
```bash
*/15 * * * * cd /path/to/algooptions && python scheduler.py --run-once
```

---

## Next Steps

1. ✅ Review this guide
2. ⏳ Create `config/scheduler_config.json`
3. ⏳ Create `scheduler.py`
4. ⏳ Test manual run
5. ⏳ Start scheduler and monitor logs
6. ⏳ Set up Windows Task Scheduler (optional, for production)

