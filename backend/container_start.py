"""Run both Python services in one network namespace to preserve loopback isolation."""
import subprocess
import sys
import os
import time
children = []
try:
    for module, port, host in [('backend.receiver:app', '8766', '127.0.0.1'), ('backend.app:app', os.getenv('PORT','8765'), '0.0.0.0')]:
        children.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', module, '--host', host, '--port', port]))
    while all(child.poll() is None for child in children): time.sleep(1)
finally:
    for child in children:
        child.terminate()
    for child in children: child.wait()
