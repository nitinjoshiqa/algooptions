# AlgoOptions Automation - Quick Start

## 3 Steps to Automate Your Screener

### ✅ Step 1: Configuration (Already Done!)
Your configuration file is ready at: `config/scheduler_config.json`

**Default settings:**
- Runs every **15 minutes**
- Market hours: **09:15 - 15:30**
- Universe: **NIFTY100**
- Output: **HTML + CSV**

### ✅ Step 2: Test Setup
Verify everything works:
```bash
# Test configuration
python scheduler.py --test

# Run screener once
python scheduler.py --run-once

# Check status
python scheduler.py --status
```

### ✅ Step 3: Start Automation

**Option A: Development (Python Scheduler)**
```bash
# Start background scheduler (for testing)
python scheduler.py --start

# Stop with Ctrl+C
```

**Option B: Production (Windows Task Scheduler)**
```powershell
# Run PowerShell as Administrator, then:
$TaskName = "AlgoOptions-Screener"
$PythonPath = "D:\DreamProject\algooptions\.venv\Scripts\python.exe"
$ScriptPath = "D:\DreamProject\algooptions\scheduler.py"
$WorkDir = "D:\DreamProject\algooptions"

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "scheduler.py --start" -WorkingDirectory $WorkDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force
```

---

## Configuration Options

Edit `config/scheduler_config.json` to customize:

```json
{
    "scheduler": {
        "enabled": true,                    // true/false
        "interval_minutes": 15,             // 5-1440
        "start_time": "09:15",              // Market open (HH:MM)
        "end_time": "15:30",                // Market close (HH:MM)
        "skip_weekends": true               // true/false
    },
    "screener": {
        "universes": ["nifty100"],          // nifty, nifty100, banknifty
        "mode": "swing",                    // swing/intraday/positional
        "parallel_workers": 8               // 1-32
    }
}
```

---

## Commands Reference

```bash
# Start scheduler
python scheduler.py --start

# Run once (no scheduling)
python scheduler.py --run-once

# Check status
python scheduler.py --status

# Validate config without running
python scheduler.py --config-validate

# Test everything
python scheduler.py --test

# With custom config file
python scheduler.py --start --config my_config.json
```

---

## Monitoring

### View Live Logs
```bash
# Watch logs in real-time
Get-Content -Path logs/scheduler.log -Wait
```

### Log Locations
- **Main log:** `logs/scheduler.log`
- **State file:** `logs/scheduler_state.json`
- **Reports:** `reports/nifty_bearnness_*.html`

### Example Log Output
```
[2026-01-19 09:15:00] [INFO] Scheduler starting - interval: 15 minutes
[2026-01-19 09:15:00] [INFO] Market hours: 09:15 - 15:30
[2026-01-19 09:30:00] [INFO] Run #1 started
[2026-01-19 09:34:00] [INFO] Run #1 completed successfully
[2026-01-19 09:45:00] [INFO] Run #2 started
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Port already in use" | Scheduler already running - stop it first |
| No files generated | Check logs: `cat logs/scheduler.log` |
| Outside market hours | Scheduler skips before 09:15 and after 15:30 |
| Memory growing | Reduce workers: `"parallel_workers": 4` |
| Slow performance | Increase interval: `"interval_minutes": 30` |

---

## Files Created

```
config/
├── scheduler_config.json      # Configuration (edit this!)
config_manager.py              # Config loader (don't edit)
scheduler.py                   # Scheduler (don't edit)
logs/
├── scheduler.log              # Main log file
└── scheduler_state.json       # Scheduler state
reports/
├── nifty_bearnness_*.html     # Generated reports
└── nifty_bearnness_*.csv      # Generated data
```

---

## Next: Detailed Documentation

For complete details, see: [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)

- Advanced configuration options
- Windows Task Scheduler setup
- Performance optimization
- FAQ & troubleshooting

---

## Need Help?

1. **Test first:** `python scheduler.py --test`
2. **Check logs:** `cat logs/scheduler.log`
3. **Run once:** `python scheduler.py --run-once`
4. **Review guide:** [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)

