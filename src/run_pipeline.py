import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def main():
    print("STEP 1: Fetching weather data")
    fetch_exit_code = run_script("fetch_weather.py")

    if fetch_exit_code != 0:
        print("Piepline stopped: weather fetch failed")
        return fetch_exit_code

    print("STEP 2: Loading weather data")
    return run_script("load_weather.py")


def run_script(script_name):
    script_path = PROJECT_ROOT / "src" / script_name
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
    )
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())