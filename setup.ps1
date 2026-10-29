#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path .venv\Scripts\python.exe)) { py -3 -m venv .venv; if ($LASTEXITCODE -ne 0) { throw 'Python 3 is required.' } }
& .venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check network and retry.' }
if (-not (Test-Path config.json)) { Copy-Item config.example.json config.json }
& .venv\Scripts\python.exe discover.py
Write-Host 'Setup complete. Pair Pixoo in Windows Settings, edit config.json, then run diagnose.bat.'

