# LimitUp Monitor - Silent Stop Script
Get-Process -Name "python" -CommandLine "*uvicorn*" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "node" -CommandLine "*vite*" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "npm" -CommandLine "*vite*" -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "LimitUp Monitor stopped."
