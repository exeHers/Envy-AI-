import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    script = root / "run_envy_windows.bat"
    process = subprocess.Popen(
        ["cmd", "/c", str(script), "--no-gui"],
        cwd=root,
    )
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
    return process.returncode


if __name__ == "__main__":
    sys.exit(main())
