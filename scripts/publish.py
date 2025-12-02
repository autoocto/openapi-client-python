#!/usr/bin/env python3
"""Publish distributions to PyPI using a token read from a .env file.

Usage examples:
  python scripts/publish.py --env-file .env         # upload using token from .env
  python scripts/publish.py --env-file .env --test  # upload to TestPyPI
  python scripts/publish.py --env-file .env --build # run local build before uploading

The script looks for a token in the provided env file under one of these keys
in order: `PYPI_API_TOKEN`, `TWINE_PASSWORD`, `PYPITOKEN`, `API_TOKEN`.
If a token is found it will set `TWINE_USERNAME=__token__` and
`TWINE_PASSWORD=<token>` in the environment and call `twine upload`.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


def parse_env_file(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    with path.open() as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            data[k.strip()] = v
    return data


def find_token(env: Dict[str, str]) -> Optional[str]:
    for key in ("PYPI_API_TOKEN", "TWINE_PASSWORD", "PYPITOKEN", "API_TOKEN"):
        if key in env and env[key]:
            return env[key]
    return None


def run(cmd: list[str], env: dict[str, str] | None = None) -> int:
    print("Running:", " ".join(map(str, cmd)))
    result = subprocess.run(cmd, env=env)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish distributions to PyPI using a token from a .env file")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file containing the API token")
    parser.add_argument("--dist", default="dist", help="Path to the distribution directory")
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI instead of PyPI")
    parser.add_argument("--build", action="store_true", help="Run the project build before uploading")
    parser.add_argument("--yes", "-y", action="store_true", help="Don't prompt for confirmation")
    args = parser.parse_args()

    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Error: env file not found: {env_path}")
        return 2

    env = parse_env_file(env_path)
    token = find_token(env)
    if not token:
        print("Error: no API token found in env file. Set PYPI_API_TOKEN or TWINE_PASSWORD.")
        return 3

    project_root = Path.cwd()

    if args.build:
        build_cmd = [sys.executable, str(project_root / "build.py"), "build"]
        if run(build_cmd) != 0:
            print("Build failed. Aborting upload.")
            return 4

    dist_dir = project_root / args.dist
    if not dist_dir.exists() or not any(dist_dir.iterdir()):
        print(f"Error: no distribution files found in {dist_dir}. Run build first.")
        return 5

    dists = sorted([str(p) for p in dist_dir.glob("*") if p.is_file()])
    print("Distributions to upload:")
    for p in dists:
        print(" -", p)

    if not args.yes:
        resp = input("Proceed with upload? [y/N]: ").strip().lower()
        if resp not in ("y", "yes"):
            print("Aborted by user.")
            return 0

    run_env = os.environ.copy()
    run_env["TWINE_USERNAME"] = "__token__"
    run_env["TWINE_PASSWORD"] = token

    if args.test:
        repo_url = "https://test.pypi.org/legacy/"
        cmd = [sys.executable, "-m", "twine", "upload", "--repository-url", repo_url] + dists
    else:
        cmd = [sys.executable, "-m", "twine", "upload"] + dists

    try:
        rc = run(cmd, env=run_env)
        if rc == 0:
            print("Upload completed successfully.")
            return 0
        else:
            print(f"twine failed with exit code {rc}")
            return rc
    except KeyboardInterrupt:
        print("Interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
