"""Deterministic probes run INSIDE the E2B VM. No LLM here.

Produces /judge/out/evidence.json : the only facts the judges may rely on.
Every fact gets a stable id (G-xx for eligibility gate, E-xx for evidence) and a tier ("ALL" or "SME").
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path("/judge")
INP = ROOT / "input"
OUT = ROOT / "out"
WORK = ROOT / "work"
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

SUB = json.loads((INP / "submission.json").read_text(encoding="utf-8"))
SUB_TEXT = ""
if SUB.get("submission_text_file") and (INP / SUB["submission_text_file"]).exists():
    SUB_TEXT = (INP / SUB["submission_text_file"]).read_text(encoding="utf-8", errors="replace")

evidence: list[dict] = []


def add(kind: str, probe: str, status: str, fact: str, excerpt: str = "", tier: str = "ALL") -> str:
    n = sum(1 for e in evidence if e["id"].startswith(kind)) + 1
    eid = f"{kind}-{n:02d}"
    evidence.append(
        {
            "id": eid,
            "probe": probe,
            "status": status,
            "tier": tier,
            "fact": fact,
            "excerpt": excerpt[:4000],
        }
    )
    print(f"[{eid}] {status:4} ({tier}) {probe}: {fact}", flush=True)
    return eid


def sh(cmd: str, timeout: int = 300, cwd: Path | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        return 124, f"TIMEOUT after {timeout}s\n{(e.stdout or b'')[-2000:]!r}"


# ---------------------------------------------------------------- GATE (G-xx)
def gate() -> None:
    missing = [
        f for f in ("project_title", "challenge", "public_url", "repo_url") if not SUB.get(f)
    ]
    if not SUB_TEXT.strip():
        missing.append("submission_text (project description)")
    add(
        "G",
        "required_fields",
        "FAIL" if missing else "PASS",
        f"Missing required submission fields: {missing}"
        if missing
        else "All required submission fields provided.",
    )

    url = SUB.get("public_url") or ""
    if url:
        code, out = sh(
            f"curl -sS -L -m 30 -o {WORK}/home.html -w '%{{http_code}} %{{url_effective}}' '{url}'",
            60,
        )
        parts = out.strip().split()
        http = parts[-2] if len(parts) >= 2 else "000"
        final = parts[-1] if parts else ""
        login = bool(re.search(r"login|signin|sign_in|accounts\.google|auth", final, re.I))
        ok = http == "200" and not login
        add(
            "G",
            "public_url_no_login",
            "PASS" if ok else "FAIL",
            f"GET {url} from an outside VM -> HTTP {http}, final URL {final}"
            + (" (login wall)" if login else ""),
        )
    else:
        add("G", "public_url_no_login", "FAIL", "No public project URL provided.")

    repo_url = SUB.get("repo_url") or ""
    if repo_url:
        code, out = sh(f"GIT_TERMINAL_PROMPT=0 git ls-remote --heads '{repo_url}'", 60)
        add(
            "G",
            "repo_public",
            "PASS" if code == 0 else "FAIL",
            f"Anonymous git ls-remote {repo_url} -> exit {code}",
            out[-400:],
        )
    else:
        add(
            "G",
            "repo_public",
            "INFO",
            "No repository URL provided (not strictly required if the public URL works).",
        )

    demo = SUB.get("demo_file")
    p = INP / demo if demo else None
    if not p or not p.exists():
        add(
            "G",
            "demo_limits",
            "FAIL",
            "No demo file provided (7-slide deck or <=30 s video is mandatory).",
        )
    else:
        ext = p.suffix.lower()
        if ext == ".pdf":
            from pypdf import PdfReader

            n = len(PdfReader(str(p)).pages)
            add(
                "G",
                "demo_limits",
                "PASS" if n <= 7 else "FAIL",
                f"Demo PDF has {n} slides/pages (limit 7).",
            )
        elif ext == ".pptx":
            from pptx import Presentation

            n = len(Presentation(str(p)).slides)
            add(
                "G",
                "demo_limits",
                "PASS" if n <= 7 else "FAIL",
                f"Demo PPTX has {n} slides (limit 7).",
            )
        elif ext in (".mp4", ".mov", ".webm", ".mkv"):
            import imageio_ffmpeg

            ff = imageio_ffmpeg.get_ffmpeg_exe()
            _, info = sh(f"'{ff}' -i '{p}' 2>&1", 60)
            m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
            secs = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else -1
            add(
                "G",
                "demo_limits",
                "PASS" if 0 < secs <= 30.0 else "FAIL",
                f"Demo video duration {secs:.2f} s (limit 30 s).",
            )
        else:
            add("G", "demo_limits", "FAIL", f"Unsupported demo format {ext}; cannot verify limits.")

    if SUB_TEXT.strip():
        from langdetect import DetectorFactory, detect_langs

        DetectorFactory.seed = 0
        langs = detect_langs(SUB_TEXT[:20000])
        top = langs[0]
        add(
            "G",
            "english_language",
            "PASS" if top.lang == "en" and top.prob > 0.9 else "FAIL",
            f"Submission text language detection: {[(ln.lang, round(ln.prob, 3)) for ln in langs]}",
        )

    nasa_terms = [
        "nasa",
        "jpl",
        "hirise",
        "mola",
        "ctx",
        "crism",
        "themis",
        "mars trek",
        "pds",
        "usgs",
        "mars reconnaissance orbiter",
        "mro",
        "mars global surveyor",
        "perseverance",
        "curiosity",
        "msl",
        "mars 2020",
        "rad ",
        "meda",
        "maven",
        "odyssey",
        "insight",
    ]
    low = SUB_TEXT.lower()
    hits = sorted({t.strip() for t in nasa_terms if t in low})
    add(
        "G",
        "nasa_data_cited",
        "PASS" if any(h in hits for h in ("nasa", "jpl", "pds")) or len(hits) >= 2 else "FAIL",
        f"NASA data/mission terms found in submission text: {hits}",
    )

    refs = bool(
        re.search(
            r"^\s*#*\s*(?:\d+[\.\)]\s*)?(references|sources|data sources|resources used)\b",
            SUB_TEXT,
            re.I | re.M,
        )
    )
    add(
        "G",
        "references_listed",
        "PASS" if refs else "FAIL",
        "A References/Sources section is present."
        if refs
        else "No References/Sources section found in submission text.",
    )
    ai = re.search(
        r"(use of (ai|artificial intelligence)|ai (tools|disclosure|usage|assistance)|generative ai|"
        r"\bllm\b|chatgpt|claude|gemini|copilot)",
        SUB_TEXT,
        re.I,
    )
    add(
        "G",
        "ai_disclosure",
        "PASS" if ai else "FAIL",
        f"AI usage disclosure found (matched '{ai.group(0)}')."
        if ai
        else "No AI usage disclosure found.",
    )

    add(
        "G",
        "deadline_context",
        "INFO",
        f"Judge run at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}; "
        "deadline Sunday Nov 15 2026 23:59 local time (Montreal, UTC-5).",
    )


# ------------------------------------------------------------- EVIDENCE (E-xx)
def site() -> None:
    url = SUB.get("public_url")
    if not url:
        return
    script = WORK / "shot.py"
    script.write_text(
        r"""
