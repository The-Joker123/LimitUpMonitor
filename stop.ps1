$ErrorActionPreference = "SilentlyContinue"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$config = Get-Content "$projectRoot\config.json" | ConvertFrom-Json
$backendPort = $config.backend.port
$frontendPort = $config.frontend.port

Write-Host "Stopping services on ports $backendPort and $frontendPort..."

$bp = Get-NetTCPConnection -LocalPort $backendPort -State Listen | Select-Object -ExpandProperty OwningProcess
if ($bp) {
    Write-Host "Killing backend process $bp"
    Stop-Process -Id $bp -Force
}

$fp = Get-NetTCPConnection -LocalPort $frontendPort -State Listen | Select-Object -ExpandProperty OwningProcess
if ($fp) {
    Write-Host "Killing frontend process $fp"
    Stop-Process -Id $fp -Force
}

Write-Host "Done."
