$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$python = if (Test-Path "C:\Python312\python.exe") { "C:\Python312\python.exe" } elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { throw "未找到 Python" }
$electron = Join-Path $root "holo_pet\node_modules\electron\dist\electron.exe"
$main = Join-Path $root "holo_pet\desktop\main.cjs"
$launcher = Join-Path $root "holo_pet\launch_panel.py"

$healthy = $false
try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/state" -TimeoutSec 2
    $healthy = $true
} catch {}

if (-not $healthy) {
    Start-Process -FilePath $python -ArgumentList @($launcher, "--host", "127.0.0.1", "--port", "8765") -WorkingDirectory $root -WindowStyle Hidden
    foreach ($attempt in 1..25) {
        Start-Sleep -Milliseconds 400
        try {
            $null = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/state" -TimeoutSec 2
            $healthy = $true
            break
        } catch {}
    }
}

if (-not $healthy) { throw "本地面板未能在 10 秒内启动" }
Start-Process -FilePath $electron -ArgumentList @($main) -WorkingDirectory (Join-Path $root "holo_pet")
