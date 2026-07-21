import paramiko
import time
import urllib.request

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, 22, USER, PASSWORD, timeout=30)

cmd = 'powershell -Command "netstat -ano | findstr :8000"'
_, stdout, stderr = client.exec_command(cmd)
print("8000 port:")
print(stdout.read().decode())

cmd = 'powershell -Command "Invoke-WebRequest -Uri http://127.0.0.1:8000/api/meta -UseBasicParsing -TimeoutSec 10 | Select-Object -ExpandProperty Content"'
_, stdout, stderr = client.exec_command(cmd, timeout=30)
print("\nLocal meta via 8000:")
try:
    print(stdout.read().decode())
except:
    print("stdout decode error")
try:
    print("\nstderr:", stderr.read().decode('gbk', errors='replace'))
except:
    print("stderr decode error")

client.close()

time.sleep(2)

print("\n=== External test ===")
try:
    with urllib.request.urlopen(f"http://{HOST}/api/meta", timeout=20) as resp:
        print("External via 80:", resp.status, resp.read().decode())
except Exception as e:
    print("External via 80 failed:", e)

try:
    with urllib.request.urlopen(f"http://{HOST}:8000/api/meta", timeout=20) as resp:
        print("External via 8000:", resp.status, resp.read().decode())
except Exception as e:
    print("External via 8000 failed:", e)
