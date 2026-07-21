"""Fix port proxy and firewall"""
from __future__ import annotations

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"

def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST, 22, USER, PASSWORD, timeout=30,
        allow_agent=False, look_for_keys=False
    )

    script = r'''
$ErrorActionPreference = 'Continue'

Write-Host "=== Kill old python ==="
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | ForEach-Object {
  if ($_.CommandLine -match 'uvicorn') {
    Stop-Process -Id $_.ProcessId -Force
  }
}
Start-Sleep -Seconds 2

Write-Host "=== Check port binding ==="
netstat -ano | findstr ":8000"

Write-Host "=== Re-configure port proxy ==="
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=80
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=80 connectaddress=127.0.0.1 connectport=8000
netsh interface portproxy show all

Write-Host "=== Firewall rules ==="
New-NetFirewallRule -DisplayName "Baicai HTTP 80" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "Baicai App 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -ErrorAction SilentlyContinue
Get-NetFirewallRule -DisplayName "*Baicai*" | Select-Object Name, DisplayName, Enabled

Write-Host "=== Start uvicorn with explicit bind ==="
$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:8000,http://127.0.0.1"
Set-Location "C:\apps\baicai-s5-auction\server"
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000" -WindowStyle Hidden

Start-Sleep -Seconds 5
Write-Host "=== Port 8000 after start ==="
netstat -ano | findstr ":8000"

Write-Host "=== Test local access ==="
try {
  $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/meta" -UseBasicParsing -TimeoutSec 5
  Write-Host "Local META: $($r.StatusCode) $($r.Content)"
} catch {
  Write-Host "Local access failed: $_"
}
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\fix_proxy.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\fix_proxy.ps1"',
        timeout=120
    )
    print("stdout:", stdout.read().decode("gbk", errors="replace"))
    print("stderr:", stderr.read().decode("gbk", errors="replace"))

    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
