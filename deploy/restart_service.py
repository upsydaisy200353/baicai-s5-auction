"""Restart uvicorn service via Scheduled Task (survives SSH session close)."""
import time
import urllib.request

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"
JWT = "baicai-s5-tencent-jwt-change-after-deploy"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, 22, USER, PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)

restart_ps = r"""$ErrorActionPreference = 'Continue'
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

Write-Host '=== Stop old uvicorn processes ==='
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | ForEach-Object {
  if ($_.CommandLine -and $_.CommandLine -match 'uvicorn main:app') {
    Write-Host ("Stopping pid " + $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
}
Start-Sleep -Seconds 2

Write-Host '=== Write start-auction.ps1 ==='
$startPs = @'
$env:AUCTION_JWT_SECRET = "JWT_PLACEHOLDER"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:8000,http://127.0.0.1"
Set-Location C:\apps\baicai-s5-auction\server
& C:\apps\baicai-s5-auction\server\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
'@
$startPs = $startPs -replace 'JWT_PLACEHOLDER', 'JWT_PLACEHOLDER'
Set-Content -Path 'C:\apps\baicai-s5-auction\start-auction.ps1' -Value $startPs -Encoding UTF8
Write-Host 'start-auction.ps1 written'

Write-Host '=== Reconfigure portproxy 80 -> 8000 ==='
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=80 2>$null
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=80 connectaddress=127.0.0.1 connectport=8000
netsh interface portproxy show all

Write-Host '=== Register Scheduled Task ==='
Unregister-ScheduledTask -TaskName 'BaicaiS5Auction' -Confirm:$false -ErrorAction SilentlyContinue
$arg = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\apps\baicai-s5-auction\start-auction.ps1'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName 'BaicaiS5Auction' -Action $action -Trigger $trigger -Settings $settings -User 'SYSTEM' -RunLevel Highest -Force | Out-Null
Write-Host 'Scheduled task registered'

Write-Host '=== Start Scheduled Task ==='
Start-ScheduledTask -TaskName 'BaicaiS5Auction'
Write-Host 'Task started, waiting for health...'

$ok = $false
for ($i=1; $i -le 20; $i++) {
  Start-Sleep -Seconds 2
  try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/meta' -UseBasicParsing -TimeoutSec 5
    Write-Host ('LOCAL_8000_OK attempt ' + $i + ': ' + $r.StatusCode)
    $ok = $true
    break
  } catch {
    Write-Host ("wait " + $i + " ...")
  }
}
if (-not $ok) { Write-Host 'LOCAL_8000_FAIL' }

Write-Host '=== Test port 80 ==='
try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:80/api/meta' -UseBasicParsing -TimeoutSec 10
    Write-Host ('LOCAL_80_OK: ' + $r.StatusCode)
} catch {
    Write-Host ('LOCAL_80_FAIL: ' + $_.Exception.Message)
}

Write-Host '=== Process check ==='
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | ForEach-Object {
  Write-Host ("pid=" + $_.ProcessId + " cmd=" + $_.CommandLine)
}
Write-Host '=== Port 8000 listener ==='
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State, OwningProcess
Write-Host 'DONE'
""".replace("JWT_PLACEHOLDER", JWT)

sftp = c.open_sftp()
with sftp.file(r"C:\apps\_restart_service.ps1", "w") as f:
    f.write(restart_ps.replace("\n", "\r\n"))
sftp.close()

_, stdout, stderr = c.exec_command(
    'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\\apps\\_restart_service.ps1"',
    timeout=120,
)
out = stdout.read().decode("utf-8", "replace")
err = stderr.read().decode("utf-8", "replace")
print("Output:", out)
if err:
    print("Stderr:", err)

c.close()

# External test
time.sleep(3)
try:
    resp = urllib.request.urlopen("http://115.159.85.157/api/meta", timeout=20)
    print("External OK:", resp.status)
    print("Body:", resp.read().decode()[:200])
except Exception as e:
    print("External FAIL:", e)
