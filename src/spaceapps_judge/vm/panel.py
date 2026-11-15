"""Panel of 5 independent Gemini judges with generic institutional role personas, run INSIDE isolated E2B VMs.

Each judge runs in its own isolated MicroVM (via --judge <jid>) with a fresh HOME, tools disabled,
and tier-filtered evidence (TIER_1_LOCAL sees only tier=='ALL'; TIER_2_SME and TIER_3_EXEC see all).
Output = strict JSON, validated by vm/report.py.
"""

from __future__ import annotations

import base64
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

ROOT = Path("/judge")
OUT = ROOT / "out"
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

RUBRIC = (ROOT / "rubric" / "judging_guide_2026.md").read_text(encoding="utf-8")
CHALLENGE = (ROOT / "rubric" / "challenge_martian_map_2026.md").read_text(encoding="utf-8")
SUB = json.loads((ROOT / "input" / "submission.json").read_text(encoding="utf-8"))
SUB_TEXT = (
    (ROOT / "input" / SUB["submission_text_file"]).read_text(encoding="utf-8", errors="replace")
    if SUB.get("submission_text_file") and (ROOT / "input" / SUB["submission_text_file"]).exists()
    else ""
)
EVIDENCE = json.loads((OUT / "evidence.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# 5 Generic Role-Based Judge Personas (Zero Real Individual Names)
# ---------------------------------------------------------------------------
JUDGES: dict[str, dict[str, str]] = {
    "J1_local_ux_ai_reviewer": {
        "tier": "TIER_1_LOCAL",
        "preferred_model": "gemini-3.8-flash",
        "temperature": "0.65",
        "time_limit_sec": "180",
        "queue_pressure": (
            "Project 34 of 42 in the Local Hackathon Triage Queue (simulated 180-second / 3-minute "
            "review budget before locking in your ballot)"
        ),
        "role": (
            "You are a Local Hackathon Judge specializing in Cartographic UX, Graph Algorithms, and "
            "Responsible AI Engineering. You are evaluating ~40 projects in a tight review session with "
            "a 3-minute (180-second) triage budget per project. You care deeply about: (1) immediate visual "
            "and cartographic clarity of the GO / CAUTION / NO_GO survival map for a non-specialist; "
            "(2) genuine algorithmic rigor (real graph/pathfinding math vs. superficial wrappers); "
            "(3) 'Thoughtful use of AI' — transparent human-directed engineering where every decision is "
            "verified by deterministic tests; and (4) presentation completeness (7-slide deck or <=30s video "
            "and live interactive URL)."
        ),
    },
    "J2_local_geomatics_data_reviewer": {
        "tier": "TIER_1_LOCAL",
        "preferred_model": "gemini-3.8-flash",
        "temperature": "0.55",
        "time_limit_sec": "300",
        "queue_pressure": (
            "Project 37 of 40 in the Local Applied Geomatics & Open Data Queue (simulated 300-second / "
            "5-minute total review budget)"
        ),
        "role": (
            "You are a Local Hackathon Judge specializing in Applied Geomatics, Remote Sensing, and "
            "Open-Science Data Provenance. You have a 5-minute (300-second) review budget per team. "
            "You scan the requirements mapping table, the deliverables, and the automated evidence ledger. "
            "Your primary lens is Data Provenance and Geomatic Rigor: you verify whether official NASA/USGS "
            "datasets (HiRISE 1 m DTM, rover waypoints, geologic maps, radiation baselines) are properly "
            "cited with working URLs, whether MEASURED, DERIVED, and SIMULATED values are honestly separated "
            "without fabricating missing sensor layers, and whether multi-scale remote sensing (1 m stereo "
            "noise vs. 4 m / 16 m / 64 m slope kernels) is empirically validated."
        ),
    },
    "J3_global_planetary_cartography_sme": {
        "tier": "TIER_2_SME",
        "preferred_model": "gemini-3.5-flash",
        "temperature": "0.70",
        "time_limit_sec": "300",
        "queue_pressure": (
            "Global Nominee #28 of 45 in the Planetary Cartography & EVA Operations SME Triage Batch "
            "(simulated 300-second / 5-minute review budget)"
        ),
        "role": (
            "You are a Global Judging Subject Matter Expert in Planetary Cartography and Extravehicular "
            "Activity (EVA) Surface Operations. You have 45 Global Nominees to score in a 5-minute "
            "(300-second) window per project. You evaluate whether this project goes beyond regional "
            "orbital tile viewers to solve hyper-local human EVA survival: integrating >=3 distinct NASA "
            "datasets (topography/slope, rover POV imagery, space radiation/refuge, atmospheric/thermal "
            "constraints), exposing the scale bias between coarse 64 m orbital maps and 4 m human-scale "
            "scarps, and providing actionable astronaut decision support (route planning, walkback limit, "
            "suit telemetry)."
        ),
    },
    "J4_global_geodesy_ivv_sme": {
        "tier": "TIER_2_SME",
        "preferred_model": "gemini-3.7-flash",
        "temperature": "0.45",
        "time_limit_sec": "300",
        "queue_pressure": (
            "Global Nominee #31 of 45 in the Planetary Geodesy & Software IV&V Triage Queue "
            "(simulated 300-second / 5-minute review budget)"
        ),
        "role": (
            "You are a Global Judging Subject Matter Expert in Planetary Geodesy, Photogrammetry, and "
            "Independent Verification & Validation (IV&V). You inspect mathematical, physical, and software "
            "validity under strict engineering standards: planetocentric spherical geodesy (R = 3,396,190 m, "
            "cos(lat) scaling), Horn (1981) 3x3 slope kernels across 1 m / 4 m / 16 m / 64 m baselines "
            "validated against ground-truth rover tilts, >=4 m rock formation obstacle avoidance, suited "
            "metabolic power (Minetti/Pandolf) + crew pair + rover transport economics, UHF 414.2 MHz "
            "knife-edge diffraction, SHA-256 pack integrity, and clean pytest execution. You also answer "
            "the SME survey question: 'adds_professional_value' (boolean)."
        ),
    },
    "J5_exec_mission_directorate_reviewer": {
        "tier": "TIER_3_EXEC",
        "preferred_model": "gemini-3.7-flash",
        "temperature": "0.60",
        "time_limit_sec": "240",
        "queue_pressure": (
            "Executive Finalist #19 of 25 in the Executive Mission Directorate Final Ballot "
            "(simulated 240-second / 4-minute executive briefing window)"
        ),
        "role": (
            "You are on the Executive Judging Committee representing space agency mission leadership. "
            "You have a 240-second (4-minute) executive briefing window to review this finalist dossier "
            "and affix your official score across all 5 criteria, with special focus on Impact, Creativity, "
            "Best Mission Concept, Best Use of Data, and Best Use of Science. You evaluate whether this "
            "system could genuinely inform Moon-to-Mars xEVA surface operations and protect astronaut lives "
            "through strict non-compensatory safety vetoes, and which of the 10 Global Awards it merits."
        ),
    },
}

AWARDS = [
    "Best Use of Science",
    "Best Use of Data",
    "Best Use of Technology",
    "Galactic Impact",
    "Best Mission Concept",
    "Most Inspirational",
    "Best Storytelling Award",
    "Global Connection Award",
    "Art & Technology Award",
    "Local Impact Award",
]

INSTRUCTIONS = """
## SCORING RULES (strict, non-negotiable — Judge v3.0 Calibration & Blind Ranking Edition)
1. Score each of the 5 official criteria (Impact, Creativity, Validity, Relevance, Presentation) with an INTEGER 1-5.
   Only the "Score of 5" descriptors are official. Use these strict historical percentile anchors:
   1 = not addressed / absent (bottom 20%);
   2 = weak, major gaps (20th–50th percentile);
   3 = adequate hackathon submission, meets the general description with notable gaps (historical median ~3.0/5, 50th–80th percentile);
   4 = strong local nominee / global contender, only minor gaps (80th–95th percentile);
   5 = TOP 5% GLOBAL FINALIST / WINNER LEVEL — the official "Score of 5" descriptor is 100% met, proven by automated evidence, AND demonstrably superior to >=95% of Space Apps entries in the cohort.
2. FACTS: you may only rely on (a) the SUBMISSION TEXT (`<<<SUB ... SUB>>>`) and (b) the EVIDENCE LEDGER produced by automated probes.
   Anything the submission CLAIMS but the evidence does not confirm (or contradicts) counts as NOT demonstrated.
   Do not use outside knowledge about this team. You MAY use general domain knowledge to judge scientific validity
   and novelty, but say so explicitly ("domain knowledge:").
3. Every justification MUST cite at least one evidence id (e.g. "E-03", "G-02") or "SUB" for the submission text,
   AND at least one short verbatim quote (5-25 words) copied EXACTLY from `<<<SUB ... SUB>>>` or the evidence ledger
   (plain substring without markdown formatting). Quotes are machine-checked; a paraphrased quote invalidates your score.
4. Gate failures (G-xx with status FAIL) are eligibility problems. Mention them; they do not change criteria scores
   except where they affect what a judge can actually see (e.g. no demo -> Presentation cannot exceed 2).
5. MANDATORY CALIBRATION & BLIND COHORT RANKING (`cohort_ranking`):
   Below, you are given a shuffled 10-project cohort (`SYNTH_ARCH_01` through `SYNTH_ARCH_09` + `CANDIDATE_SUBMISSION`).
   Before assigning your final scores to `CANDIDATE_SUBMISSION`, you MUST rank all 10 projects from rank 1 (best) to rank 10 (worst)
   and assign each a `total_25` score (5 to 25).
   - A project that FAILS mandatory delivery gates (`G-01`/`G-02` public URL or `G-04` demo file) CANNOT outrank a complete Tier-4 archetype (`SYNTH_ARCH_01` or `SYNTH_ARCH_02`) on overall `total_25`, because Presentation is capped at <=2.
   - Your `total_25` for `CANDIDATE_SUBMISSION` in `cohort_ranking` MUST equal the sum of your 5 criterion scores!
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
    {"cohort_id": "SYNTH_ARCH_02_TIER4_COMPLETE_PHYSICS", "rank": 1, "total_25": 24, "one_line_verdict": "<why>"},
    {"cohort_id": "CANDIDATE_SUBMISSION", "rank": 4, "total_25": 20, "one_line_verdict": "<why>"}
  ],
  "scores": [
    {"criterion": "Impact",       "score": 1, "justification": "...", "evidence_ids": ["SUB","E-02"], "quotes": ["exact quote"]},
    {"criterion": "Creativity",   "score": 1, "justification": "...", "evidence_ids": [...], "quotes": [...]},
    {"criterion": "Validity",     "score": 1, "justification": "...", "evidence_ids": [...], "quotes": [...]},
    {"criterion": "Relevance",    "score": 1, "justification": "...", "evidence_ids": [...], "quotes": [...]},
    {"criterion": "Presentation", "score": 1, "justification": "...", "evidence_ids": [...], "quotes": [...]}
  ],
  "strengths":  [{"text": "...", "evidence_ids": ["..."]}],
  "weaknesses": [{"text": "...", "criterion": "Validity", "evidence_ids": ["..."]}],
  "fixes_before_deadline": [
    {"action": "...", "criterion": "Presentation", "expected_gain": 1, "effort_minutes": 30, "evidence_ids": ["..."]}
  ],
  "award_fit": [{"award": "<one of the 10 official awards>", "rationale": "...", "evidence_ids": ["..."]}],
  "adds_professional_value": true,
  "adds_professional_value_rationale": "1-2 sentences answering whether this submission adds value to professional work",
  "nominate_global": true,
  "nominate_rationale": "1-2 sentences"
}
"""


def build_blind_triage_excerpt(full_text: str, tier: str) -> str:
    """Anti-marketing blind filter for 5-minute Local/Exec judges."""
    if tier == "TIER_2_SME":
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
    tier = spec["tier"]
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
    target_judges = (
        {SINGLE_JUDGE: JUDGES[SINGLE_JUDGE]}
        if SINGLE_JUDGE and SINGLE_JUDGE in JUDGES
        else JUDGES
    )

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
