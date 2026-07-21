"""Upload zip via SFTP and finish Windows deploy (no GitHub)."""
from __future__ import annotations

import os
import sys
import time

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"
ZIP_LOCAL = os.path.join(os.environ["TEMP"], "baicai-s5-deploy.zip")
APP_ROOT = r"C:\apps\baicai-s5-auction"
JWT = "baicai-s5-tencent-jwt-change-after-deploy"


def connect() -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        HOST,
        22,
        USER,
        PASSWORD,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
        banner_timeout=60,
    )
    return c


def run_ps(client: paramiko.SSHClient, script: str, timeout: int = 1200) -> tuple[int, str]:
    sftp = client.open_sftp()
    try:
        try:
            sftp.mkdir("C:/apps")
        except OSError:
            pass
        remote = r"C:\apps\_deploy_step.ps1"
        with sftp.file(remote, "w") as f:
            f.write(script.replace("\n", "\r\n"))
    finally:
        sftp.close()
    print(f"\n>>> script ({len(script)} bytes)")
    _, stdout, stderr = client.exec_command(
        f'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\\apps\\_deploy_step.ps1"',
        timeout=timeout,
    )
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out[-5000:] if len(out) > 5000 else out)
    if err.strip():
        print("[stderr]", err[-2500:] if len(err) > 2500 else err)
    print(f"[exit {code}]")
    return code, out


def main() -> int:
    if not os.path.isfile(ZIP_LOCAL):
        print("missing zip", ZIP_LOCAL)
        return 1

    client = connect()
    print("connected, uploading", ZIP_LOCAL, os.path.getsize(ZIP_LOCAL))
    sftp = client.open_sftp()
    try:
        try:
            sftp.mkdir("C:/apps")
        except OSError:
            pass
        remote_zip = "/C:/apps/baicai-s5-deploy.zip"

        def progress(transferred, total):
            if total and transferred % (1024 * 1024) < 32768:
                print(f"  upload {transferred}/{total}")

        sftp.put(ZIP_LOCAL, r"C:\apps\baicai-s5-deploy.zip", callback=progress)
    finally:
        sftp.close()
    print("upload done")

    code, out = run_ps(
        client,
        rf"""
$ErrorActionPreference = 'Stop'
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

if (Test-Path '{APP_ROOT}') {{ Remove-Item -Recurse -Force '{APP_ROOT}' }}
New-Item -ItemType Directory -Force -Path '{APP_ROOT}' | Out-Null
Expand-Archive -Path 'C:\apps\baicai-s5-deploy.zip' -DestinationPath '{APP_ROOT}' -Force
Write-Host 'EXTRACT_OK'
Get-ChildItem '{APP_ROOT}' | Select-Object Name
if (-not (Test-Path '{APP_ROOT}\frontend\dist\index.html')) {{ throw 'missing frontend dist' }}
if (-not (Test-Path '{APP_ROOT}\server\main.py')) {{ throw 'missing server' }}
""",
        timeout=300,
    )
    if code != 0:
        return 1

    client.close()
    client = connect()

    code, out = run_ps(
        client,
        rf"""
$ErrorActionPreference = 'Stop'
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
Set-Location '{APP_ROOT}\server'
if (-not (Test-Path .venv)) {{ python -m venv .venv }}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt
Write-Host 'PIP_OK'
""",
        timeout=1200,
    )
    if code != 0:
        return 1

    client.close()
    client = connect()

    code, out = run_ps(
        client,
        rf"""
$ErrorActionPreference = 'Continue'
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

New-NetFirewallRule -DisplayName 'Baicai Auction HTTP 80' -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName 'Baicai Auction App 8000' -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -ErrorAction SilentlyContinue | Out-Null
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=80 | Out-Null
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=80 connectaddress=127.0.0.1 connectport=8000
netsh interface portproxy show all

$startPs = @'
$env:AUCTION_JWT_SECRET = "{JWT}"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:8000,http://127.0.0.1"
Set-Location C:\apps\baicai-s5-auction\server
& C:\apps\baicai-s5-auction\server\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
'@
Set-Content -Path 'C:\apps\baicai-s5-auction\start-auction.ps1' -Value $startPs -Encoding UTF8

Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | ForEach-Object {{
  if ($_.CommandLine -and $_.CommandLine -match 'uvicorn main:app') {{
    Write-Host ("Stopping old pid " + $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }}
}}
Start-Sleep -Seconds 2

$arg = '-NoProfile -ExecutionPolicy Bypass -File C:\apps\baicai-s5-auction\start-auction.ps1'
Start-Process -FilePath 'powershell.exe' -ArgumentList $arg -WindowStyle Hidden

Unregister-ScheduledTask -TaskName 'BaicaiS5Auction' -Confirm:$false -ErrorAction SilentlyContinue
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName 'BaicaiS5Auction' -Action $action -Trigger $trigger -Settings $settings -User 'SYSTEM' -RunLevel Highest -Force | Out-Null

$ok = $false
for ($i=1; $i -le 20; $i++) {{
  Start-Sleep -Seconds 2
  try {{
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/meta' -UseBasicParsing -TimeoutSec 5
    Write-Host ('META ' + $r.StatusCode + ' ' + $r.Content)
    $ok = $true
    break
  }} catch {{
    Write-Host ("wait $i ... " + $_.Exception.Message)
  }}
}}
if (-not $ok) {{ throw 'local meta failed' }}
Write-Host 'DEPLOY_OK'
""",
        timeout=180,
    )
    client.close()
    if code != 0 or "DEPLOY_OK" not in out:
        return 1

    import urllib.request

    time.sleep(2)
    try:
        with urllib.request.urlopen(f"http://{HOST}:8000/api/meta", timeout=20) as resp:
            print("EXT8000", resp.status, resp.read().decode())
    except Exception as e:
        print("EXT8000_FAIL", e)
    try:
        with urllib.request.urlopen(f"http://{HOST}/api/meta", timeout=20) as resp:
            print("EXT80", resp.status, resp.read().decode())
    except Exception as e:
        print("EXT80_FAIL", e)
        print("Open TCP 80 (and optionally 8000) in Tencent Cloud firewall")
        return 2

    print("DONE http://115.159.85.157/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
