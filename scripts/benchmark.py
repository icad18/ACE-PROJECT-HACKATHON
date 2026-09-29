import sys
import subprocess
import time


def run_benchmark():
    start_time = time.time()
    cmd = [sys.executable, "-m", "pytest"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start_time
        print(f"Benchmark completed in {elapsed:.2f}s")
        print(result.stdout)
        if result.returncode != 0:
            print("Errors:", result.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: pytest is not installed in the active Python environment.")
        return False


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
