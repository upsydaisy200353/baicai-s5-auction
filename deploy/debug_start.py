import paramiko

HOST = "115.159.85.157"
USER = "Administrator"
PASSWORD = "sssss3.14159"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, 22, USER, PASSWORD, timeout=30)

cmd = 'powershell -Command "Get-Content C:\\apps\\baicai-s5-auction\\start-auction.ps1"'
_, stdout, stderr = client.exec_command(cmd)
print("Start script:")
print(stdout.read().decode())

cmd = 'powershell -Command "cd C:\\apps\\baicai-s5-auction\\server; & .\\.venv\\Scripts\\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 2>&1"'
_, stdout, stderr = client.exec_command(cmd, timeout=60)
print("\nStarting uvicorn (60s timeout)...")
try:
    print("stdout:", stdout.read().decode())
except:
    print("stdout decode error")
try:
    print("stderr:", stderr.read().decode('gbk', errors='replace'))
except:
    print("stderr decode error")

client.close()
