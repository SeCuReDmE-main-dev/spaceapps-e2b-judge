"""Panel of N independent Gemini judges (default: 5 generic institutional role personas), run INSIDE isolated E2B VMs.

Each judge runs in its own isolated MicroVM (via --judge <jid>) with a fresh HOME, tools disabled,
and tier-filtered evidence (TIER_1_LOCAL sees only tier=='ALL'; TIER_2_SME and TIER_3_EXEC see all).
Judges come from /judge/input/judges.json and criteria/awards from /judge/input/hackathon_settings.json
when present (NASA Space Apps 2026 v3.0 defaults otherwise).
Output = strict JSON, validated by vm/report.py.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibration_cohort import CALIBRATION_COHORT  # noqa: E402
from hackathon_config import (  # noqa: E402
    DEFAULT_AWARDS,
    DEFAULT_JUDGES,
    criterion_names,
    default_settings,
    max_total,
    normalize_tier,
    resolve_judges,
    resolve_settings,
)

ROOT = Path("/judge")
OUT = ROOT / "out"
INP = ROOT / "input"
MODEL = (
    sys.argv[1]
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--")
    else "gemini-3.8-flash"
)
FALLBACK = (
    sys.argv[2]
    if len(sys.argv) > 2 and sys.argv[2] and not sys.argv[2].startswith("--")
    else "gemini-3.5-flash"
)

SINGLE_JUDGE: str | None = None
for idx, arg in enumerate(sys.argv):
    if arg == "--judge" and idx + 1 < len(sys.argv):
        SINGLE_JUDGE = sys.argv[idx + 1]

# Runtime inputs are loaded by load_runtime() (called from main) so the module stays importable for tests.
RUBRIC = ""
CHALLENGE = ""
SUB: dict = {}
SUB_TEXT = ""
EVIDENCE: list[dict] = []
SETTINGS: dict = default_settings()

# ---------------------------------------------------------------------------
# Judges (default: 5 generic role-based personas, zero real individual names) & official awards
# ---------------------------------------------------------------------------
JUDGES: dict[str, dict[str, str]] = copy.deepcopy(DEFAULT_JUDGES)
CRITERIA: list[str] = criterion_names(SETTINGS)
AWARDS: list[str] = list(DEFAULT_AWARDS)

INSTRUCTIONS_TEMPLATE = """
## SCORING RULES (strict, non-negotiable — Judge v3.0 Calibration & Blind Ranking Edition)
1. Score each of the @@K@@ official criteria (@@CRITERIA_CSV@@) with an INTEGER 1-5.
   Only the "Score of 5" descriptors are official. Use these strict historical percentile anchors:
   1 = not addressed / absent (bottom 20%);
   2 = weak, major gaps (20th–50th percentile);
   3 = adequate hackathon submission, meets the general description with notable gaps (historical median ~3.0/5, 50th–80th percentile);
   4 = strong local nominee / global contender, only minor gaps (80th–95th percentile);
   5 = TOP 5% GLOBAL FINALIST / WINNER LEVEL — the official "Score of 5" descriptor is 100% met, proven by automated evidence, AND demonstrably superior to >=95% of @@HACKATHON@@ entries in the cohort.
2. FACTS: you may only rely on (a) the SUBMISSION TEXT (`<<<SUB ... SUB>>>`) and (b) the EVIDENCE LEDGER produced by automated probes.
   Anything the submission CLAIMS but the evidence does not confirm (or contradicts) counts as NOT demonstrated.
   Do not use outside knowledge about this team. You MAY use general domain knowledge to judge scientific validity
   and novelty, but say so explicitly ("domain knowledge:").
3. Every justification MUST cite at least one evidence id (e.g. "E-03", "G-02") or "SUB" for the submission text,
   AND at least one short verbatim quote (5-25 words) copied EXACTLY from `<<<SUB ... SUB>>>` or the evidence ledger
   (plain substring without markdown formatting). Quotes are machine-checked; a paraphrased quote invalidates your score.
4. Gate failures (G-xx with status FAIL) are eligibility problems. Mention them; they do not change criteria scores
   except where they affect what a judge can actually see (e.g. no demo -> @@PRESENTATION_CAP@@ cannot exceed 2).
