"""Upload main.py to server and restart."""
import time

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"
APP_ROOT = r"C:\apps\baicai-s5-auction"
LOCAL_MAIN = r"d:\开发类\baicai s5-Auction\server\main.py"
REMOTE_MAIN = r"C:\apps\baicai-s5-auction\server\main.py"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, 22, USER, PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)

# Upload main.py
sftp = c.open_sftp()
sftp.put(LOCAL_MAIN, REMOTE_MAIN)
sftp.close()
print("main.py uploaded")

# Write restart script - use port 8000 with portproxy 80->8000 (matches original deploy)
restart_ps = r"""$ErrorActionPreference = 'Continue'
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
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000" -WindowStyle Hidden
Start-Sleep -Seconds 5
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/meta" -UseBasicParsing -TimeoutSec 10
    Write-Host ("LOCAL_OK: " + $r.StatusCode)
} catch {
    Write-Host ("LOCAL_FAIL: " + $_.Exception.Message)
}
"""

sftp = c.open_sftp()
with sftp.file(r"C:\apps\_restart.ps1", "w") as f:
    f.write(restart_ps.replace("\n", "\r\n"))
sftp.close()

_, stdout, stderr = c.exec_command(
    'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\\apps\\_restart.ps1"',
    timeout=60,
)
out = stdout.read().decode("utf-8", "replace")
err = stderr.read().decode("utf-8", "replace")
print("Restart output:", out)
if err:
    print("Stderr:", err)

c.close()

# Verify external access
time.sleep(5)
import urllib.request

try:
    resp = urllib.request.urlopen("http://115.159.85.157/api/meta", timeout=20)
    print("External OK:", resp.status)
except Exception as e:
    print("External FAIL:", e)
