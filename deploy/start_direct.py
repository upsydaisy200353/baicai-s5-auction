"""Start server directly and capture errors"""
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

Write-Host "=== Kill old ==="
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "=== Env vars ==="
$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:80,http://127.0.0.1"
Write-Host "JWT: $($env:AUCTION_JWT_SECRET)"
Write-Host "CORS: $($env:CORS_ORIGINS)"

Write-Host "`n=== Start uvicorn ==="
Set-Location "C:\apps\baicai-s5-auction\server"
Write-Host "Current dir: $(Get-Location)"
Write-Host "Files: $(Get-ChildItem | Select-Object Name)"

& ".venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 80 --log-level debug 2>&1
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\start_direct.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\start_direct.ps1"',
        timeout=120
    )
    print("stdout:", stdout.read().decode("gbk", errors="replace")[:5000])
    print("stderr:", stderr.read().decode("gbk", errors="replace")[:2000])

    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
