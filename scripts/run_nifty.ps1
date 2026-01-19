Param(
  [string]$Script,
  [string]$Log,
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$ExtraArgs
)

# Resolve default paths relative to the repo root (avoid escape issues when using -File)
if (-not $Script) {
  $Script = Join-Path (Join-Path $PSScriptRoot '..') 'nifty_bearnness.py'
}
if (-not $Log) {
  $repoRoot = Join-Path $PSScriptRoot '..'
  $logDir = Join-Path $repoRoot 'logs'
  $Log = Join-Path $logDir 'nifty_run.log'
}
# Ensure UTF-8 for Python and PowerShell output to avoid encoding errors
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new()

# Locate venv python if present, otherwise use system python
$venvPython = Join-Path $PSScriptRoot '..\venv\Scripts\python.exe'
if (Test-Path $venvPython) {
  $python = $venvPython
} else {
  $python = 'python'
}

Write-Host "Using python: $python"
# Ensure log directory exists
$logDir = Split-Path $Log -Parent
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
# Forward any additional args passed to the wrapper to the Python script
& $python $Script @ExtraArgs 2>&1 | Tee-Object -FilePath $Log
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
  Write-Warning "Script exited with code $exitCode"
}
exit $exitCode
