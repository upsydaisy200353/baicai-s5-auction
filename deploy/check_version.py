"""Check server frontend version"""
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

Write-Host "=== Check frontend dist files ==="
Get-ChildItem "C:\apps\baicai-s5-auction\frontend\dist" | Select-Object Name, Length, LastWriteTime

Write-Host "`n=== Check if isEditing is in the code ==="
Select-String -Path "C:\apps\baicai-s5-auction\frontend\dist\assets\*.js" -Pattern "isEditing" -Quiet

Write-Host "`n=== Check if onSubmit function exists ==="
Select-String -Path "C:\apps\baicai-s5-auction\frontend\dist\assets\*.js" -Pattern "onSubmit" -Quiet

Write-Host "`n=== Check file size ==="
Get-ChildItem "C:\apps\baicai-s5-auction\frontend\dist\assets\*.js" | Select-Object Name, Length

Write-Host "`n=== Local build time ==="
Get-Item "C:\apps\baicai-s5-auction\frontend\dist\index.html" | Select-Object LastWriteTime
'''

    sftp = client.open_sftp()
    with sftp.file(r"C:\apps\check_version.ps1", "w") as f:
        f.write(script.replace("\n", "\r\n"))
    sftp.close()

    _, stdout, stderr = client.exec_command(
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "C:\apps\check_version.ps1"',
        timeout=60
    )
    print("stdout:", stdout.read().decode("gbk", errors="replace"))
    print("stderr:", stderr.read().decode("gbk", errors="replace"))

    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
