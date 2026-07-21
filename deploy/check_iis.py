"""Check IIS and other services"""
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

Write-Host "=== Check IIS ==="
Get-Service W3SVC -ErrorAction SilentlyContinue | Select-Object Name, Status

Write-Host "`n=== Check all listeners on 80 ==="
Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State, OwningProcess
Get-Process -Id (Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Select-Object Id, ProcessName

Write-Host "`n=== Check Windows Firewall inbound rules for 80 ==="
Get-NetFirewallRule -Direction Inbound -LocalPort 80 -ErrorAction SilentlyContinue | Select-Object DisplayName, Enabled, Action

Write-Host "`n=== Try curl from server ==="
try {
  curl -Uri "http://127.0.0.1:80/api/meta" -UseBasicParsing
} catch {
  Write-Host "Local curl failed: $_"
}

Write-Host "`n=== Check DNS ==="
nslookup 115.159.85.157 2>&1 | Select-Object -First 5
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\check_iis.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\check_iis.ps1"',
        timeout=60
    )
    print("stdout:", stdout.read().decode("gbk", errors="replace"))
    print("stderr:", stderr.read().decode("gbk", errors="replace"))

    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
