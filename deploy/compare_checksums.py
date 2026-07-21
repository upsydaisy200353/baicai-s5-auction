"""Compare local and server file checksums."""
import hashlib
import os

import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"
APP_ROOT = r"C:\apps\baicai-s5-auction"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def local_md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def main():
    # Local files
    files = [
        r"server\main.py",
        r"server\auction_engine.py",
        r"server\auth.py",
        r"server\db.py",
        r"frontend\dist\index.html",
    ]

    dist_assets = os.path.join(PROJECT_ROOT, "frontend", "dist", "assets")
    for f in os.listdir(dist_assets):
        if f.endswith(".js") or f.endswith(".css"):
            files.append(f"frontend/dist/assets/{f}")

    print("=== LOCAL ===")
    local_hashes = {}
    for f in files:
        p = os.path.join(PROJECT_ROOT, f)
        if os.path.isfile(p):
            h = local_md5(p)
            local_hashes[f] = h
            print(f"{h}  {f}")
        else:
            print(f"MISSING       {f}")

    # Server files
    print("\n=== SERVER ===")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, 22, USER, PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)

    # Get server-side asset files
    _, stdout, _ = c.exec_command(
        f'powershell -NoProfile -c "Get-ChildItem \\"{APP_ROOT}\\frontend\\dist\\assets\\" -Name"'
    )
    server_assets = stdout.read().decode("utf-8", "replace").strip().split("\n")
    for a in server_assets:
        a = a.strip()
        if a.endswith(".js") or a.endswith(".css"):
            sf = f"frontend/dist/assets/{a}"
            if sf not in files:
                files.append(sf)

    server_hashes = {}
    for f in files:
        p = os.path.join(APP_ROOT, f)
        cmd = (
            f'powershell -NoProfile -c "if (Test-Path \\"{p}\\") {{ '
            f'(Get-FileHash -Algorithm MD5 \\"{p}\\").Hash.ToLower() }} '
            f'else {{ \\"MISSING\\" }}"'
        )
        _, stdout, _ = c.exec_command(cmd)
        h = stdout.read().decode("utf-8", "replace").strip()
        server_hashes[f] = h
        print(f"{h}  {f}")

    c.close()

    # Compare
    print("\n=== COMPARISON ===")
    all_match = True
    for f in files:
        lh = local_hashes.get(f, "MISSING")
        sh = server_hashes.get(f, "MISSING")
        match = "OK" if lh == sh else "DIFF"
        if lh != sh:
            all_match = False
        print(f"  [{match}] {f}")
        if lh != sh:
            print(f"         local:  {lh}")
            print(f"         server: {sh}")

    print()
    if all_match:
        print("RESULT: All files match!")
    else:
        print("RESULT: Some files differ!")

    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