5. MANDATORY CALIBRATION & BLIND COHORT RANKING (`cohort_ranking`):
   Below, you are given a shuffled 10-project cohort (`SYNTH_ARCH_01` through `SYNTH_ARCH_09` + `CANDIDATE_SUBMISSION`).
   Before assigning your final scores to `CANDIDATE_SUBMISSION`, you MUST rank all 10 projects from rank 1 (best) to rank 10 (worst)
   and assign each a `@@TOTAL_KEY@@` score (@@K@@ to @@MAX@@).
   - A project that FAILS mandatory delivery gates (`G-01`/`G-02` public URL or `G-04` demo file) CANNOT outrank a complete Tier-4 archetype (`SYNTH_ARCH_01` or `SYNTH_ARCH_02`) on overall `@@TOTAL_KEY@@`, because @@PRESENTATION_CAP@@ is capped at <=2.
   - Your `@@TOTAL_KEY@@` for `CANDIDATE_SUBMISSION` in `cohort_ranking` MUST equal the sum of your @@K@@ criterion scores!
   - When justifying any `5/5` score on `CANDIDATE_SUBMISSION`, explicitly contrast it against at least one benchmark (`SYNTH_ARCH_03`, `SYNTH_ARCH_04`, etc.) to prove why it is superior.
6. MANDATORY CRITICAL RIGOR: You MUST identify at least 3 concrete `weaknesses` (even on strong submissions, e.g. missing gates, single-site spatial scope, unmeasured sensor layers, UI/demo gaps).
7. MANDATORY PERSONAL JUDGE DEBRIEF (`judge_debrief`):
   Give your candid first-person perspective as a judge:
   - `what_i_judged_and_how`: What you inspected during your 3-to-5 minute triage window and how you tested it against your domain lens.
   - `why_this_score`: Candid explanation of why the project received this exact score and cohort rank (why it beat some benchmarks and lost to others).
   - `what_would_change_my_verdict`: Concrete, high-leverage improvements that would make you raise your score and rank this project #1.
   - `positive_highlights`: What genuinely impressed you most and stood out above typical hackathon projects.
   - `must_keep_sacred`: List of 2-3 specific elements/features that are already rock-solid and MUST NOT be broken or removed during final edits.
