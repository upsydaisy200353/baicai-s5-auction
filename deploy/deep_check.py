"""Deep check server network and services"""
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

Write-Host "=== 1. Check all listeners ==="
netstat -ano | findstr "LISTENING"

Write-Host "`n=== 2. Process on port 80 ==="
$pid = (netstat -ano | findstr ":80.*LISTENING").Split()[-1]
Write-Host "PID: $pid"
if ($pid) {
  Get-Process -Id $pid -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Path
}

Write-Host "`n=== 3. Check for IIS ==="
Get-Service W3SVC -ErrorAction SilentlyContinue | Select-Object Name, Status

Write-Host "`n=== 4. Check for nginx/apache ==="
Get-Process nginx -ErrorAction SilentlyContinue | Select-Object Id, ProcessName
Get-Process httpd -ErrorAction SilentlyContinue | Select-Object Id, ProcessName

Write-Host "`n=== 5. Windows Firewall status ==="
Get-NetFirewallProfile | Select-Object Name, Enabled

Write-Host "`n=== 6. Check load balancer metadata ==="
try {
  Invoke-RestMethod -Uri "http://metadata.tencentyun.com/meta-data/instance-id" -TimeoutSec 5
} catch {
  Write-Host "No Tencent metadata"
}

Write-Host "`n=== 7. Test from localhost without port ==="
try {
  $r = Invoke-WebRequest -Uri "http://localhost/api/meta" -UseBasicParsing -TimeoutSec 5
  Write-Host "localhost: $($r.StatusCode)"
} catch {
  Write-Host "localhost failed: $_"
}

Write-Host "`n=== 8. Check hosts file ==="
Get-Content "C:\Windows\System32\drivers\etc\hosts" | Select-Object -First 30

Write-Host "`n=== 9. Check for proxy software ==="
Get-Process | Where-Object { $_.ProcessName -match "proxy|nginx|apache|haproxy|lb" } | Select-Object ProcessName, Id
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\deep_check.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\deep_check.ps1"',
        timeout=120
    )
    print("stdout:", stdout.read().decode("gbk", errors="replace"))
    print("stderr:", stderr.read().decode("gbk", errors="replace"))

    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
