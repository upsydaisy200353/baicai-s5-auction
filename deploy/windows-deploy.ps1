$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Log($m) { Write-Output ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) }

Log 'START deploy'
New-Item -ItemType Directory -Force -Path C:\apps | Out-Null

if (Test-Path 'C:\apps\baicai-s5-auction\.git') {
  Set-Location 'C:\apps\baicai-s5-auction'
  git fetch --all
  git reset --hard origin/main
  Log 'REPO updated'
} else {
  if (Test-Path 'C:\apps\baicai-s5-auction') {
    Remove-Item -Recurse -Force 'C:\apps\baicai-s5-auction'
  }
  git clone https://github.com/upsydaisy200353/baicai-s5-auction.git 'C:\apps\baicai-s5-auction'
  Log 'REPO cloned'
}

Set-Location 'C:\apps\baicai-s5-auction'
git log -1 --oneline

Log 'Building frontend'
Set-Location 'C:\apps\baicai-s5-auction\frontend'
npm ci
npm run build
if (-not (Test-Path '.\dist\index.html')) { throw 'frontend dist missing' }
Log 'Frontend OK'

Log 'Installing backend deps'
Set-Location 'C:\apps\baicai-s5-auction\server'
if (-not (Test-Path '.\.venv\Scripts\python.exe')) {
  python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Log 'Backend deps OK'

# Start script
$startPs1 = @'
$env:AUCTION_JWT_SECRET = 'baicai-s5-tencent-prod-change-me'
$env:CORS_ORIGINS = 'http://115.159.85.157,http://127.0.0.1:8000,http://127.0.0.1'
Set-Location 'C:\apps\baicai-s5-auction\server'
& 'C:\apps\baicai-s5-auction\server\.venv\Scripts\python.exe' -m uvicorn main:app --host 0.0.0.0 --port 8000
'@
Set-Content -Path 'C:\apps\baicai-s5-auction\start-auction.ps1' -Value $startPs1 -Encoding UTF8
Log 'Wrote start-auction.ps1'

# Firewall
New-NetFirewallRule -DisplayName 'Baicai Auction HTTP 80' -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName 'Baicai Auction App 8000' -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -ErrorAction SilentlyContinue | Out-Null
Log 'Firewall rules OK'

# Port proxy 80 -> 8000
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=80 2>$null
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=80 connectaddress=127.0.0.1 connectport=8000
netsh interface portproxy show all
Log 'Portproxy OK'

# Stop old process on 8000 if any
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

# Scheduled task for autostart
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\apps\baicai-s5-auction\start-auction.ps1'
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName 'BaicaiS5Auction' -Action $action -Trigger $trigger -Settings $settings -User 'SYSTEM' -RunLevel Highest -Force | Out-Null
Log 'Scheduled task registered'

# Start now via scheduled task or background process
Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\apps\baicai-s5-auction\start-auction.ps1' -WindowStyle Hidden
Log 'Started app process'

# Wait for health
$ok = $false
for ($i = 1; $i -le 30; $i++) {
  Start-Sleep -Seconds 2
  try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/meta' -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -eq 200) { $ok = $true; Log ("Health OK attempt $i : " + $r.Content); break }
  } catch {
    Log ("Health wait $i ...")
  }
}
if (-not $ok) { throw 'App failed to become healthy on :8000' }

try {
  $r80 = Invoke-WebRequest -Uri 'http://127.0.0.1:80/api/meta' -UseBasicParsing -TimeoutSec 5
  Log ("Port80 OK: " + $r80.StatusCode)
} catch {
  Log ('Port80 check failed (open Tencent firewall TCP 80): ' + $_.Exception.Message)
}

Log 'DEPLOY_DONE'
Write-Output 'URL=http://115.159.85.157/'
