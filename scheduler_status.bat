@echo off
REM Check scheduler status

echo Checking AlgoOptions Scheduler Status...
echo.

python scripts\scheduling\scheduler.py --status

echo.
pause