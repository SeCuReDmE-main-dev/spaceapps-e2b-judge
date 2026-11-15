"""Zero-leak credential loader for E2B and Gemini API keys.

I read keys in the following priority order:
  1. Process environment variables (`E2B_API_KEY`, `GEMINI_API_KEY`)
  2. Custom `.env` path specified by `SPACEAPPS_ENV_FILE` (if set)
  3. `.env` in the current working directory

I never print, log, or persist secret values.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def _parse_env_file(path: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    if not path.is_file():
        return found
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw or raw.lstrip().startswith("#"):
            continue
        m = _LINE.match(raw)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        if v:
            found[k] = v
    return found


def load_keys(*names: str, env_file: Path | None = None) -> dict[str, str]:
    """Load required keys from environment or `.env` without echoing values."""
    wanted = set(names)
    found: dict[str, str] = {}

    candidate_files: list[Path] = []
    if env_file is not None:
        candidate_files.append(env_file)
    custom_env = os.environ.get("SPACEAPPS_ENV_FILE", "").strip()
    if custom_env:
        candidate_files.append(Path(custom_env))
    candidate_files.append(Path.cwd() / ".env")

    file_Map: dict[str, str] = {}
    for p in reversed(candidate_files):
        file_Map.update(_parse_env_file(p))

    for k in wanted:
        val = os.environ.get(k, "").strip() or file_Map.get(k, "").strip()
        if val:
            found[k] = val

    missing = sorted(wanted - found.keys())
    if missing:
        raise RuntimeError(
            f"Missing required environment keys: {missing}. "
            "Export them in your shell or create a .env file (see .env.example)."
        )
    return found
