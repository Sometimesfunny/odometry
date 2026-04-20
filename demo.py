
#!/usr/bin/env python3
import subprocess, sys

def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)

run([sys.executable, "data/generate_synthetic_data.py"])
run([sys.executable, "-m", "src.runner", "--mode", "adaptive", "--profile", "wifi", "--start", "0", "--end", "200", "--step", "10"])
for mode, prof in [("local","wifi"), ("remote","4g"), ("hybrid","radio")]:
    run([sys.executable, "-m", "src.runner", "--mode", mode, "--profile", prof, "--start", "0", "--end", "200", "--step", "10"])
