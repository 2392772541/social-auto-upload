$ErrorActionPreference = 'SilentlyContinue'
$pids = New-Object System.Collections.Generic.HashSet[int]

Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match 'sau_backend\.py' -or
    ($_.CommandLine -match 'vite' -and $_.CommandLine -match 'sau_frontend')
} | ForEach-Object {
    [void]$pids.Add([int]$_.ProcessId)
}

foreach ($port in @(5409, 5173)) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.OwningProcess -gt 0) {
            [void]$pids.Add([int]$_.OwningProcess)
        }
    }
}

if ($pids.Count -eq 0) {
    Write-Host '[INFO] 未发现正在运行的 SAU 进程'
} else {
    foreach ($p in $pids) {
        try {
            Stop-Process -Id $p -Force -ErrorAction Stop
            Write-Host "[OK] 已停止进程 PID=$p"
        } catch {
            Write-Host "[WARN] 无法停止进程 PID=$p"
        }
    }
}
