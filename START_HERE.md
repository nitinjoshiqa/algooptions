# ✅ AUTOMATION SETUP COMPLETE

## What You Now Have

### 3 New Files Ready to Use:

1. **`scheduler.py`** - Background task runner
   - Runs screener every 15 minutes (configurable)
   - Market hours aware (09:15-15:30)
   - Logs all activity
   - Can be scheduled with Windows Task Scheduler

2. **`config_manager.py`** - Configuration system
   - Loads settings from JSON
   - Validates all values
   - Builds CLI commands dynamically

3. **`config/scheduler_config.json`** - Your settings
   - Interval: 15 minutes
   - Universes: NIFTY100
   - Format: HTML + CSV
   - ⚠️ **Edit this file to customize!**

### 2 New Documentation Files:

4. **`AUTOMATION_QUICKSTART.md`** - Quick reference (read this first!)
5. **`AUTOMATION_GUIDE.md`** - Complete guide with all details

---

## Quick Start (3 Commands)

### 1️⃣ Test Setup
```bash
python scheduler.py --test
```
Output: `[OK] All checks passed. Ready to run!`

### 2️⃣ Run Once (Test)
```bash
python scheduler.py --run-once
```
This will run the screener immediately and generate a report.

### 3️⃣ Start Automation
```bash
python scheduler.py --start
```
Now it runs automatically every 15 minutes (during market hours). Press **Ctrl+C** to stop.

---

## Customize Your Settings

Edit: `config/scheduler_config.json`

```json
{
    "scheduler": {
        "interval_minutes": 15,      // Change this for different interval
        "start_time": "09:15",       // Market open
        "end_time": "15:30"          // Market close
    },
    "screener": {
        "universes": ["nifty100"],   // Change to: nifty, banknifty
        "parallel_workers": 8         // Lower for less CPU usage
    }
}
```

Then **restart the scheduler** for changes to take effect.

---

## Monitor Your Runs

### Check Status
```bash
python scheduler.py --status
```

### View Live Logs
```bash
Get-Content logs/scheduler.log -Wait
```

### Outputs Generated
- `nifty_bearnness.html` - Main report
- `nifty_bearnness.csv` - Data export
- `logs/scheduler.log` - Activity log

---

## For Production (Optional)

Set up Windows Task Scheduler to run automatically on startup:

See: [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md#setting-up-windows-task-scheduler-production)

---

## What's Different Now?

**Before:** Had to manually run the screener each time
```bash
python nifty_bearnness_v2.py --universe nifty100 --mode swing --force-yf --screener-format html
```

**After:** Runs automatically
```bash
python scheduler.py --start
# Generates fresh report every 15 minutes!
```

---

## File Structure

```
algooptions/
├── scheduler.py                # Main scheduler (you run this)
├── config_manager.py           # Config loader
├── config/
│   └── scheduler_config.json   # Your settings (EDIT THIS!)
├── logs/
│   ├── scheduler.log           # Activity log
│   └── scheduler_state.json    # Run statistics
├── reports/
│   └── nifty_bearnness_*.html  # Generated reports
│
├── AUTOMATION_QUICKSTART.md    # Quick reference
├── AUTOMATION_GUIDE.md         # Complete documentation
└── REFACTORING_COMPLETE.md     # What was changed
```

---

## Common Tasks

### Run Once (No Scheduling)
```bash
python scheduler.py --run-once
```

### Start Automation (Runs Every 15 Min)
```bash
python scheduler.py --start
```

### Check What Will Happen
```bash
python scheduler.py --test
```

### View Configuration
```bash
python scheduler.py --status
```

### Change Interval
Edit `config/scheduler_config.json`:
```json
"interval_minutes": 30    // Changed from 15 to 30
```
Then restart scheduler.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Nothing generated" | Check `logs/scheduler.log` for errors |
| "Outside market hours" | Normal - only runs 09:15-15:30 |
| "Port already in use" | Scheduler already running - stop it first |
| Want different interval | Edit `config/scheduler_config.json` |

---

## Example: Monitoring Over Time

```bash
# Terminal 1: Start scheduler
python scheduler.py --start

# Terminal 2: Watch logs (new terminal)
Get-Content logs/scheduler.log -Wait

# Output you'll see:
[2026-01-20 09:15:00] [INFO] Run #1 started
[2026-01-20 09:19:45] [INFO] Run #1 completed successfully
[2026-01-20 09:30:00] [INFO] Run #2 started
[2026-01-20 09:35:12] [INFO] Run #2 completed successfully
# ... and so on every 15 minutes!
```

---

## Next: Full Documentation

For advanced topics, see:
- **Quick start:** [AUTOMATION_QUICKSTART.md](AUTOMATION_QUICKSTART.md)
- **Complete guide:** [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)
  - Windows Task Scheduler setup
  - Advanced configuration
  - Performance tuning
  - FAQ

---

## You're All Set! 

Start with:
```bash
python scheduler.py --test
```

Then when ready:
```bash
python scheduler.py --start
```

Enjoy automated stock screening! 📊

