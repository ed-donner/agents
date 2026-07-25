import subprocess
result = subprocess.run(["python", "-m", "unittest", "test_account_backend.py"], capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RC:", result.returncode)
