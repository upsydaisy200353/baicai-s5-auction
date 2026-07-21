"""Check and fix netsh portproxy 80 -> 8000 on the server."""
import time
import urllib.request

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, 22, USER, PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)

fix_ps = r"""$ErrorActionPreference = 'Continue'
Write-Host '=== Current portproxy ==='
netsh interface portproxy show all
Write-Host '=== Reconfiguring 80 -> 8000 ==='
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=80 2>$null
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=80 connectaddress=127.0.0.1 connectport=8000
Write-Host '=== New portproxy ==='
netsh interface portproxy show all
Write-Host '=== Firewall rules ==='
Get-NetFirewallRule -DisplayName 'Baicai Auction*' -ErrorAction SilentlyContinue | Select-Object DisplayName, Enabled, Direction, Action
Write-Host '=== Port 80 listener ==='
Get-NetTCPConnection -LocalPort 80 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State, OwningProcess
Write-Host '=== Port 8000 listener ==='
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State, OwningProcess
Write-Host '=== Local 8000 test ==='
try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/meta' -UseBasicParsing -TimeoutSec 10
    Write-Host ('LOCAL_8000_OK: ' + $r.StatusCode)
} catch {
    Write-Host ('LOCAL_8000_FAIL: ' + $_.Exception.Message)
}
Write-Host '=== Local 80 test ==='
try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:80/api/meta' -UseBasicParsing -TimeoutSec 10
    Write-Host ('LOCAL_80_OK: ' + $r.StatusCode)
} catch {
    Write-Host ('LOCAL_80_FAIL: ' + $_.Exception.Message)
}
Write-Host 'DONE'
"""

sftp = c.open_sftp()
with sftp.file(r"C:\apps\_fix_portproxy.ps1", "w") as f:
    f.write(fix_ps.replace("\n", "\r\n"))
sftp.close()

_, stdout, stderr = c.exec_command(
    'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\\apps\\_fix_portproxy.ps1"',
    timeout=60,
)
out = stdout.read().decode("utf-8", "replace")
err = stderr.read().decode("utf-8", "replace")
print("Output:", out)
if err:
    print("Stderr:", err)

c.close()

# External test
time.sleep(3)
try:
    resp = urllib.request.urlopen("http://115.159.85.157/api/meta", timeout=20)
    print("External OK:", resp.status)
    print("Body:", resp.read().decode()[:200])
except Exception as e:
    print("External FAIL:", e)
