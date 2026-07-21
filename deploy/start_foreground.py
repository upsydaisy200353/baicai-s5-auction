"""Start server in foreground mode"""
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
        allow_agent=False, look_for_keys=False,
        banner_timeout=60
    )

    client.exec_command(
        r'powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"',
        timeout=30
    )
    time.sleep(3)

    script = r'''
$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:80,http://127.0.0.1"
Set-Location "C:\apps\baicai-s5-auction\server"
& ".venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 80
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\start_foreground.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    stdin, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\start_foreground.ps1"',
        timeout=300
    )

    time.sleep(10)
    print("=== Checking if server started ===")
    
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
    
    _, stdout2, stderr2 = client2.exec_command(
        'powershell -Command "Invoke-WebRequest -Uri http://127.0.0.1/api/meta -UseBasicParsing -TimeoutSec 5"',
        timeout=30
    )
    print("Local test:", stdout2.read().decode()[:200])
    
    client2.close()

    time.sleep(5)
    print("\n=== Testing external access ===")
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://{HOST}/api/meta", timeout=20)
        print("SUCCESS:", resp.status, resp.read().decode()[:100])
    except Exception as e:
        print("EXTERNAL FAIL:", e)

    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
