# LimitUp Monitor - Silent Startup Script
$ErrorActionPreference = 'SilentlyContinue'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"

# Kill existing processes
Get-Process -Name "python" -CommandLine "*uvicorn*" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "node" -CommandLine "*vite*" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "npm" -CommandLine "*vite*" -ErrorAction SilentlyContinue | Stop-Process -Force

# Start backend
Start-Process -FilePath "python" `
  -ArgumentList "-m uvicorn main:app --reload --host 0.0.0.0 --port 8000" `
  -WorkingDirectory $backendDir `
  -WindowStyle Hidden

# Start frontend
Start-Process -FilePath "npm" `
  -ArgumentList "run dev" `
  -WorkingDirectory $frontendDir `
  -WindowStyle Hidden

Write-Host "LimitUp Monitor started silently."
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  Backend:  http://localhost:8000"
