# =============================================================================
#  run_wallet.ps1 — 路径无关的 gbt_wallet 启动器 (Windows PowerShell 5.1+)
# -----------------------------------------------------------------------------
#  特性:
#    * 不硬编码解释器: 依次尝试 GBT_PYTHON -> Get-Command python -> 项目内 .venv/venv
#      -> py -3 -> $PSHOME 推算, 并逐个验证 "版本>=3.10 且能 import fastapi/uvicorn"
#    * 口令: 优先 $env:GBT_WALLET_PASS; 未设置时安全提示(Read-Host -AsSecureString, 仅内存)
#    * 端口守卫: 端口被占时区分"已在运行的钱包服务"(退出 0)与"被别的进程占用"(退出 3)
#    * 默认只绑 127.0.0.1; 数据根默认 %USERPROFILE%\.gbt\gbt_wallet
#
#  用法:
#    pwsh> $env:GBT_WALLET_PASS = Read-Host -AsSecureString | ...   # 或直接设明文
#    pwsh> powershell -ExecutionPolicy Bypass -File gbt_allinone\deploy\run_wallet.ps1
#    pwsh> ... -EnvFile C:\secrets\wallet.env   # 从文件加载(勿提交该文件)
#    pwsh> ... -Foreground                      # 前台运行, Ctrl+C 停止(便于看日志)
#    pwsh> ... -DryRun                          # 只做环境自检并打印将要执行的命令
#
#  退出码: 0=已启动/已在运行  1=参数或环境错误  2=找不到可用解释器
#          3=端口被其他进程占用  4=钱包未初始化  5=启动失败
# =============================================================================
[CmdletBinding()]
param(
    [int]$Port = 0,
    [string]$EnvFile = '',
    [string]$BindHost = '',
    [switch]$Foreground,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)   # 仓库根(gbt_allinone\deploy -> 上两级)
Set-Location $root

function Write-Step($msg) { Write-Host "[run_wallet] $msg" -ForegroundColor Cyan }
function Write-Warn2($msg) { Write-Host "[run_wallet] $msg" -ForegroundColor Yellow }
function Write-Err2($msg) { Write-Host "[run_wallet] $msg" -ForegroundColor Red }

