"""Repository hygiene, secret-leak, and persona-anonymity tests for spaceapps-e2b-judge."""

from __future__ import annotations

import re
from pathlib import Path

from spaceapps_judge.envkeys import load_keys

REPO_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_PATTERNS = [
    re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE),
    re.compile(r"Z:\\SecuredMe", re.IGNORECASE),
    re.compile(r"AIzaSy[A-Za-z0-9_\-]{30,}"),
    re.compile(r"e2b_[a-f0-9]{32,}", re.IGNORECASE),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    # Guard against real judge or competitor team names in public artifacts
    re.compile(
        r"\b(natasha\s+fee|natasha_thierry|schaeffer|satuelisa|thierry\s+marcoux|"
        r"joel\s+trudeau|brian\s+h?\.\s*day|brian_day|lakdawalla|marshall\s+r?\.\s*trautman|"
        r"trautman_laura|nicola\s+.*fox|nassouri|astrowrap|godzinauts|"
        r"bm_01_wanderer|bm_02_origen|bm_04_redpath)\b",
        re.IGNORECASE,
    ),
]

EXCLUDED_DIRS = {".git", "__pycache__", "reports", ".pytest_cache", ".ruff_cache", ".venv", "venv", "build", "dist"}


def test_required_public_files_exist() -> None:
    assert (REPO_ROOT / "README.md").is_file()
    assert (REPO_ROOT / "LICENSE").is_file()
    assert (REPO_ROOT / "pyproject.toml").is_file()
    assert (REPO_ROOT / ".env.example").is_file()
    assert (REPO_ROOT / "e2b_template" / "e2b.Dockerfile").is_file()
    assert (REPO_ROOT / "e2b_template" / "e2b.toml").is_file()


def test_env_example_is_safe_and_complete() -> None:
    env_ex = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "E2B_API_KEY=e2b_your_api_key_here" in env_ex
    assert "GEMINI_API_KEY=AIza_your_gemini_api_key_here" in env_ex
    for pat in FORBIDDEN_PATTERNS:
        assert pat.search(env_ex) is None


def test_no_local_paths_secrets_or_real_names_in_tracked_files() -> None:
    scanned = 0
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(REPO_ROOT).parts
        if any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in rel_parts):
            continue
        if p.name == "test_hygiene.py":
            continue
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".mp4"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        for pat in FORBIDDEN_PATTERNS:
            match = pat.search(text)
            assert match is None, (
                f"Forbidden pattern '{pat.pattern}' found in {p.relative_to(REPO_ROOT).as_posix()}: "
                f"{match.group(0)}"
            )
    assert scanned >= 15


def test_envkeys_loads_from_custom_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "E2B_API_KEY='test_e2b_dummy'\nGEMINI_API_KEY=\"test_gemini_dummy\"\n",
        encoding="utf-8",
    )
    keys = load_keys("E2B_API_KEY", "GEMINI_API_KEY", env_file=env_file)
    assert "E2B_API_KEY" in keys
    assert "GEMINI_API_KEY" in keys
