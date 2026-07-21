"""Deploy baicai-s5-auction to Windows Server over SSH."""
from __future__ import annotations

import sys
import time

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"
REPO = "https://github.com/upsydaisy200353/baicai-s5-auction.git"
APP_ROOT = r"C:\apps\baicai-s5-auction"
JWT = "baicai-s5-tencent-jwt-change-after-deploy"


def connect() -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        HOST,
        port=22,
        username=USER,
        password=PASSWORD,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
        banner_timeout=60,
    )
    return c


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str, str]:
    print(f"\n>>> {cmd[:200]}{'...' if len(cmd) > 200 else ''}")
    # Use PowerShell for consistency
    full = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{cmd}"'
    stdin, stdout, stderr = client.exec_command(full, timeout=timeout, get_pty=False)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out[-3000:] if len(out) > 3000 else out)
    if err.strip():
        print("[stderr]", err[-2000:] if len(err) > 2000 else err)
    print(f"[exit {code}]")
    return code, out, err


def run_ps_file(client: paramiko.SSHClient, script: str, timeout: int = 1200) -> tuple[int, str, str]:
    """Upload and execute a PowerShell script to avoid quoting hell."""
    sftp = client.open_sftp()
    remote = r"C:\apps\_deploy_step.ps1"
    try:
        sftp.mkdir("C:/apps")
    except OSError:
        pass
    with sftp.file(remote, "w") as f:
        f.write(script.replace("\r\n", "\n").replace("\n", "\r\n"))
    sftp.close()
    print(f"\n>>> (script {len(script)} bytes)")
    stdin, stdout, stderr = client.exec_command(
        f'powershell -NoProfile -ExecutionPolicy Bypass -File "{remote}"',
        timeout=timeout,
    )
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out[-4000:] if len(out) > 4000 else out)
    if err.strip():
        print("[stderr]", err[-2000:] if len(err) > 2000 else err)
    print(f"[exit {code}]")
    return code, out, err


def main() -> int:
    client = connect()
    print("connected")

    # 1) tools
    code, out, _ = run_ps_file(
        client,
        r"""
$ErrorActionPreference = 'Continue'
Write-Host 'PATH refresh'
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

function Has($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

if (-not (Has 'choco')) {
  Write-Host 'Installing Chocolatey...'
  Set-ExecutionPolicy Bypass -Scope Process -Force
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  iex ((New-Object Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
}

if (-not (Has 'git')) { choco install -y git --no-progress }
if (-not (Has 'python')) { choco install -y python312 --no-progress }
if (-not (Has 'node')) { choco install -y nodejs-lts --no-progress }

$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
Write-Host ('git: ' + (git --version))
Write-Host ('python: ' + (python --version 2>&1))
Write-Host ('node: ' + (node --version))
Write-Host ('npm: ' + (npm --version))
""",
        timeout=1800,
    )
    if code != 0:
        print("tool install failed")
        return 1

    # Reconnect in case session long
    client.close()
    client = connect()

    # 2) clone / pull + build
    code, out, _ = run_ps_file(
        client,
        rf"""
$ErrorActionPreference = 'Stop'
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
New-Item -ItemType Directory -Force -Path C:\apps | Out-Null
if (Test-Path '{APP_ROOT}\.git') {{
  Set-Location '{APP_ROOT}'
  git fetch --all
  git reset --hard origin/main
}} else {{
  if (Test-Path '{APP_ROOT}') {{ Remove-Item -Recurse -Force '{APP_ROOT}' }}
  git clone {REPO} '{APP_ROOT}'
}}
Set-Location '{APP_ROOT}\frontend'
npm ci
npm run build
if (-not (Test-Path '{APP_ROOT}\frontend\dist\index.html')) {{ throw 'frontend build missing dist' }}
Write-Host 'FRONTEND_OK'
""",
        timeout=1800,
    )
    if code != 0:
        print("frontend build failed")
        return 1

    client.close()
    client = connect()

    # 3) python venv
    code, out, _ = run_ps_file(
        client,
        rf"""
$ErrorActionPreference = 'Stop'
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
Set-Location '{APP_ROOT}\server'
if (-not (Test-Path .venv)) {{ python -m venv .venv }}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt
Write-Host 'BACKEND_OK'
""",
        timeout=1200,
    )
    if code != 0:
        print("backend install failed")
        return 1

    client.close()
    client = connect()

    # 4) firewall, portproxy, start scripts, scheduled task
    code, out, _ = run_ps_file(
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
Set-Content -Path C:\apps\baicai-s5-auction\start-auction.ps1 -Value $startPs -Encoding UTF8

# stop old uvicorn if any
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | ForEach-Object {{
  if ($_.CommandLine -and $_.CommandLine -match 'uvicorn main:app') {{
    Write-Host ("Stopping old pid " + $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }}
}}
Start-Sleep -Seconds 2

# start detached
$arg = '-NoProfile -ExecutionPolicy Bypass -File C:\apps\baicai-s5-auction\start-auction.ps1'
Start-Process -FilePath 'powershell.exe' -ArgumentList $arg -WindowStyle Hidden

# scheduled task for reboot
Unregister-ScheduledTask -TaskName 'BaicaiS5Auction' -Confirm:$false -ErrorAction SilentlyContinue
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName 'BaicaiS5Auction' -Action $action -Trigger $trigger -Settings $settings -User 'SYSTEM' -RunLevel Highest -Force | Out-Null

Start-Sleep -Seconds 8
try {{
  $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/meta' -UseBasicParsing -TimeoutSec 15
  Write-Host ('META ' + $r.StatusCode + ' ' + $r.Content)
}} catch {{
  Write-Host ('LOCAL_META_FAIL ' + $_.Exception.Message)
  throw
}}
Write-Host 'DEPLOY_OK'
""",
        timeout=180,
    )

    client.close()
    if code != 0 or "DEPLOY_OK" not in out:
        print("start/verify failed")
        return 1

    # external check
    import urllib.request

    time.sleep(2)
    try:
        with urllib.request.urlopen(f"http://{HOST}/api/meta", timeout=20) as resp:
            print("EXTERNAL_META", resp.status, resp.read().decode())
    except Exception as e:
        print("EXTERNAL_META_FAIL", e)
        print("Hint: open TCP 80 in Tencent Cloud Lighthouse firewall if needed")
        return 2

    print("\nDONE http://115.159.85.157/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
