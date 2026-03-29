@echo off
setlocal

set "projectRoot=%~dp0"

powershell -Command "^
$config = Get-Content '%projectRoot%config.json' | ConvertFrom-Json; ^
$backendPort = $config.backend.port; ^
$frontendPort = $config.frontend.port; ^
Write-Host 'Stopping services on ports' $backendPort 'and' $frontendPort '...'; ^
$bp = Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess; ^
if ($bp) { Write-Host 'Killing backend process' $bp; Stop-Process -Id $bp -Force }; ^
$fp = Get-NetTCPConnection -LocalPort $frontendPort -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess; ^
if ($fp) { Write-Host 'Killing frontend process' $fp; Stop-Process -Id $fp -Force }; ^
Write-Host 'Done.'"

echo Press any key to exit...
pause >nul