8. Return ONLY a single JSON object matching this exact schema (no prose outside JSON, no markdown fences):
{
  "judge": "<your judge id>",
  "tier": "<TIER_1_LOCAL | TIER_2_SME | TIER_3_EXEC>",
  "time_pressure_audit": {
    "time_limit_sec": 300,
    "simulated_review_sec": 240,
    "thirty_second_impression": "<1-sentence raw gut reaction after the first 30 seconds of scanning>",
    "ballot_locked_under_time_limit": true
  },
  "judge_debrief": {
    "what_i_judged_and_how": "<2-3 sentences: what you looked at and how you evaluated it>",
    "why_this_score": "<2-3 sentences: why you gave this exact score and rank>",
    "what_would_change_my_verdict": "<2-3 sentences: what specific additions/fixes would flip your vote or raise the score>",
    "positive_highlights": "<1-2 sentences: the best aspect of this submission>",
    "must_keep_sacred": ["<item 1 to never break/remove>", "<item 2 to never break/remove>"]
  },
  "cohort_ranking": [
    {"cohort_id": "SYNTH_ARCH_02_TIER4_COMPLETE_PHYSICS", "rank": 1, "@@TOTAL_KEY@@": @@EX_TOP@@, "one_line_verdict": "<why>"},
    {"cohort_id": "CANDIDATE_SUBMISSION", "rank": 4, "@@TOTAL_KEY@@": @@EX_CAND@@, "one_line_verdict": "<why>"}
  ],
  "scores": [
@@SCORES_SCHEMA@@
  ],
  "strengths":  [{"text": "...", "evidence_ids": ["..."]}],
  "weaknesses": [{"text": "...", "criterion": @@WEAKNESS_CRIT@@, "evidence_ids": ["..."]}],
  "fixes_before_deadline": [
    {"action": "...", "criterion": @@FIX_CRIT@@, "expected_gain": 1, "effort_minutes": 30, "evidence_ids": ["..."]}
  ],
  "award_fit": [{"award": "@@AWARD_HINT@@", "rationale": "...", "evidence_ids": ["..."]}],
  "adds_professional_value": true,
  "adds_professional_value_rationale": "1-2 sentences answering whether this submission adds value to professional work",
  "nominate_global": true,
  "nominate_rationale": "1-2 sentences"
}
"""


def build_instructions(criteria: list[str], awards: list[str], hackathon_label: str = "Space Apps") -> str:
    """Render the scoring rules + JSON schema for K criteria (max total = 5*K) and the official awards list.

    With the 5 NASA criteria, the 10 NASA awards and the "Space Apps" label this returns the exact v3.0 text.
    """
    if not criteria:
        raise ValueError("at least 1 criterion is required")
    k = len(criteria)
    mx = max_total(criteria)
    width = max(len(json.dumps(c)) for c in criteria) + 2
    rows = []
    for i, c in enumerate(criteria):
        ids_quotes = '["SUB","E-02"], "quotes": ["exact quote"]' if i == 0 else '[...], "quotes": [...]'
        sep = "," if i < k - 1 else ""
        rows.append(
            f'    {{"criterion": {(json.dumps(c) + ",").ljust(width)}"score": 1, "justification": "...", '
            f'"evidence_ids": {ids_quotes}}}{sep}'
        )
    if len(awards) == 1:
        award_hint = "<the 1 official award, only if it genuinely fits>"
    elif awards:
        award_hint = f"<one of the {len(awards)} official awards>"
    else:
        award_hint = "<free-form award or prize category this project fits (no official award list)>"
    presentation = "Presentation" if "Presentation" in criteria else "any presentation/demo-related criterion"
    replacements = {
        "@@K@@": str(k),
        "@@CRITERIA_CSV@@": ", ".join(criteria),
        "@@HACKATHON@@": hackathon_label,
        "@@PRESENTATION_CAP@@": presentation,
        "@@TOTAL_KEY@@": f"total_{mx}",
        "@@MAX@@": str(mx),
        "@@EX_TOP@@": str(round(24 * mx / 25)),
        "@@EX_CAND@@": str(round(20 * mx / 25)),
        "@@SCORES_SCHEMA@@": "\n".join(rows),
        "@@WEAKNESS_CRIT@@": json.dumps(criteria[2] if k > 2 else criteria[-1]),
        "@@FIX_CRIT@@": json.dumps(criteria[-1]),
        "@@AWARD_HINT@@": award_hint,
    }
    text = INSTRUCTIONS_TEMPLATE
    for token, value in replacements.items():
        text = text.replace(token, value)
    return text


INSTRUCTIONS = build_instructions(CRITERIA, AWARDS)


def load_runtime() -> None:
    """Load rubric, submission, evidence, hackathon settings and judges from /judge (inside the VM)."""
    global RUBRIC, CHALLENGE, SUB, SUB_TEXT, EVIDENCE, SETTINGS, JUDGES, CRITERIA, AWARDS, INSTRUCTIONS
    RUBRIC = (ROOT / "rubric" / "judging_guide_2026.md").read_text(encoding="utf-8")
    CHALLENGE = (ROOT / "rubric" / "challenge_martian_map_2026.md").read_text(encoding="utf-8")
    SUB = json.loads((INP / "submission.json").read_text(encoding="utf-8"))
    SUB_TEXT = (
        (INP / SUB["submission_text_file"]).read_text(encoding="utf-8", errors="replace")
        if SUB.get("submission_text_file") and (INP / SUB["submission_text_file"]).exists()
        else ""
    )
    EVIDENCE = json.loads((OUT / "evidence.json").read_text(encoding="utf-8"))
    SETTINGS = resolve_settings(INP)
    JUDGES = resolve_judges(INP, SETTINGS["hackathon_name"])
    CRITERIA = criterion_names(SETTINGS)
    AWARDS = list(SETTINGS["awards"])
    INSTRUCTIONS = build_instructions(
        CRITERIA, AWARDS, "Space Apps" if SETTINGS["is_default"] else SETTINGS["hackathon_name"]
    )


def build_criteria_section() -> str:
    """Custom hackathons only: the K criteria definitions from hackathon_settings.json."""
    if SETTINGS.get("is_default", True):
        return ""
    rows = [
        f"- **{c['name']}**" + (f": {c['description']}" if c.get("description") else "")
        for c in SETTINGS["criteria"]
    ]
    return (
        f"# HACKATHON SCORING CRITERIA ({SETTINGS['hackathon_name']} — {len(rows)} criteria, "
        f"each 1-5, total /{max_total(SETTINGS)})\n" + "\n".join(rows) + "\n"
    )


def build_blind_triage_excerpt(full_text: str, tier: str) -> str:
    """Anti-marketing blind filter for 5-minute Local/Exec judges (unknown tiers are treated as SME: never truncated)."""
    if normalize_tier(tier) == "TIER_2_SME":
        return full_text[:28000]
    lines = full_text.splitlines()
    kept: list[str] = []
    word_count = 0
    for ln in lines:
        w = len(ln.split())
        if word_count + w <= 350 or ln.strip().startswith(("|", "#", "- **", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")):
            kept.append(ln)
            word_count += w
        if len("\n".join(kept)) > 7500:
            break
    return "\n".join(kept)


def build_cohort_section(jid: str) -> str:
    """Deterministically shuffle the 9 synthetic archetypes + CANDIDATE_SUBMISSION per judge."""
    rng = random.Random(hashlib.sha256(jid.encode("utf-8")).hexdigest())
    items = list(CALIBRATION_COHORT) + [
        {
            "cohort_id": "CANDIDATE_SUBMISSION",
            "title": f"{SUB.get('project_title', 'Candidate Project')} (The submission under evaluation below)",
            "summary_300w": "Evaluate using the <<<SUB ... SUB>>> text and EVIDENCE LEDGER below.",
            "gates_status": "See G-01..G-09 in EVIDENCE LEDGER below.",
        }
    ]
    rng.shuffle(items)
    out = [
        "# 10-PROJECT CALIBRATION COHORT (Rank ALL 10 from 1 to 10 in `cohort_ranking`)",
        "Use these 9 synthetic reference archetypes across 4 quality tiers to anchor your scoring scale:",
    ]
    for idx, it in enumerate(items, 1):
        out.append(
            f"### Cohort Entry #{idx}: `{it['cohort_id']}` — {it['title']}\n"
            f"- **Gates / Probes**: {it['gates_status']}\n"
            f"- **Summary**: {it['summary_300w']}"
        )
    return "\n\n".join(out)


def build_prompt(jid: str, spec: dict[str, str]) -> str:
    tier = normalize_tier(spec.get("tier"))
    vis = [
        e
        for e in EVIDENCE
        if tier in ("TIER_2_SME", "TIER_3_EXEC") or e.get("tier") == "ALL"
    ]
    ledger = "\n".join(
        f"- **{e['id']}** [{e['probe']}] status={e['status']} — {e['fact']}"
        + (f"\n  excerpt:\n  ```\n  {e['excerpt'][:1200]}\n  ```" if e.get("excerpt") else "")
        for e in vis
    )
    triage_sub = build_blind_triage_excerpt(SUB_TEXT, tier)
    cohort_block = build_cohort_section(jid)
    return (
        f"# YOUR JUDGE ID: {jid} ({tier})\n"
        f"## ⏱️ SIMULATED TRIAGE BUDGET: {spec['time_limit_sec']} SECONDS\n"
        f"**Queue Context**: {spec['queue_pressure']}.\n"
        f"**Role**: {spec['role']}\n"
        f"{INSTRUCTIONS}\n"
        f"{build_criteria_section()}"
        f"# OFFICIAL JUDGING GUIDE\n{RUBRIC}\n"
        f"# CHALLENGE BRIEF\n{CHALLENGE}\n"
        f"{cohort_block}\n\n"
        f"# CANDIDATE SUBMISSION METADATA\nProject: {SUB.get('project_title')}\nChallenge: {SUB.get('challenge')}\n"
        f"# CANDIDATE SUBMISSION TEXT (cite as 'SUB'; quotes must be exact substrings of this block)\n<<<SUB\n{triage_sub}\nSUB>>>\n"
        f"# AUTOMATED EVIDENCE LEDGER (cite by id; quotes must be exact substrings)\n{ledger}\n"
        f"# OFFICIAL GLOBAL AWARDS LIST\n{json.dumps(AWARDS)}\n"
    )


def extract_json(txt: str) -> dict:
    txt = txt.strip()
    try:
        obj = json.loads(txt)
        if isinstance(obj, dict) and "response" in obj and isinstance(obj["response"], str):
            inner = obj["response"].strip()
            inner = re.sub(r"^```(?:json)?\s*|\s*```$", "", inner, flags=re.DOTALL).strip()
            return json.loads(inner)
        if isinstance(obj, dict) and "scores" in obj:
            return obj
    except Exception:
        pass
    for m in re.finditer(r"\{.*\}", txt, flags=re.DOTALL):
        chunk = m.group(0)
        try:
            d = json.loads(chunk)
            if isinstance(d, dict) and "scores" in d:
                return d
        except Exception:
            continue
    raise ValueError("No valid judge JSON found in output")


def call_rest_api(prompt: str, model: str, temp: float, jhome: Path, attempt: int) -> dict | None:
    """Call Gemini generateContent REST API directly inside the MicroVM."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    parts: list[dict] = [{"text": prompt}]
    for name in ("screenshot_desktop.png", "screenshot_mobile.png"):
        src = OUT / name
        if src.exists():
            b64 = base64.b64encode(src.read_bytes()).decode("ascii")
            parts.append({"inline_data": {"mime_type": "image/png", "data": b64}})
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": temp,
            "responseMimeType": "application/json",
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            raw_body = resp.read().decode("utf-8", errors="replace")
            (jhome / f"rest_attempt{attempt}.json").write_text(raw_body, encoding="utf-8")
            body = json.loads(raw_body)
            cand_text = body["candidates"][0]["content"]["parts"][0]["text"]
            data = extract_json(cand_text)
            data["_model"] = model
            data["_temperature"] = temp
            data["_stats"] = body.get("usageMetadata", {})
            return data
    except urllib.error.HTTPError as e:
        err_txt = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        (jhome / f"rest_attempt{attempt}_err.txt").write_text(f"HTTP {e.code}: {err_txt}", encoding="utf-8")
        if e.code == 404:
            print(f"  {jhome.name} REST {model} HTTP 404 (not found); skipping retries", flush=True)
            raise FileNotFoundError(f"Model {model} 404")
        if e.code == 429:
            wait = 20 * (attempt + 1)
            print(f"  {jhome.name} REST {model} attempt {attempt} HTTP 429; retry in {wait}s", flush=True)
            time.sleep(wait)
        else:
            print(f"  {jhome.name} REST {model} attempt {attempt} HTTP {e.code}; retry in 8s", flush=True)
            time.sleep(8)
    except Exception as e:
        (jhome / f"rest_attempt{attempt}_err.txt").write_text(f"{type(e).__name__}: {e}", encoding="utf-8")
        print(f"  {jhome.name} REST {model} attempt {attempt} error ({type(e).__name__}); retry in 8s", flush=True)
        time.sleep(8)
    return None


