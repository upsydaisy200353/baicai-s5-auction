"""Check and restart server"""
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

Write-Host "=== Kill python ==="
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

Write-Host "=== Start uvicorn ==="
$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:80,http://127.0.0.1"
Set-Location "C:\apps\baicai-s5-auction\server"
& ".venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 80
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\start_again.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    stdin, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\start_again.ps1"',
        timeout=300
    )

    time.sleep(12)
    print("=== Checking ===")
    
    client2 = paramiko.SSHClient()
    client2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client2.connect(
        HOST, 22, USER, PASSWORD, timeout=30,
        allow_agent=False, look_for_keys=False
    )
    
    _, stdout2, stderr2 = client2.exec_command(
        'netstat -ano | findstr ":80.*LISTENING"', timeout=30
    )
    print("Port 80:", stdout2.read().decode())
    
    client2.close()
    client.close()

    time.sleep(5)
    print("\n=== Testing external ===")
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://{HOST}/api/meta", timeout=20)
        print("SUCCESS:", resp.status)
    except Exception as e:
        print("EXTERNAL FAIL:", e)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
