"""Deploy full application"""
from __future__ import annotations

import os
import sys
import zipfile

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"
APP_ROOT = r"C:\apps\baicai-s5-auction"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def connect() -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        HOST, 22, USER, PASSWORD, timeout=30,
        allow_agent=False, look_for_keys=False
    )
    return c


def make_deploy_zip() -> str:
    zip_path = os.path.join(PROJECT_ROOT, "deploy", "full-deploy.zip")
    print(f"Creating full zip: {zip_path}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
        dist_dir = os.path.join(frontend_dir, "dist")

        for root, dirs, files in os.walk(dist_dir):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, PROJECT_ROOT)
                zf.write(src, rel)

        server_dir = os.path.join(PROJECT_ROOT, "server")
        for root, dirs, files in os.walk(server_dir):
            for f in files:
                if f.endswith(".py"):
                    src = os.path.join(root, f)
                    rel = os.path.relpath(src, PROJECT_ROOT)
                    zf.write(src, rel)

    size = os.path.getsize(zip_path)
    print(f"Zip created: {size / (1024 * 1024):.2f} MB")
    return zip_path


def run_ps(client: paramiko.SSHClient, script: str, timeout: int = 120) -> tuple[int, str]:
    sftp = client.open_sftp()
    try:
        remote = r"C:\apps\_deploy_full.ps1"
        with sftp.file(remote, "w") as f:
            f.write(script.replace("\n", "\r\n"))
    finally:
        sftp.close()

    _, stdout, stderr = client.exec_command(
        f'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\\apps\\_deploy_full.ps1"',
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
    sftp.put(zip_path, r"C:\apps\full-deploy.zip")
    sftp.close()
    print("upload done")

    code, out = run_ps(
        client,
        rf"""
$ErrorActionPreference = 'Stop'

Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

$tempDir = 'C:\apps\_full_temp'
if (Test-Path $tempDir) {{ Remove-Item -Recurse -Force $tempDir }}
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
Expand-Archive -Path 'C:\apps\full-deploy.zip' -DestinationPath $tempDir -Force

if (Test-Path '{APP_ROOT}\frontend') {{ Remove-Item -Recurse -Force '{APP_ROOT}\frontend' }}
Copy-Item -Path "$tempDir\frontend" -Destination '{APP_ROOT}' -Recurse -Force

$serverFiles = Get-ChildItem -Path "$tempDir\server\*.py" -File
foreach ($f in $serverFiles) {{
  Copy-Item -Path $f.FullName -Destination '{APP_ROOT}\server' -Force
}}

Remove-Item -Recurse -Force $tempDir
Write-Host 'DEPLOY_OK'

$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:80,http://127.0.0.1"
Set-Location "{APP_ROOT}\server"
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 80" -WindowStyle Hidden

Start-Sleep -Seconds 8
Write-Host '=== Port 80 ==='
netstat -ano | findstr ":80.*LISTENING"

Write-Host '`n=== Test local ==='
try {{
  $r = Invoke-WebRequest -Uri "http://127.0.0.1/api/meta" -UseBasicParsing -TimeoutSec 5
  Write-Host "OK: $($r.StatusCode)"
}} catch {{
  Write-Host "FAIL: $_"
}}
""",
        timeout=300,
    )
    if code != 0:
        return 1

    client.close()
    print("\nFull deployment completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