# ---------- 0) 可选: 从 env 文件加载(KEY=VALUE, 支持 # 注释) ----------
function Import-EnvFile([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { Write-Err2 "env 文件不存在: $path"; exit 1 }
    $n = 0
    foreach ($line in Get-Content -LiteralPath $path -Encoding UTF8) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        $i = $t.IndexOf('=')
        if ($i -lt 1) { continue }
        $k = $t.Substring(0, $i).Trim()
        $v = $t.Substring($i + 1).Trim().Trim('"').Trim("'")
        if ($k -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { continue }
        Set-Item -Path ("Env:" + $k) -Value $v
        $n++
    }
    Write-Step "已从 $path 加载 $n 个环境变量"
    # 密封口令: install_service_windows.ps1 -Action Seal 写出的 DPAPI 密文, 在此仅内存解封
    if (-not $env:GBT_WALLET_PASS -and $env:GBT_WALLET_PASS_DPAPI) {
        try {
            Add-Type -AssemblyName System.Security
            $scopeName = 'LocalMachine'
            if ($env:GBT_WALLET_PASS_DPAPI_SCOPE) { $scopeName = $env:GBT_WALLET_PASS_DPAPI_SCOPE }
            $scope = [Security.Cryptography.DataProtectionScope]::$scopeName
            $bytes = [Security.Cryptography.ProtectedData]::Unprotect(
                [Convert]::FromBase64String($env:GBT_WALLET_PASS_DPAPI), $null, $scope)
            $env:GBT_WALLET_PASS = [Text.Encoding]::UTF8.GetString($bytes)
            [Array]::Clear($bytes, 0, $bytes.Length)      # 擦除临时明文缓冲区
            Write-Step "已用 DPAPI($scopeName) 解封口令(仅内存, 不落盘)"
        } catch {
            Write-Err2 "DPAPI 解封失败(账号/作用域不匹配, 或文件损坏): $($_.Exception.Message)"
            exit 1
        }
    }
}
if ($EnvFile) { Import-EnvFile $EnvFile }

# ---------- 1) 参数/默认值 ----------
if ($Port -le 0) { if ($env:GBT_WALLET_PORT) { $Port = [int]$env:GBT_WALLET_PORT } else { $Port = 8097 } }
if (-not $BindHost) { if ($env:GBT_WALLET_BIND_HOST) { $BindHost = $env:GBT_WALLET_BIND_HOST } else { $BindHost = '127.0.0.1' } }
if (-not $env:GBT_WALLET_DIR) {
    $env:GBT_WALLET_DIR = Join-Path $env:USERPROFILE '.gbt\gbt_wallet'
    Write-Step "未设置 GBT_WALLET_DIR, 使用默认: $($env:GBT_WALLET_DIR)"
}
$dataDir = $env:GBT_WALLET_DIR
$logDir = Join-Path $dataDir 'logs'

# ---------- 2) 解释器解析(路径无关) ----------
# 注意(本机实测): AutoClaw 自带解释器带 python3xx._pth, 处于"隔离路径"模式 ——
#   cwd 与 PYTHONPATH 都不会进 sys.path, 因此 `python -m gbt_wallet.api` 会报 No module named 'gbt_wallet'。
# 对策: 不依赖 cwd, 统一用 -c 引导串显式 sys.path.insert(仓库根) 再 runpy 运行, 任何解释器都成立。
function New-BootstrapScript([int]$p, [string]$bindHost) {
    "import sys; sys.path.insert(0, r'$root'); " +
    "sys.argv = ['gbt_wallet.api', '--port', '$p', '--host', r'$bindHost']; " +
    "import runpy; runpy.run_module('gbt_wallet.api', run_name='__main__')"
}

# 同样用于 CLI 子命令(如 init): 文件名:行号口径与上面一致, 不依赖 cwd
function New-CliBootstrap([string]$argvLiteral) {
    "import sys; sys.path.insert(0, r'$root'); sys.argv = $argvLiteral; " +
    "import runpy; runpy.run_module('gbt_wallet.cli', run_name='__main__')"
}

function Test-PythonCandidate([string]$exe, [string]$prefixArg) {
    try {
        $probe = "import sys; v=sys.version_info; assert v>=(3,10), 'need python>=3.10'; " +
                 "sys.path.insert(0, r'$root'); " +
                 "import fastapi, uvicorn, eth_account, cryptography; " +
                 "import gbt_wallet.api as A; assert A.app is not None; print(sys.executable)"
        if ($prefixArg) {
            $out = & $exe $prefixArg '-c' $probe 2>$null
        } else {
            $out = & $exe '-c' $probe 2>$null
        }
        if ($LASTEXITCODE -eq 0 -and $out) { return ([string]($out | Select-Object -Last 1)).Trim() }
    } catch { }
    return $null
}

function Resolve-WalletPython {
    $cands = @()
    if ($env:GBT_PYTHON) { $cands += @{ exe = $env:GBT_PYTHON; pre = '' } }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $cands += @{ exe = $cmd.Source; pre = '' } }
    foreach ($rel in @('.venv\Scripts\python.exe', 'venv\Scripts\python.exe', 'env\Scripts\python.exe')) {
        $p = Join-Path $root $rel
        if (Test-Path -LiteralPath $p) { $cands += @{ exe = $p; pre = '' } }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { $cands += @{ exe = $py.Source; pre = '-3' } }
    # 兜底: 由当前 PowerShell 安装位置推算(常见布局 <home>\python\python.exe 与本机 AutoClaw 自带解释器)
    foreach ($p in @((Join-Path (Split-Path $PSHOME -Parent) 'python.exe'),
                     (Join-Path (Split-Path (Split-Path $PSHOME -Parent) -Parent) 'python.exe'))) {
        if ($p -and (Test-Path -LiteralPath $p)) { $cands += @{ exe = $p; pre = '' } }
    }
    $seen = @{}
    foreach ($c in $cands) {
        if (-not $c.exe) { continue }
        $key = $c.exe.ToLower()
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true
        $found = Test-PythonCandidate $c.exe $c.pre
        if ($found) { return @{ exe = $c.exe; pre = $c.pre; real = $found } }
    }
    return $null
}

Write-Step '解析可用解释器(需 >=3.10 且含 fastapi/uvicorn)...'
$pyInfo = Resolve-WalletPython
if (-not $pyInfo) {
    Write-Err2 '找不到可用解释器。请先安装依赖: python -m pip install -r gbt_allinone\requirements.txt'
    Write-Err2 '也可显式指定: $env:GBT_PYTHON = "<python.exe 绝对路径>"'
    exit 2
}
Write-Step ("解释器: {0}  (sys.executable={1})" -f $pyInfo.exe, $pyInfo.real)

# ---------- 3) 钱包目录守卫 ----------
$keystore = Join-Path $dataDir 'master.enc'
if (-not (Test-Path -LiteralPath $keystore)) {
    Write-Err2 "钱包未初始化, 缺少 $keystore"
    Write-Host '  初始化(助记词只显示一次, 务必离线抄录后离线保存):' -ForegroundColor Yellow
    Write-Host "    cd $root"
    Write-Host '    $env:GBT_WALLET_PASS = "<强口令,>=16位>"'
    Write-Host ("    & '{0}' -c ""{1}""" -f $pyInfo.exe, (New-CliBootstrap "['gbt_wallet.cli','init','--pass-env']"))
    exit 4
}

# ---------- 4) 口令: env -> 安全提示(仅内存) ----------
if (-not $env:GBT_WALLET_PASS) {
    if (-not [Environment]::UserInteractive) {
        Write-Err2 '非交互会话且未设置 GBT_WALLET_PASS(服务/计划任务请在任务动作或 EnvironmentFile 中提供)'
        exit 1
    }
    Write-Warn2 '未设置 $env:GBT_WALLET_PASS, 请交互输入(不会落盘)'
    $sec = Read-Host 'Wallet passphrase' -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { $env:GBT_WALLET_PASS = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
if (-not $env:GBT_WALLET_PASS) { Write-Err2 '口令为空, 中止'; exit 1 }

# ---------- 5) 端口守卫 ----------
function Get-PortOwner([int]$p) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        if ($conn) { return @($conn.OwningProcess | Select-Object -Unique) }
    } catch { }
    try {   # 兼容无 Get-NetTCPConnection 的环境
        $line = netstat -ano | Select-String -Pattern (":$p\s+.*LISTENING")
        if ($line) {
            $ids = @()
            foreach ($l in $line) {
                $t = ($l.ToString() -split '\s+') | Where-Object { $_ }
                $ids += [int]$t[-1]
            }
            return @($ids | Select-Object -Unique)
        }
    } catch { }
    return @()
}

$healthUrl = "http://127.0.0.1:$Port/api/gbtwallet/health"
# 探测健康时必须带上令牌(服务一旦启用 GBT_WALLET_API_TOKEN, 无令牌一律 401)
$healthHeaders = @{}
if ($env:GBT_WALLET_API_TOKEN) { $healthHeaders['Authorization'] = "Bearer $($env:GBT_WALLET_API_TOKEN)" }

function Test-Health([int]$timeoutSec = 5) {
    # 返回 @{ state = 'ok'|'auth_required'|'other'|'down'; detail = '' }
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -Headers $healthHeaders -TimeoutSec $timeoutSec -UseBasicParsing
        if ($r.StatusCode -eq 200 -and $r.Content -match 'gbtwallet|initialized|version') {
            return @{ state = 'ok'; detail = '200' }
        }
        return @{ state = 'other'; detail = "status=$($r.StatusCode)" }
    } catch {
        $code = $null
        try { $code = [int]$_.Exception.Response.StatusCode } catch { }
        if ($code -eq 401) { return @{ state = 'auth_required'; detail = '401 (令牌不匹配或未提供)' } }
        return @{ state = 'down'; detail = $_.Exception.Message }
    }
}

