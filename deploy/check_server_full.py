"""Check server status and code version"""
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

Write-Host "=== 1. Check port 80 ==="
netstat -ano | findstr ":80.*LISTENING"

Write-Host "`n=== 2. Check python processes ==="
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Path

Write-Host "`n=== 3. Frontend dist files ==="
Get-ChildItem "C:\apps\baicai-s5-auction\frontend\dist" | Select-Object Name, Length, LastWriteTime

Write-Host "`n=== 4. Check if debug console.log is present ==="
$content = Get-Content "C:\apps\baicai-s5-auction\frontend\dist\assets\*.js" -Raw
if ($content -match "onSubmit called") {
  Write-Host "YES - debug log found"
} else {
  Write-Host "NO - debug log not found"
}

Write-Host "`n=== 5. Server files ==="
Get-ChildItem "C:\apps\baicai-s5-auction\server" | Select-Object Name, Length, LastWriteTime

Write-Host "`n=== 6. Test local access ==="
try {
  $r = Invoke-WebRequest -Uri "http://127.0.0.1/api/meta" -UseBasicParsing -TimeoutSec 5
  Write-Host "OK: $($r.StatusCode) $($r.Content.Substring(0, [Math]::Min(100, $r.Content.Length)))"
} catch {
  Write-Host "FAIL: $_"
}
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\check_full.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\check_full.ps1"',
        timeout=120
    )
    print("stdout:", stdout.read().decode("gbk", errors="replace"))
    print("stderr:", stderr.read().decode("gbk", errors="replace"))

    client.close()

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
