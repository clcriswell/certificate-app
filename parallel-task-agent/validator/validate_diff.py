import subprocess
import sys
from pathlib import Path


def run(cmd: str, cwd: Path) -> None:
    print(f"[validator] {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def validate(repo_path: Path) -> None:
    run("black --check .", repo_path)
    run("pylint $(git ls-files '*.py')", repo_path)
    run("eslint $(git ls-files '*.js')", repo_path)
    run("pytest -q", repo_path)


if __name__ == "__main__":
    validate(Path.cwd())
