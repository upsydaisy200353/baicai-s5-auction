"""Bind uvicorn directly to port 80"""
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

Write-Host "=== Remove port proxy ==="
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=80

Write-Host "=== Start uvicorn directly on port 80 ==="
$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:80,http://127.0.0.1"
Set-Location "C:\apps\baicai-s5-auction\server"
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 80" -WindowStyle Hidden

Start-Sleep -Seconds 5
Write-Host "=== Port 80 after start ==="
netstat -ano | findstr ":80"

Write-Host "=== Test local access ==="
try {
  $r = Invoke-WebRequest -Uri "http://127.0.0.1:80/api/meta" -UseBasicParsing -TimeoutSec 5
  Write-Host "Local META: $($r.StatusCode) $($r.Content)"
} catch {
  Write-Host "Local access failed: $_"
}
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\bind_80.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\bind_80.ps1"',
        timeout=120
    )
    print("stdout:", stdout.read().decode("gbk", errors="replace"))
    print("stderr:", stderr.read().decode("gbk", errors="replace"))

    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