import json, re, sys, time
from playwright.sync_api import sync_playwright
url, out = sys.argv[1], sys.argv[2]
res = {"console_errors": [], "requests": [], "failed": [], "interaction": {}}
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp in (("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})):
        pg = b.new_page(viewport=vp)
        if name == "desktop":
            pg.on("console", lambda m: m.type == "error" and res["console_errors"].append(m.text[:300]))
            pg.on("requestfinished", lambda r: res["requests"].append(r.url[:200]))
            pg.on("requestfailed", lambda r: res["failed"].append(r.url[:200]))
        t0 = time.time()
        pg.goto(url, wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(4000)
        res[f"{name}_load_s"] = round(time.time() - t0, 2)
        pg.screenshot(path=f"{out}/screenshot_{name}.png", full_page=False)
        if name == "desktop":
            res["title"] = pg.title()
            before_text = pg.inner_text("body")
            res["text"] = before_text[:6000]
            els = pg.query_selector_all("button, [role=button], a")
            res["buttons"] = [e.inner_text()[:60] for e in els][:80]
            clicked_label = None
            for e in els:
                try:
                    lbl = (e.inner_text() or "").strip()
                    if lbl and re.search(r"sol|route|eva|4\s*m|16\s*m|64\s*m|hud|layer|plan|evaluate|3d|terrain|next|stop", lbl, re.I):
                        e.click(timeout=3000)
                        clicked_label = lbl[:60]
                        break
                except Exception:
                    continue
            if not clicked_label:
                for e in els:
                    try:
                        lbl = (e.inner_text() or "").strip()
                        if lbl:
                            e.click(timeout=3000)
                            clicked_label = lbl[:60]
                            break
                    except Exception:
                        continue
            pg.wait_for_timeout(1500)
            after_text = pg.inner_text("body")
            pg.screenshot(path=f"{out}/screenshot_interaction.png", full_page=False)
            res["interaction"] = {
                "clicked": clicked_label,
                "state_changed": after_text != before_text,
                "after_excerpt": after_text[:1500],
            }
    b.close()
print(json.dumps(res))
""",
        encoding="utf-8",
    )
    code, out = sh(f"python3 {script} '{url}' {OUT}", 180)
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except Exception:
        add(
            "E",
            "site_render",
            "FAIL",
            f"Headless browser could not render {url} (exit {code}).",
            out[-1500:],
        )
        return
    add(
        "E",
        "site_render",
        "PASS",
        f"Rendered {url}: title '{res.get('title')}', desktop load {res.get('desktop_load_s')} s, "
        f"mobile load {res.get('mobile_load_s')} s; screenshots screenshot_desktop.png / screenshot_mobile.png.",
    )
    add(
        "E",
        "site_visible_text",
        "INFO",
        "Visible text of the landing page (first 6000 chars).",
        res.get("text", ""),
    )
    add(
        "E",
        "site_controls",
        "INFO",
        f"{len(res.get('buttons', []))} clickable controls found.",
        " | ".join(b for b in res.get("buttons", []) if b.strip()),
    )
    inter = res.get("interaction") or {}
    add(
        "E",
        "site_human_interaction",
        "PASS" if inter.get("clicked") else "INFO",
        f"Active human interaction probe clicked '{inter.get('clicked')}', "
        f"DOM state_changed={inter.get('state_changed')}; saved screenshot_interaction.png.",
        inter.get("after_excerpt", ""),
    )
    add(
        "E",
        "site_console_errors",
        "FAIL" if res["console_errors"] else "PASS",
        f"{len(res['console_errors'])} console errors on load/interaction.",
        "\n".join(res["console_errors"][:20]),
    )
    reqs = res.get("requests", [])
    data_reqs = [
        r
        for r in reqs
        if re.search(r"\.(json|geojson|tif|tiff|png|jpg|jpeg|webp|bin|pbf|glb|csv)(\?|$)", r, re.I)
    ]
    add(
        "E",
        "site_data_requests",
        "INFO",
        f"{len(reqs)} network requests completed, {len(data_reqs)} data/imagery files, "
        f"{len(res.get('failed', []))} failed.",
        "\n".join(data_reqs[:60])
        + ("\nFAILED:\n" + "\n".join(res["failed"][:20]) if res.get("failed") else ""),
    )


def repo() -> None:
    url = SUB.get("repo_url")
    if not url:
        return
    branch = SUB.get("repo_branch") or "main"
    dst = WORK / "repo"
    code, out = sh(
        f"GIT_TERMINAL_PROMPT=0 git clone --depth 1 --branch '{branch}' '{url}' {dst}", 180
    )
    if code != 0:
        add(
            "E",
            "repo_clone",
            "FAIL",
            f"Anonymous clone of branch '{branch}' failed (exit {code}).",
            out[-600:],
        )
        return
    files = [p for p in dst.rglob("*") if p.is_file() and ".git" not in p.parts]
    exts: dict[str, int] = {}
    for p in files:
        exts[p.suffix.lower() or "(none)"] = exts.get(p.suffix.lower() or "(none)", 0) + 1
    top = sorted(exts.items(), key=lambda x: -x[1])[:12]
    add(
        "E",
        "repo_clone",
        "PASS",
        f"Cloned branch '{branch}' anonymously: {len(files)} files; top extensions {top}.",
    )
    readme = next((p for p in dst.iterdir() if p.name.lower().startswith("readme")), None)
    add(
        "E",
        "repo_readme",
        "PASS" if readme else "FAIL",
        f"README present ({readme.stat().st_size} bytes)." if readme else "No README at repo root.",
        readme.read_text(encoding="utf-8", errors="replace")[:4000] if readme else "",
    )
    lic = any(p.name.upper().startswith(("LICENSE", "LICENCE")) for p in dst.iterdir())
    add(
        "E",
        "repo_license",
        "PASS" if lic else "FAIL",
        "LICENSE file present." if lic else "No LICENSE file.",
    )

    terms = {
        "HiRISE": r"hirise",
        "MOLA": r"\bmola\b",
        "CTX": r"\bctx\b",
        "CRISM": r"crism",
        "THEMIS": r"themis",
        "Mars Trek": r"mars ?trek|trek\.nasa",
        "PDS": r"\bpds\b|pds-geosciences|pds\.nasa",
        "MEDA (Perseverance weather)": r"\bmeda\b",
        "RAD (radiation)": r"\brad\b.*(curiosity|msl)|radiation assessment",
        "Mars 2020/Perseverance": r"perseverance|mars ?2020|m2020",
        "Curiosity/MSL": r"curiosity|\bmsl\b",
        "USGS geologic map": r"usgs",
        "Jezero": r"jezero",
        "Gale/Mount Sharp": r"gale|mount sharp|aeolis",
    }
    code_files = [
        p
        for p in files
        if p.suffix.lower()
        in (".py", ".ts", ".tsx", ".js", ".json", ".md", ".yaml", ".yml", ".toml")
        and p.stat().st_size < 2_000_000
    ]
    counts = {}
    for name, rx in terms.items():
        r = re.compile(rx, re.I)
        counts[name] = sum(
            1 for p in code_files if r.search(p.read_text(encoding="utf-8", errors="ignore"))
        )
    add(
        "E",
        "repo_nasa_data_refs",
        "INFO",
        f"Files mentioning each NASA dataset/mission: {counts}",
        tier="SME",
    )
    data_files = [
        str(p.relative_to(dst))
        for p in files
        if p.suffix.lower()
        in (".tif", ".tiff", ".img", ".geojson", ".bin", ".npy", ".png", ".jpg", ".json")
        and ("data" in str(p).lower() or "pack" in str(p).lower())
    ]
    add(
        "E",
        "repo_data_files",
        "INFO",
        f"{len(data_files)} data/imagery files under data/pack folders.",
        "\n".join(data_files[:80]),
        tier="SME",
    )

    if (dst / "pyproject.toml").exists() or (dst / "requirements.txt").exists():
        inst = (
            "pip install -q -e '.[dev]' || pip install -q -e . "
            if (dst / "pyproject.toml").exists()
            else "pip install -q -r requirements.txt"
        )
        c1, o1 = sh(
            f"python3 -m venv /judge/work/venv && . /judge/work/venv/bin/activate && ({inst}) && pip install -q pytest",
            900,
            dst,
        )
        if c1 != 0:
            add(
                "E",
                "repo_python_install",
                "FAIL",
                f"Python install failed (exit {c1}).",
                o1[-1500:],
            )
        else:
            c2, o2 = sh(
                ". /judge/work/venv/bin/activate && python -m pytest -q --tb=short -p no:cacheprovider",
                900,
                dst,
            )
            summary = [
                ln for ln in o2.strip().splitlines() if re.search(r"passed|failed|error", ln)
            ][-1:] or [o2[-200:]]
            add(
                "E",
                "repo_pytest",
                "PASS" if c2 == 0 else "FAIL",
                f"pytest -q --tb=short exit {c2}: {summary[0].strip()}",
                o2[-2500:],
            )
    fe = next(
        (p.parent for p in [dst / "package.json", dst / "frontend" / "package.json"] if p.exists()),
        None,
    )
    if fe:
        c3, o3 = sh(
            "npm ci --no-audit --no-fund >/tmp/npmci.log 2>&1 || npm install --no-audit --no-fund >>/tmp/npmci.log 2>&1; "
            "npm run build 2>&1 | tail -40",
            900,
            fe,
        )
        ok = c3 == 0 and not re.search(r"\berror\b", o3, re.I)
        add(
            "E",
            "repo_frontend_build",
            "PASS" if ok else "FAIL",
            f"Frontend `npm run build` in {fe.relative_to(dst) or '.'} exit {c3}.",
            o3[-2500:],
        )


def citations() -> None:
    raw_urls = sorted(set(re.findall(r"https?://[^\s)>\]\"'`]+", SUB_TEXT)))
    urls = [
        u.rstrip(".,;:")
        for u in raw_urls
        if not re.search(
            r"^https?://(localhost|127\.0\.0\.1|img\.shields\.io|www\.spaceappschallenge\.org)\b",
            u,
            re.I,
        )
    ][:40]
    if not urls:
        add("E", "citations_live", "FAIL", "No external URLs cited in submission text.")
        return
    rows, dead = [], 0
    ok_codes = ("200", "206", "301", "302", "303", "307", "308", "403", "429")
    for u in urls:
        _, out = sh(
            f"curl -s -I -A 'Mozilla/5.0 SpaceAppsJudge/2.0' -o /dev/null -L -m 15 -w '%{{http_code}}' '{u}'",
            20,
        )
        code = out.strip()[-3:]
        if code not in ok_codes:
            _, out2 = sh(
                f"curl -s -r 0-511 -A 'Mozilla/5.0 SpaceAppsJudge/2.0' -o /dev/null -L -m 15 -w '%{{http_code}}' '{u}'",
                20,
            )
            code = out2.strip()[-3:]
        dead += code not in ok_codes
        rows.append(f"{code} {u}")
    add(
        "E",
        "citations_live",
        "PASS" if dead == 0 else "FAIL",
        f"{len(urls)} cited external URLs checked, {dead} unreachable.",
        "\n".join(rows),
    )


if __name__ == "__main__":
    gate()
    for fn in (site, repo, citations):
        try:
            fn()
        except Exception as e:
            add(
                "E",
                f"{fn.__name__}_crash",
                "FAIL",
                f"Probe {fn.__name__} crashed: {type(e).__name__}: {e}",
            )
    (OUT / "evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    gate_fail = [e["id"] for e in evidence if e["id"].startswith("G") and e["status"] == "FAIL"]
    print(f"PROBES DONE: {len(evidence)} facts, gate failures: {gate_fail}")
