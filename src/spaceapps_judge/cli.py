"""SpaceApps E2B Judge v3.0 — Host Orchestrator & CLI.

Architecture:
  - Wave 1 (1 isolated Probe MicroVM, zero LLM access):
      Runs deterministic eligibility & engineering probes (`G-01..G-09`, `E-01..E-08`),
      Playwright headless browser checks, clean-clone pytest/frontend build, and URL citation checks.
  - Wave 2 (N parallel isolated Judge MicroVMs, default 5):
      Each judge (default: generic institutional roles; or any 1..10 judges from `judges.json`)
      runs in its own MicroVM with a prompt-enforced 350-word triage excerpt (for Local/Exec tiers),
      ranks a blind 10-project cohort (`SYNTH_ARCH_01..09` + candidate), and produces a 5-part debrief.
  - Wave 3 (Deterministic Anti-Hallucination Verifier & Report Generator):
      Validates every verbatim quote against the submission corpus and Wave 1 evidence ledger,
      computes Kendall tau concordance on the 9 synthetic calibration archetypes, and writes `JUDGEMENT_REPORT.md`.

Any hackathon: `hackathon_settings.json` (gates, K criteria, awards), `hackathon_rules.md` (judging guide),
`challenge_brief.md` and `judges.json` are auto-detected in the submission folder (or passed by flag).
Without them, the NASA Space Apps 2026 v3.0 defaults apply unchanged.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path

from e2b import Sandbox

from spaceapps_judge.envkeys import load_keys
from spaceapps_judge.vm.hackathon_config import (
    CHALLENGE_FILENAME,
    DEFAULT_JUDGE_ORDER,
    DEFAULT_JUDGES,
    JUDGES_FILENAME,
    RULES_FILENAME,
    SETTINGS_FILENAME,
    criterion_names,
    default_settings,
    load_judges_file,
    load_settings_file,
    max_total,
)

PKG_DIR = Path(__file__).resolve().parent
JUDGE_ORDER = list(DEFAULT_JUDGE_ORDER)
DEFAULT_JUDGING_GUIDE = PKG_DIR / "rubric" / "judging_guide_2026.md"
DEFAULT_CHALLENGE_BRIEF = PKG_DIR / "rubric" / "challenge_martian_map_2026.md"


def _pick(explicit: Path | None, sub_dir: Path, filename: str, flag: str) -> tuple[Path | None, str]:
    """Explicit flag > auto-detected file in the submission folder > None (packaged default)."""
    if explicit is not None:
        p = explicit.resolve()
        if not p.is_file():
            raise SystemExit(f"{flag} file not found: {p}")
        return p, f"{flag} ({p.name})"
    auto = sub_dir / filename
    if auto.is_file():
        return auto, f"auto-detected {filename} in submission folder"
    return None, "default (NASA Space Apps 2026)"


def resolve_run_config(
    sub_dir: Path,
    hackathon_settings: Path | None = None,
    judging_guide: Path | None = None,
    challenge_rubric: Path | None = None,
    judges_config: Path | None = None,
) -> dict:
    """Resolve and validate every hackathon/judge input before any VM is created (fail fast on bad JSON)."""
    settings_path, settings_src = _pick(hackathon_settings, sub_dir, SETTINGS_FILENAME, "--hackathon-settings")
    guide_path, guide_src = _pick(judging_guide, sub_dir, RULES_FILENAME, "--judging-guide")
    challenge_path, challenge_src = _pick(challenge_rubric, sub_dir, CHALLENGE_FILENAME, "--challenge-rubric")
    judges_path, judges_src = _pick(judges_config, sub_dir, JUDGES_FILENAME, "--judges-config")
    try:
        settings = load_settings_file(settings_path) if settings_path else default_settings()
        judges = (
            load_judges_file(judges_path, settings["hackathon_name"]) if judges_path else dict(DEFAULT_JUDGES)
        )
    except ValueError as e:
        raise SystemExit(f"Invalid hackathon configuration: {e}") from None
    return {
        "settings_path": settings_path,
        "judges_path": judges_path,
        "guide_path": guide_path or DEFAULT_JUDGING_GUIDE,
        "challenge_path": challenge_path or DEFAULT_CHALLENGE_BRIEF,
        "settings": settings,
        "judges": judges,
        "judge_order": list(judges),
        "sources": {
            "hackathon_settings": settings_src,
            "judging_guide": guide_src,
            "challenge_brief": challenge_src,
            "judges": judges_src,
        },
    }


def build_bundle(cfg: dict, sub_dir: Path) -> dict[str, Path]:
    """Remote VM path -> local file. Explicit config files override same-named files from the submission folder."""
    bundle: dict[str, Path] = {
        "/judge/rubric/judging_guide_2026.md": cfg["guide_path"],
        "/judge/rubric/challenge_martian_map_2026.md": cfg["challenge_path"],
        "/judge/vm/probes.py": PKG_DIR / "vm" / "probes.py",
        "/judge/vm/calibration_cohort.py": PKG_DIR / "vm" / "calibration_cohort.py",
        "/judge/vm/hackathon_config.py": PKG_DIR / "vm" / "hackathon_config.py",
        "/judge/vm/panel.py": PKG_DIR / "vm" / "panel.py",
        "/judge/vm/report.py": PKG_DIR / "vm" / "report.py",
    }
    for p in sub_dir.iterdir():
        if p.is_file():
            bundle[f"/judge/input/{p.name}"] = p
    if cfg["settings_path"] is not None:
        bundle[f"/judge/input/{SETTINGS_FILENAME}"] = cfg["settings_path"]
    if cfg["judges_path"] is not None:
        bundle[f"/judge/input/{JUDGES_FILENAME}"] = cfg["judges_path"]
    return bundle


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(
    sb: Sandbox,
    cmd: str,
    timeout: int,
    echo,
    envs: dict[str, str] | None = None,
) -> int:
    echo(f"\n$ {cmd}\n")
    r = sb.commands.run(
        cmd,
        timeout=timeout,
        envs=envs or {},
        on_stdout=lambda d: echo(d),
        on_stderr=lambda d: echo(d),
    )
    return r.exit_code


def create_sandbox(
    api_key: str,
    template: str | None,
    timeout: int,
    metadata: dict[str, str],
    echo=None,
) -> Sandbox:
    """Create an E2B Sandbox using the requested template, logging any fallback to base Sandbox."""
    if template:
        try:
            return Sandbox.create(
                template=template,
                timeout=timeout,
                api_key=api_key,
                metadata=metadata,
            )
        except Exception as e:
            if echo is not None:
                echo(
                    f"[Template] Custom template '{template}' unavailable ({type(e).__name__}: {e}); "
                    "falling back to base E2B sandbox.\n"
                )
    return Sandbox.create(
        timeout=timeout,
        api_key=api_key,
        metadata=metadata,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="spaceapps-judge",
        description=(
            "Run SpaceApps E2B Judge v3.0 (Calibrated 10-Project Cohort & N Isolated Judge MicroVMs; "
            "NASA Space Apps defaults or any hackathon via hackathon_settings.json + judges.json)."
        ),
    )
    ap.add_argument(
        "submission_dir",
        type=Path,
        help=(
            "Folder containing submission.json, submission_text.md, optional demo file, and optional "
            "hackathon_settings.json / hackathon_rules.md / challenge_brief.md / judges.json (auto-detected)."
        ),
    )
    ap.add_argument("--model", default="gemini-3.8-flash", help="Default Gemini model ID.")
    ap.add_argument("--fallback", default="gemini-3.5-flash", help="Fallback Gemini model ID.")
    ap.add_argument("--gemini-cli", default="0.68.0", help="Gemini CLI npm package version.")
    ap.add_argument(
        "--template",
        default=os.environ.get("E2B_JUDGE_TEMPLATE", ""),
        help="Optional pre-baked E2B template ID/name (e.g. spaceapps-judge-v3).",
    )
    ap.add_argument(
        "--challenge-rubric",
        type=Path,
        default=None,
        help=(
            "Challenge brief markdown (default: <submission_dir>/challenge_brief.md if present, "
            "else the packaged Martian Map 2026 brief)."
        ),
    )
    ap.add_argument(
        "--judging-guide",
        type=Path,
        default=None,
        help=(
            "Hackathon rules / judging guide markdown (default: <submission_dir>/hackathon_rules.md if present, "
            "else the packaged NASA Space Apps 2026 judging guide)."
        ),
    )
    ap.add_argument(
        "--hackathon-settings",
        type=Path,
        default=None,
        help=(
            "hackathon_settings.json: gates, K criteria and awards (default: <submission_dir>/hackathon_settings.json "
            "if present, else NASA Space Apps 2026 defaults). See templates/hackathon_settings_template.json."
        ),
    )
    ap.add_argument(
        "--judges-config",
        type=Path,
        default=None,
        help=(
            "judges.json with 1..10 judge personas (default: <submission_dir>/judges.json if present, "
            "else the 5 NASA v3.0 role personas). See templates/judge_panel_template.json."
        ),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path.cwd() / "reports" / "judge",
        help="Base output directory for generated reports.",
    )
    ap.add_argument(
        "--reuse-wave1",
        type=Path,
        default=None,
        help="Path to an existing report folder to reuse Wave 1 evidence.json & screenshots.",
    )
    ap.add_argument("--env-file", type=Path, default=None, help="Optional path to .env file.")
    a = ap.parse_args(argv)

    sub_dir = a.submission_dir.resolve()
    sub_json = sub_dir / "submission.json"
    if not sub_json.is_file():
        raise SystemExit(f"submission.json not found in {sub_dir}")
    sub = json.loads(sub_json.read_text(encoding="utf-8"))

    cfg = resolve_run_config(
        sub_dir,
        hackathon_settings=a.hackathon_settings,
        judging_guide=a.judging_guide,
        challenge_rubric=a.challenge_rubric,
        judges_config=a.judges_config,
    )
    judge_order: list[str] = cfg["judge_order"]
    settings = cfg["settings"]

    keys = load_keys("E2B_API_KEY", "GEMINI_API_KEY", env_file=a.env_file)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dest = a.out.resolve() / f"{sub_dir.name}_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    log = (dest / "run.log").open("w", encoding="utf-8")
    log_lock = threading.Lock()

    def echo(s: str) -> None:
        with log_lock:
            sys.stdout.write(s)
            sys.stdout.flush()
            log.write(s)
            log.flush()

    bundle = build_bundle(cfg, sub_dir)

    manifest = {
        "project_title": sub.get("project_title"),
        "model": a.model,
        "fallback_model": a.fallback,
        "gemini_cli_version": a.gemini_cli,
        "e2b_template": a.template or "base",
        "parallel_vms": True,
        "judges": judge_order,
        "judge_tiers": {jid: cfg["judges"][jid]["tier"] for jid in judge_order},
        "hackathon_name": settings["hackathon_name"],
        "criteria": criterion_names(settings),
        "max_total": max_total(settings),
        "hackathon_settings": {k: v for k, v in settings.items() if k != "is_default"},
        "config_sources": cfg["sources"],
        "host_started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sha256": {remote: sha256_file(local) for remote, local in sorted(bundle.items())},
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    echo(
        f"=== SPACEAPPS E2B JUDGE v3.0 START ({len(judge_order)} Parallel VMs · {settings['hackathon_name']} · "
        f"{len(manifest['criteria'])} criteria /{manifest['max_total']}) -> {dest} ===\n"
    )
    for label, src in cfg["sources"].items():
        echo(f"[Config] {label}: {src}\n")

    # --------------------------------------------------------- WAVE 1: PROBE VM
    if a.reuse_wave1 and (a.reuse_wave1.resolve() / "evidence.json").exists():
        reuse_dir = a.reuse_wave1.resolve()
        echo(f"[Wave 1] Reusing evidence from {reuse_dir}\n")
        for name in (
            "evidence.json",
            "screenshot_desktop.png",
            "screenshot_interaction.png",
            "screenshot_mobile.png",
        ):
            if (reuse_dir / name).exists():
                (dest / name).write_bytes((reuse_dir / name).read_bytes())
    else:
        sb_probe: Sandbox | None = None
        try:
            sb_probe = create_sandbox(
                api_key=keys["E2B_API_KEY"],
                template=a.template or None,
                timeout=3600,
                metadata={"purpose": "spaceapps-judge-probe"},
                echo=echo,
            )
            echo(f"[Wave 1] Probe VM {sb_probe.sandbox_id} created\n")
            for remote, local in bundle.items():
                sb_probe.files.write(remote, local.read_bytes())
            sb_probe.files.write("/judge/out/manifest.json", json.dumps(manifest, indent=1))

            run_cmd(
                sb_probe,
                "set -e; mkdir -p /judge/out /judge/work; "
                "python3 -c 'import pypdf, pptx, langdetect, playwright' 2>/dev/null || ("
                "pip install -q pypdf python-pptx langdetect imageio-ffmpeg playwright >/tmp/pip.log 2>&1 && "
                "python3 -m playwright install --with-deps chromium >/tmp/pw.log 2>&1); "
                "echo PROBE_SETUP_OK",
                900,
                echo,
            )
            run_cmd(sb_probe, "cd /judge && python3 vm/probes.py", 2400, echo)
        except Exception as e:
            echo(f"\n[Wave 1] PROBE VM ERROR: {type(e).__name__}: {e}\n")
        finally:
            if sb_probe is not None:
                for name in (
                    "evidence.json",
                    "screenshot_desktop.png",
                    "screenshot_interaction.png",
                    "screenshot_mobile.png",
                ):
                    try:
                        data = sb_probe.files.read(f"/judge/out/{name}", format="bytes")
                        (dest / name).write_bytes(bytes(data))
                    except Exception:
                        pass
                try:
                    sb_probe.kill()
                    echo(f"\n[Wave 1] Probe VM {sb_probe.sandbox_id} destroyed.\n")
                except Exception:
                    pass

    if not (dest / "evidence.json").exists():
        echo("\n[FATAL] evidence.json was not produced by Wave 1; aborting.\n")
        log.close()
        return 1

    # --------------------------------------------------------- WAVE 2: N PARALLEL JUDGE VMs
    api_gate = threading.Semaphore(2)
    api_last_call = [0.0]
    api_lock = threading.Lock()

    def acquire_staggered_slot() -> None:
        api_gate.acquire()
        with api_lock:
            now = time.time()
            wait_s = max(0.0, (api_last_call[0] + 5.0) - now)
            if wait_s > 0:
                time.sleep(wait_s)
            api_last_call[0] = time.time()

    def run_single_judge_vm(jid: str) -> tuple[str, dict]:
        sb_j: Sandbox | None = None
        try:
            sb_j = create_sandbox(
                api_key=keys["E2B_API_KEY"],
                template=a.template or None,
                timeout=1800,
                metadata={"purpose": "spaceapps-judge-persona", "judge": jid},
                echo=echo,
            )
            echo(f"[Wave 2 / {jid}] Judge VM {sb_j.sandbox_id} created\n")
            for remote, local in bundle.items():
                sb_j.files.write(remote, local.read_bytes())
            sb_j.files.write("/judge/out/manifest.json", json.dumps(manifest, indent=1))
            for name in (
                "evidence.json",
                "screenshot_desktop.png",
                "screenshot_interaction.png",
                "screenshot_mobile.png",
            ):
                if (dest / name).exists():
                    sb_j.files.write(f"/judge/out/{name}", (dest / name).read_bytes())

            def j_echo(s: str) -> None:
                echo(f"[{jid}] {s}" if not s.startswith("\n") else s)

            run_cmd(
                sb_j,
                f"set -e; mkdir -p /judge/out /judge/work; "
                f"command -v gemini >/dev/null 2>&1 || npm i -g @google/gemini-cli@{a.gemini_cli} >/tmp/npm.log 2>&1; "
                f"gemini --version",
                600,
                j_echo,
            )
            fb_arg = f" {a.fallback}" if a.fallback else " ''"
            acquire_staggered_slot()
            try:
                run_cmd(
                    sb_j,
                    f"cd /judge && python3 vm/panel.py {a.model}{fb_arg} --judge {shlex.quote(jid)}",
                    1200,
                    j_echo,
                    envs={"GEMINI_API_KEY": keys["GEMINI_API_KEY"]},
                )
            finally:
                api_gate.release()

            raw_dir = dest / "raw_attempts" / jid
            raw_dir.mkdir(parents=True, exist_ok=True)
            for fname in (
                "prompt.md",
                "rest_attempt0.json",
                "rest_attempt0_err.txt",
                "rest_attempt1.json",
                "rest_attempt1_err.txt",
                "raw_attempt0.txt",
                "raw_attempt1.txt",
            ):
                try:
                    b = sb_j.files.read(f"/judge/panel/{jid}/{fname}", format="bytes")
                    (raw_dir / fname).write_bytes(bytes(b))
                except Exception:
                    pass

            raw_bytes = sb_j.files.read(f"/judge/out/panel_{jid}.json", format="bytes")
            (dest / f"panel_{jid}.json").write_bytes(bytes(raw_bytes))
            return jid, json.loads(bytes(raw_bytes).decode("utf-8"))
        except Exception as e:
            echo(f"\n[Wave 2 / {jid}] JUDGE VM ERROR: {type(e).__name__}: {e}\n")
            return jid, {
                "judge": jid,
                "_error": f"VM failure: {type(e).__name__}: {e}",
                "scores": [],
                "strengths": [],
                "weaknesses": [],
                "fixes_before_deadline": [],
                "award_fit": [],
            }
        finally:
            if sb_j is not None:
                try:
                    sb_j.kill()
                    echo(f"[Wave 2 / {jid}] Judge VM {sb_j.sandbox_id} destroyed.\n")
                except Exception:
                    pass

    panel_map: dict[str, dict] = {}
    echo(f"\n[Wave 2] Launching {len(judge_order)} judge VMs ({len(judge_order)} Parallel VMs): {judge_order}\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(len(judge_order), 8))) as pool:
        futs = [pool.submit(run_single_judge_vm, jid) for jid in judge_order]
        for fut in concurrent.futures.as_completed(futs):
            jid, data = fut.result()
            panel_map[jid] = data

    ordered_panel = [panel_map[jid] for jid in judge_order if jid in panel_map]
    (dest / "panel_raw.json").write_text(
        json.dumps(ordered_panel, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    # --------------------------------------------------------- WAVE 3: REPORT AGGREGATION
    echo("\n[Wave 3] Running deterministic anti-hallucination validator & report generator...\n")
    r_rep = subprocess.run(
        [sys.executable, str(PKG_DIR / "vm" / "report.py"), str(dest), str(sub_dir)],
        capture_output=True,
        text=True,
    )
    echo(r_rep.stdout + r_rep.stderr)
    echo(f"\n=== SPACEAPPS E2B JUDGE v3.0 COMPLETE -> {dest} ===\n")
    log.close()
    return r_rep.returncode


if __name__ == "__main__":
    raise SystemExit(main())
