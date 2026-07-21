"""Restart server script"""
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

Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | ForEach-Object {
  if ($_.CommandLine -and $_.CommandLine -match 'uvicorn main:app') {
    Write-Host ("Stopping old pid " + $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
}
Start-Sleep -Seconds 2

$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:8000,http://127.0.0.1"
Set-Location C:\apps\baicai-s5-auction\server
$arg = '-m uvicorn main:app --host 0.0.0.0 --port 8000'
Start-Process -FilePath '.venv\Scripts\python.exe' -ArgumentList $arg -WindowStyle Hidden

Start-Sleep -Seconds 5
netstat -ano | findstr :8000
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\restart_auction.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\restart_auction.ps1"',
        timeout=60
    )
    print("stdout:", stdout.read().decode())
    print("stderr:", stderr.read().decode())

    time.sleep(5)
    _, stdout, stderr = client.exec_command("netstat -ano | findstr :8000", timeout=30)
    print("\nPort 8000 after restart:", stdout.read().decode())

    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