def call_judge(jid: str, spec: dict[str, str], model: str) -> dict:
    jhome = ROOT / "panel" / jid
    gdir = jhome / ".gemini"
    gdir.mkdir(parents=True, exist_ok=True)
    temp = float(spec.get("temperature", "0.5"))
    for name in ("screenshot_desktop.png", "screenshot_interaction.png", "screenshot_mobile.png"):
        src = OUT / name
        if src.exists():
            (jhome / name).write_bytes(src.read_bytes())

    (gdir / "settings.json").write_text(
        json.dumps(
            {
                "security": {"folderTrust": {"enabled": False}},
                "tools": {"core": [], "allowed": []},
                "model": {"generationConfig": {"temperature": temp}},
            }
        ),
        encoding="utf-8",
    )
    prompt = build_prompt(jid, spec)
    (jhome / "prompt.md").write_text(prompt, encoding="utf-8")
    env = {
        **os.environ,
        "HOME": str(jhome),
        "GEMINI_CLI_HOME": str(jhome),
        "GEMINI_CLI_TRUST_WORKSPACE": "1",
    }

    for attempt in range(2):
        try:
            rest_res = call_rest_api(prompt, model, temp, jhome, attempt)
            if rest_res is not None:
                return rest_res
        except FileNotFoundError:
            break

    cmd = ["gemini", "-p", "Output ONLY the requested JSON object.", "-m", model, "--output-format", "json", "-y"]
    last_err = "unknown"
    for attempt in range(2):
        r = subprocess.run(cmd, input=prompt, text=True, capture_output=True, cwd=jhome, env=env, timeout=360)
        (jhome / f"raw_attempt{attempt}.txt").write_text(
            f"EXIT={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}",
            encoding="utf-8",
        )
        if r.returncode == 0:
            try:
                data = extract_json(r.stdout)
                try:
                    outer = json.loads(r.stdout)
                    data["_stats"] = outer.get("stats", {}).get("models", {})
                except Exception:
                    pass
                data["_model"] = model
                data["_temperature"] = temp
                return data
            except Exception as e:
                last_err = f"JSON parse error: {e}"
        else:
            last_err = f"CLI exit {r.returncode}: {(r.stderr or r.stdout)[-300:]}"
        is_quota = "429" in (r.stderr + r.stdout) or "RESOURCE_EXHAUSTED" in (r.stderr + r.stdout)
        wait = 20 * (attempt + 1) if is_quota else 10
        print(f"  {jid} CLI attempt {attempt} failed; retry in {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError(last_err)


def main() -> int:
    load_runtime()
    print(
        f"[panel] {SETTINGS['hackathon_name']}: {len(JUDGES)} judge(s), {len(CRITERIA)} criteria "
        f"(/{max_total(SETTINGS)}), {len(AWARDS)} official award(s)",
        flush=True,
    )
    if SINGLE_JUDGE and SINGLE_JUDGE not in JUDGES:
        # Never silently fan out to the whole panel inside one VM (N judges x N VMs).
        err = f"unknown judge id {SINGLE_JUDGE!r}; known: {list(JUDGES)}"
        print(f"  {err}", flush=True)
        (OUT / f"panel_{SINGLE_JUDGE}.json").write_text(
            json.dumps({"judge": SINGLE_JUDGE, "_error": err, "scores": [], "strengths": [], "weaknesses": [],
                        "fixes_before_deadline": [], "award_fit": []}, indent=2),
            encoding="utf-8",
        )
        return 2
    target_judges = {SINGLE_JUDGE: JUDGES[SINGLE_JUDGE]} if SINGLE_JUDGE else JUDGES

    results = []
    for idx, (jid, spec) in enumerate(target_judges.items()):
        if idx > 0:
            time.sleep(6)
        preferred = spec.get("preferred_model") or MODEL
        temp_str = spec.get("temperature", "0.5")
        print(f"== {jid} [{spec['tier']}] ({preferred}, temp={temp_str})", flush=True)
        fallback_chain = []
        for cand in (FALLBACK, "gemini-3.8-flash", "gemini-3.5-flash", MODEL):
            if cand and cand != preferred and cand not in fallback_chain:
                fallback_chain.append(cand)
        try:
            res = call_judge(jid, spec, preferred)
        except Exception as e:
            res = None
            last_exc = e
            for fb_model in fallback_chain:
                print(f"  {jid}: {preferred} failed, trying fallback {fb_model} (temp={temp_str})", flush=True)
                try:
                    res = call_judge(jid, spec, fb_model)
                    res["_fallback_from"] = f"{preferred}: {last_exc}"
                    break
                except Exception as e2:
                    last_exc = e2
            if res is None:
                res = {
                    "judge": jid,
                    "tier": spec["tier"],
                    "_error": str(last_exc),
                    "scores": [],
                    "strengths": [],
                    "weaknesses": [],
                    "fixes_before_deadline": [],
                    "award_fit": [],
                }
        res["judge"] = jid
        res["tier"] = spec["tier"]
        results.append(res)
        (OUT / f"panel_{jid}.json").write_text(
            json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(
            f"  {jid}: {'OK' if res.get('scores') else 'FAILED - ' + res.get('_error', '')}",
            flush=True,
        )

    if not SINGLE_JUDGE:
        (OUT / "panel_raw.json").write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