$owners = @(Get-PortOwner $Port)
if ($owners.Count -gt 0) {
    $h = Test-Health 5
    if ($h.state -eq 'ok') {
        Write-Step "端口 $Port 已在运行钱包服务(健康检查 200), 无需重复启动: $healthUrl"
        exit 0
    }
    if ($h.state -eq 'auth_required') {
        Write-Err2 "端口 $Port 已被一个受令牌保护的服务占用(PID: $($owners -join ',')) —— $($h.detail)"
        Write-Host '  若那确实是本钱包服务: 请让本进程拿到同一 GBT_WALLET_API_TOKEN; 否则换端口启动。' -ForegroundColor Yellow
        exit 3
    }
    Write-Err2 "端口 $Port 被其他进程占用(PID: $($owners -join ','))"
    Write-Host "  排查: Get-Process -Id $($owners -join ',') | Select-Object Id,ProcessName,Path" -ForegroundColor Yellow
    Write-Host "  或换端口: -Port 8098 (并同步 GBT_WALLET_PORT / 反向代理上游)" -ForegroundColor Yellow
    exit 3
}

if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outLog = Join-Path $logDir "wallet-$stamp.out.log"
$errLog = Join-Path $logDir "wallet-$stamp.err.log"
$bootstrap = New-BootstrapScript $Port $BindHost
$argList = @('-c', ('"' + $bootstrap + '"'))   # Start-Process 不会自动加引号, 需自带
$argListDirect = @('-c', $bootstrap)           # & 调用由 PowerShell 自动加引号, 不能再自带

