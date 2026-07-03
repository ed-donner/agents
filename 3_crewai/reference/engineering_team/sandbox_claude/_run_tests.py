import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "unittest", "test_backend", "-v"],
    capture_output=True,
    text=True,
)
output = (
    "RETURNCODE: " + str(result.returncode) + "\n"
    + "STDOUT:\n" + result.stdout + "\n"
    + "STDERR:\n" + result.stderr + "\n"
)
with open("test_output.txt", "w") as f:
    f.write(output)

# Print only a short summary so stdout doesn't get filtered.
last_lines = (result.stderr or result.stdout).strip().splitlines()[-20:]
for line in last_lines:
    print(line)
print("RC=" + str(result.returncode))
