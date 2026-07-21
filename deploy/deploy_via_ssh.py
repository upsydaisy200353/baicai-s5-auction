"""Deploy baicai-s5-auction to Windows Server over SSH - local build + upload."""
from __future__ import annotations

import os
import sys
import time
import zipfile

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"
APP_ROOT = r"C:\apps\baicai-s5-auction"
JWT = "baicai-s5-tencent-jwt-change-after-deploy"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


def make_deploy_zip() -> str:
    zip_path = os.path.join(PROJECT_ROOT, "deploy", "baicai-s5-deploy.zip")
    print(f"Creating deploy zip: {zip_path}")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        server_dir = os.path.join(PROJECT_ROOT, "server")
        frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
        
        for root, dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".py") or f == "requirements.txt":
                    src = os.path.join(root, f)
                    rel = os.path.relpath(src, PROJECT_ROOT)
                    zf.write(src, rel)
        
        dist_dir = os.path.join(frontend_dir, "dist")
        for root, dirs, files in os.walk(dist_dir):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, PROJECT_ROOT)
                zf.write(src, rel)
    
    size = os.path.getsize(zip_path)
    print(f"Zip created: {size / (1024 * 1024):.2f} MB")
    return zip_path


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
    zip_path = make_deploy_zip()
    
    client = connect()
    print("connected, uploading...")
    
    sftp = client.open_sftp()
    try:
        try:
            sftp.mkdir("C:/apps")
        except OSError:
            pass
        sftp.put(zip_path, r"C:\apps\baicai-s5-deploy.zip")
    finally:
        sftp.close()
    print("upload done")

    code, out = run_ps(
        client,
        rf"""
$ErrorActionPreference = 'Stop'
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

$tempDir = 'C:\apps\_deploy_temp'
if (Test-Path $tempDir) {{ Remove-Item -Recurse -Force $tempDir }}
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
Expand-Archive -Path 'C:\apps\baicai-s5-deploy.zip' -DestinationPath $tempDir -Force

if (-not (Test-Path '{APP_ROOT}')) {{ New-Item -ItemType Directory -Force -Path '{APP_ROOT}' | Out-Null }}

Copy-Item -Path "$tempDir\server\*.py" -Destination '{APP_ROOT}\server\' -Force
Copy-Item -Path "$tempDir\server\requirements.txt" -Destination '{APP_ROOT}\server\' -Force -ErrorAction SilentlyContinue
if (Test-Path "$tempDir\server\data") {{ Copy-Item -Path "$tempDir\server\data" -Destination '{APP_ROOT}\server\' -Recurse -Force -ErrorAction SilentlyContinue }}

if (Test-Path '{APP_ROOT}\frontend') {{ Remove-Item -Recurse -Force '{APP_ROOT}\frontend' }}
Copy-Item -Path "$tempDir\frontend" -Destination '{APP_ROOT}' -Recurse -Force

Remove-Item -Recurse -Force $tempDir
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
    Write-Host ("wait $i ...")
  }}
}}
if (-not $ok) {{ throw 'local meta failed' }}
Write-Host 'DEPLOY_OK'
""",
        timeout=180,
    )
    client.close()
    if code != 0 or "DEPLOY_OK" not in out:
        print("DEPLOY_FAILED")
        return 1

    import urllib.request

    time.sleep(2)
    try:
        with urllib.request.urlopen(f"http://{HOST}/api/meta", timeout=20) as resp:
            print("EXT80", resp.status, resp.read().decode())
    except Exception as e:
        print("EXT80_FAIL", e)
        print("Open TCP 80 in Tencent Cloud firewall")
        return 2

    print("\nDONE http://115.159.85.157/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
