@echo off
REM Stop the running AlgoOptions scheduler

echo Stopping AlgoOptions Scheduler...
python stop_scheduler.py
echo.
pause