if ($DryRun) {
    Write-Step "[DryRun] 不启动。将要执行:"
    Write-Host ("  {0} -c ""{1}""" -f $pyInfo.exe, $bootstrap)
    Write-Host ("  cwd      : {0}" -f $root)
    Write-Host ("  data dir : {0}" -f $dataDir)
    Write-Host ("  bind     : {0}:{1}   auth={2}  cors={3}" -f $BindHost, $Port,
        $(if ($env:GBT_WALLET_API_TOKEN) { 'on(Bearer)' } else { 'off' }),
        $(if ($env:GBT_CORS_ORIGINS) { $env:GBT_CORS_ORIGINS } else { '*' }))
    exit 0
}

# ---------- 6) 启动 ----------
if ($Foreground) {
    Write-Step "前台启动: http://$BindHost`:$Port  (Ctrl+C 停止; data=$dataDir)"
    & $pyInfo.exe @argListDirect
    exit $LASTEXITCODE
}

Write-Step "后台启动(隐藏窗口)..."
$proc = Start-Process -FilePath $pyInfo.exe -ArgumentList $argList -WorkingDirectory $root `
    -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru

# 轮询健康检查(最多 30 秒)
$ok = $false
$lastState = ''
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if ($proc.HasExited) { break }
    $h = Test-Health 3
    $lastState = $h.state
    if ($h.state -eq 'ok') { $ok = $true; break }
}
if ($ok) {
    Write-Step "已启动: http://$BindHost`:$Port/api/gbtwallet/health (PID $($proc.Id))"
    Write-Host "  日志: $outLog / $errLog" -ForegroundColor DarkGray
    Write-Host "  停止: Stop-Process -Id $($proc.Id)" -ForegroundColor DarkGray
    exit 0
}
if ($proc.HasExited) {
    Write-Err2 "进程已退出(code=$($proc.ExitCode)), 见日志: $errLog"
    if (Test-Path -LiteralPath $errLog) { Get-Content -LiteralPath $errLog -Encoding UTF8 -Tail 20 | Write-Host }
    exit 5
}
if ($lastState -eq 'auth_required') {
    Write-Err2 "服务已在监听, 但健康检查返回 401 —— 启动进程与服务端令牌不是同一个"
    Write-Host '  请检查 GBT_WALLET_API_TOKEN 是否在本脚本环境与 env 文件中一致。' -ForegroundColor Yellow
    exit 5
}
Write-Warn2 "已启动但健康检查未在 30 秒内通过(PID $($proc.Id)); 请查看日志: $errLog"
exit 5
