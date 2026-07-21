"""Full deployment with database migration"""
from __future__ import annotations

import os
import sys
import zipfile
import time

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
    zip_path = os.path.join(PROJECT_ROOT, "deploy", "final-deploy.zip")
    print(f"Creating deployment zip: {zip_path}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        frontend_dist = os.path.join(PROJECT_ROOT, "frontend", "dist")
        for root, dirs, files in os.walk(frontend_dist):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, PROJECT_ROOT)
                zf.write(src, rel)

        server_dir = os.path.join(PROJECT_ROOT, "server")
        for f in os.listdir(server_dir):
            if f.endswith(".py"):
                src = os.path.join(server_dir, f)
                rel = os.path.relpath(src, PROJECT_ROOT)
                zf.write(src, rel)

    size = os.path.getsize(zip_path)
    print(f"Zip created: {size / (1024 * 1024):.2f} MB")
    return zip_path


def run_ps(client: paramiko.SSHClient, script: str, timeout: int = 120) -> tuple[int, str]:
    sftp = client.open_sftp()
    try:
        remote = r"C:\apps\_deploy_final.ps1"
        with sftp.file(remote, "w") as f:
            f.write(script.replace("\n", "\r\n"))
    finally:
        sftp.close()

    _, stdout, stderr = client.exec_command(
        f'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\\apps\\_deploy_final.ps1"',
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
    print("Connected to server, uploading...")

    sftp = client.open_sftp()
    sftp.put(zip_path, r"C:\apps\final-deploy.zip")
    sftp.close()
    print("Upload completed")

    code, out = run_ps(
        client,
        rf"""
$ErrorActionPreference = 'Continue'

Write-Host "=== 1. Stop existing services ==="
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

Write-Host "`n=== 2. Extract deployment ==="
$tempDir = 'C:\apps\_final_temp'
if (Test-Path $tempDir) {{ Remove-Item -Recurse -Force $tempDir }}
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
Expand-Archive -Path 'C:\apps\final-deploy.zip' -DestinationPath $tempDir -Force

Write-Host "`n=== 3. Update frontend ==="
if (Test-Path '{APP_ROOT}\frontend') {{ Remove-Item -Recurse -Force '{APP_ROOT}\frontend' }}
Copy-Item -Path "$tempDir\frontend" -Destination '{APP_ROOT}' -Recurse -Force

Write-Host "`n=== 4. Update backend ==="
$serverFiles = Get-ChildItem -Path "$tempDir\server\*.py" -File
foreach ($f in $serverFiles) {{
  Copy-Item -Path $f.FullName -Destination '{APP_ROOT}\server' -Force
  Write-Host "Updated: $($f.Name)"
}}

Write-Host "`n=== 5. Database migration ==="
Set-Location "{APP_ROOT}\server"
& ".venv\Scripts\python.exe" migrate_online.py

Write-Host "`n=== 6. Cleanup ==="
Remove-Item -Recurse -Force $tempDir

Write-Host "`n=== 7. Start server ==="
$env:AUCTION_JWT_SECRET = "baicai-s5-tencent-jwt-change-after-deploy"
$env:CORS_ORIGINS = "http://115.159.85.157,http://127.0.0.1:80,http://127.0.0.1"
& ".venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 80

""",
        timeout=300,
    )
    if code != 0:
        return 1

    client.close()
    
    time.sleep(10)
    print("\n=== Testing external access ===")
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://{HOST}/api/meta", timeout=20)
        print("SUCCESS:", resp.status)
    except Exception as e:
        print("EXTERNAL FAIL:", e)

    print("\nDeployment completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
