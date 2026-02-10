#!/usr/bin/env python3
"""
Quick BANKNIFTY test to verify cache fix works
"""
import subprocess
import sys
import json

print("=" * 70)
print("BANKNIFTY SCREENER TEST - Cache Integrity Fix Verification")
print("=" * 70)
print()

# Run BANKNIFTY screener
print("Running BANKNIFTY screener...")
result = subprocess.run(
    [sys.executable, 'nifty_bearnness_v2.py', '--index', 'BANKNIFTY', '--quick'],
    cwd='d:\\DreamProject\\algooptions',
    capture_output=True,
    text=True,
    timeout=120
)

# Check for HDFCBANK in results
output = result.stdout
if 'HDFCBANK' in output:
    print("[FOUND] HDFCBANK appears in output")
    # Extract relevant lines
    for line in output.split('\n'):
        if 'HDFCBANK' in line:
            print(f"  {line.strip()}")
else:
    print("[WARNING] HDFCBANK not found in output")

# Check for errors
if 'error' in output.lower() or 'exception' in output.lower():
    print("\n[ERROR] Errors detected in output")
    for line in output.split('\n')[-20:]:  # Last 20 lines
        if line.strip():
            print(f"  {line.strip()}")
else:
    print("[OK] No errors detected")

# Show summary
print()
print("Output Summary:")
lines = output.split('\n')
for i, line in enumerate(lines[-30:]):  # Last 30 lines
    if line.strip():
        print(f"  {line.strip()}")

print()
print("Exit code:", result.returncode)
if result.returncode == 0:
    print("[SUCCESS] BANKNIFTY screener completed successfully")
else:
    print("[FAILED] BANKNIFTY screener failed")
