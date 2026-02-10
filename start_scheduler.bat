@echo off
REM Start the AlgoOptions scheduler
REM Runs the screener every 15 minutes during market hours

echo Starting AlgoOptions Scheduler...
echo Press Ctrl+C to stop the scheduler
echo.

python start_scheduler.py

echo.
echo Scheduler stopped.
pause