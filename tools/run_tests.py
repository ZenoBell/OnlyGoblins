# FanGoblin modifications by ZenoBell, 2026-11-06. See CHANGES_FROM_UPSTREAM.md.
"""Run offline tests, isolating each Tk test in its own process."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONUTF8"] = "1"
    # Some Windows sandbox TEMP paths contain braces interpreted by Loguru.
    # Keep isolated test data in this ignored, predictable scratch parent instead.
    scratch = ROOT / ".build-tools"
    scratch.mkdir(exist_ok=True)
    env["TEMP"] = str(scratch)
    env["TMP"] = str(scratch)
    env["TMPDIR"] = str(scratch)
    with tempfile.TemporaryDirectory(prefix="onlygoblins-tests-", dir=scratch) as directory:
        work = Path(directory)
        command = [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q", "-p", "no:cacheprovider"]
        result = subprocess.run(command + ["-m", "not gui"], cwd=work, env=env)
        if result.returncode:
            return result.returncode
        collected = subprocess.run(command + ["--collect-only", "-m", "gui"], cwd=ROOT,
                                   env=env, capture_output=True, text=True, check=True)
        nodes = [line.strip() for line in collected.stdout.splitlines() if "::" in line and line.startswith("tests/")]
        for node in nodes:
            file, case = node.split("::", 1)
            result = subprocess.run([sys.executable, "-m", "pytest", str(ROOT / file) + "::" + case,
                                     "-q", "-p", "no:cacheprovider"], cwd=work, env=env)
            if result.returncode:
                return result.returncode
        print(f"All offline tests passed, including {len(nodes)} isolated GUI cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
