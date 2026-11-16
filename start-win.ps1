$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logsDir = Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$confFile = Join-Path $root 'conf.py'
$confExample = Join-Path $root 'conf.example.py'
if (-not (Test-Path $confFile) -and (Test-Path $confExample)) {
    Copy-Item -LiteralPath $confExample -Destination $confFile -Force
}

$pyExe = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $pyExe)) {
    throw "Python virtualenv not found: $pyExe"
}

$p5409 = Get-NetTCPConnection -LocalPort 5409 -State Listen -ErrorAction SilentlyContinue
if (-not $p5409) {
    Start-Process -FilePath $pyExe `
        -ArgumentList 'sau_backend.py' `
        -WorkingDirectory $root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logsDir 'sau-backend.out.log') `
        -RedirectStandardError (Join-Path $logsDir 'sau-backend.err.log') | Out-Null
}

$p5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
if (-not $p5173) {
    $frontendDir = Join-Path $root 'sau_frontend'
    Start-Process -FilePath 'cmd.exe' `
        -ArgumentList '/c npm run dev -- --host 127.0.0.1 --port 5173' `
        -WorkingDirectory $frontendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logsDir 'sau-frontend.out.log') `
        -RedirectStandardError (Join-Path $logsDir 'sau-frontend.err.log') | Out-Null
}

$deadline = (Get-Date).AddSeconds(15)
while ((Get-Date) -lt $deadline) {
    $okBe = Get-NetTCPConnection -LocalPort 5409 -State Listen -ErrorAction SilentlyContinue
    $okFe = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($okBe -and $okFe) {
        Write-Host '[OK] SAU backend (5409) and frontend (5173) are listening.'
        exit 0
    }
    Start-Sleep -Milliseconds 400
}

Write-Host '[WARN] Started SAU processes; ports still warming up.'
exit 0
