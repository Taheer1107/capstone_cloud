import requests
import time
import subprocess
import os
import atexit

app_proc = subprocess.Popen(["python", "backend.py"])
atexit.register(app_proc.kill)

time.sleep(3)

print("Testing app connection...")
try:
    res = requests.get("http://127.0.0.1:5000/doctors")
    if res.status_code == 200:
        print("Backend up. Test passed.")
    else:
        print("Tests failed.")
except Exception as e:
    print(f"Failed to connect: {e}")

print("Test complete.")
