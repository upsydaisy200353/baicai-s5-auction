"""Restart server and verify"""
from __future__ import annotations

import paramiko
import time

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

Write-Host "=== Kill old processes ==="
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "=== Start uvicorn ==="
$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:80,http://127.0.0.1"
Set-Location "C:\apps\baicai-s5-auction\server"
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 80" -WindowStyle Hidden

Start-Sleep -Seconds 8
Write-Host "=== Port 80 ==="
netstat -ano | findstr ":80.*LISTENING"

Write-Host "`n=== Test local ==="
try {
  $r = Invoke-WebRequest -Uri "http://127.0.0.1/api/meta" -UseBasicParsing -TimeoutSec 5
  Write-Host "OK: $($r.StatusCode)"
} catch {
  Write-Host "FAIL: $_"
}

Write-Host "`n=== Python processes ==="
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\restart_final.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\restart_final.ps1"',
        timeout=120
    )
    print("stdout:", stdout.read().decode("gbk", errors="replace"))
    print("stderr:", stderr.read().decode("gbk", errors="replace"))

    client.close()

    time.sleep(5)
    print("\n=== Testing external access ===")
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://{HOST}/api/meta", timeout=20)
        print("SUCCESS:", resp.status, resp.read().decode()[:100])
    except Exception as e:
        print("EXTERNAL FAIL:", e)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
