"""Hackathon settings & judge-panel configuration shared by the host CLI and the E2B VM scripts.

Standard library only: this file is uploaded to `/judge/vm/hackathon_config.py` inside every MicroVM
and imported by `probes.py`, `panel.py` and `report.py`.

Without any configuration file, every resolver returns the exact NASA Space Apps 2026 v3.0 defaults
(5 judges, 5 criteria scored on /25, NASA eligibility gates). With `hackathon_settings.json` and/or
`judges.json`, any hackathon with 1..10 judges and K criteria (scored on /5K) is supported.

Merge rule for `hackathon_settings.json`: every key that is omitted falls back to the NASA default;
an explicit `[]` / `null` is honored (e.g. `"required_keywords": []` disables the keyword gate,
`"awards": []` means "no official award list").
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

SETTINGS_FILENAME = "hackathon_settings.json"
JUDGES_FILENAME = "judges.json"
RULES_FILENAME = "hackathon_rules.md"
CHALLENGE_FILENAME = "challenge_brief.md"

MIN_JUDGES = 1
MAX_JUDGES = 10
VALID_TIERS = ("TIER_1_LOCAL", "TIER_2_SME", "TIER_3_EXEC")
DEFAULT_TIER = "TIER_2_SME"

DEFAULT_HACKATHON_NAME = "NASA Space Apps Challenge 2026"

# ---------------------------------------------------------------------------
# NASA Space Apps 2026 defaults (exact v3.0 behavior)
# ---------------------------------------------------------------------------
DEFAULT_CRITERIA: list[dict[str, str]] = [
    {
        "name": "Impact",
        "description": "Addresses a minor or major problem; reach, inspiration and effectiveness of the proposed solution.",
    },
    {
        "name": "Creativity",
        "description": "Originality and innovation: a novel concept or a meaningful improvement upon existing ideas.",
    },
    {
        "name": "Validity",
        "description": "Grounded in scientific principles; technically, functionally and logically feasible; usable.",
    },
    {
        "name": "Relevance",
        "description": "Fully addresses the challenge and integrates NASA data as a core component, not a superficial add-on.",
    },
    {
        "name": "Presentation",
        "description": "Clear, engaging, well-structured communication of the challenge, solution and significance (demo + project).",
    },
]

DEFAULT_AWARDS: list[str] = [
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

# Exact v3.0 G-06 term list (case-insensitive substring match; "rad " keeps its trailing space on purpose).
DEFAULT_REQUIRED_KEYWORDS: list[str] = [
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
# v3.0 rule for the default list: PASS if one of these strong terms is cited, or >= 2 distinct terms.
NASA_STRONG_KEYWORDS: tuple[str, ...] = ("nasa", "jpl", "pds")
NASA_MIN_KEYWORD_HITS = 2

DEFAULT_GATES: dict[str, Any] = {
    "max_slides": 7,
    "max_video_sec": 30.0,
    "require_demo_file": True,
    "required_language": "en",
    "required_keywords": list(DEFAULT_REQUIRED_KEYWORDS),
    "require_references": True,
    "require_ai_disclosure": True,
}

# 5 generic role-based judge personas (zero real individual names) — exact v3.0 panel.
DEFAULT_JUDGES: dict[str, dict[str, str]] = {
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
DEFAULT_JUDGE_ORDER: list[str] = list(DEFAULT_JUDGES)

# ---------------------------------------------------------------------------
# Tier normalization
# ---------------------------------------------------------------------------
_TIER_ALIASES: dict[str, tuple[str, ...]] = {
    "TIER_1_LOCAL": (
        "LOCAL", "TIER_1", "TIER1", "T1", "1", "LOCAL_JUDGE", "LOCAL_REVIEWER", "TRIAGE",
        "GENERALIST", "COMMUNITY", "MENTOR", "PEER",
    ),
    "TIER_2_SME": (
        "SME", "TIER_2", "TIER2", "T2", "2", "TECHNICAL", "TECH", "EXPERT", "SUBJECT_MATTER_EXPERT",
        "ENGINEER", "SCIENTIST", "RESEARCHER", "DOMAIN_EXPERT", "SPECIALIST",
    ),
    "TIER_3_EXEC": (
        "EXEC", "EXECUTIVE", "VIP", "TIER_3", "TIER3", "T3", "3", "SPONSOR", "LEADERSHIP",
        "DIRECTOR", "CEO", "CTO", "FOUNDER", "INVESTOR", "VC", "PARTNER", "HEAD_JUDGE", "CHAIR",
    ),
}
_ALIAS_TO_TIER: dict[str, str] = {
    alias: tier for tier, aliases in _TIER_ALIASES.items() for alias in aliases
}
# Token-level hints (checked in priority order) for free-form values such as "Sponsor VIP Judge".
_TIER_TOKEN_PRIORITY: tuple[tuple[str, frozenset[str]], ...] = (
    ("TIER_3_EXEC", frozenset({"EXEC", "EXECUTIVE", "VIP", "SPONSOR", "LEADERSHIP", "DIRECTOR", "CEO",
                               "CTO", "FOUNDER", "INVESTOR", "VC", "CHAIR"})),
    ("TIER_2_SME", frozenset({"SME", "TECHNICAL", "TECH", "EXPERT", "ENGINEER", "SCIENTIST",
                              "RESEARCHER", "SPECIALIST"})),
    ("TIER_1_LOCAL", frozenset({"LOCAL", "TRIAGE", "GENERALIST", "COMMUNITY", "MENTOR", "PEER"})),
)


def normalize_tier(value: object) -> str:
    """Map any tier label (canonical, alias such as "SME"/"TECHNICAL"/"LOCAL"/"EXEC"/"VIP", or free text)
    to one of VALID_TIERS. Unknown or missing values become TIER_2_SME so that a judge is never
    silently truncated to the 350-word triage excerpt by mistake."""
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return DEFAULT_TIER
    key = re.sub(r"[^A-Z0-9]+", "_", str(value).strip().upper()).strip("_")
    if not key:
        return DEFAULT_TIER
    if key in VALID_TIERS:
        return key
    if key in _ALIAS_TO_TIER:
        return _ALIAS_TO_TIER[key]
    tokens = set(key.split("_"))
    for tier, hints in _TIER_TOKEN_PRIORITY:
        if tokens & hints:
            return tier
    return DEFAULT_TIER


# ---------------------------------------------------------------------------
# Small coercion helpers (lenient with AI-generated JSON, strict on nonsense)
# ---------------------------------------------------------------------------
def _is_private_key(key: object) -> bool:
    return isinstance(key, str) and key.startswith("_")


def _coerce_bool(value: object, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in ("true", "yes", "1", "on"):
        return True
    if isinstance(value, str) and value.strip().lower() in ("false", "no", "0", "off"):
        return False
    raise ValueError(f"gates.{field} must be true/false, got {value!r}")


def _coerce_positive_number(value: object, field: str, as_int: bool) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"gates.{field} must be a positive number or null, got {value!r}")
    try:
        num = float(str(value).strip()) if isinstance(value, str) else float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValueError(f"gates.{field} must be a positive number or null, got {value!r}") from None
    if not num > 0 or num != num or num == float("inf"):
        raise ValueError(f"gates.{field} must be > 0 (or null for no limit), got {value!r}")
    if as_int:
        if num != int(num):
            raise ValueError(f"gates.{field} must be a whole number, got {value!r}")
        return int(num)
    return float(num)


def _coerce_language(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"gates.required_language must be an ISO code string or null, got {value!r}")
    code = value.strip().lower().replace("_", "-")
    if code in ("", "any", "*", "none", "null"):
        return None
    if not re.fullmatch(r"[a-z]{2,3}(-[a-z0-9]{2,8})*", code):
        raise ValueError(f"gates.required_language must be an ISO 639-1 code like 'en', got {value!r}")
    return code


def _coerce_keywords(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise ValueError(f"gates.required_keywords must be a list of strings, got {value!r}")
    out: list[str] = []
    for kw in value:
        if not isinstance(kw, str):
            raise ValueError(f"gates.required_keywords items must be strings, got {kw!r}")
        low = kw.lower()
        if low.strip() and low not in out:
            out.append(low)
    return out


def _coerce_criteria(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError(f"criteria must be a list, got {type(value).__name__}")
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, str):
            name, desc = item, ""
        elif isinstance(item, dict):
            name = item.get("name") or item.get("criterion") or item.get("title") or ""
            desc = item.get("description") or ""
        else:
            raise ValueError(f"criteria items must be strings or objects, got {item!r}")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"every criterion needs a non-empty 'name', got {item!r}")
        name = re.sub(r"\s+", " ", name.strip())
        if name.casefold() in seen:
            continue
        seen.add(name.casefold())
        out.append({"name": name, "description": str(desc).strip()})
    if not out:
        raise ValueError("criteria must contain at least 1 criterion")
    return out


def _coerce_awards(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"awards must be a list of strings (or []), got {value!r}")
    out: list[str] = []
    for item in value:
        name = item.get("name") if isinstance(item, dict) else item
        if not isinstance(name, str):
            raise ValueError(f"awards items must be strings, got {item!r}")
        name = re.sub(r"\s+", " ", name.strip())
        if name and name not in out:
            out.append(name)
    return out


def _read_json(path: Path) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON ({e})") from None


# ---------------------------------------------------------------------------
# hackathon_settings.json
# ---------------------------------------------------------------------------
def default_settings() -> dict[str, Any]:
    return {
        "hackathon_name": DEFAULT_HACKATHON_NAME,
        "gates": copy.deepcopy(DEFAULT_GATES),
        "criteria": copy.deepcopy(DEFAULT_CRITERIA),
        "awards": list(DEFAULT_AWARDS),
        "is_default": True,
    }


def normalize_settings(raw: object) -> dict[str, Any]:
    """Merge a raw hackathon_settings object over the NASA defaults and validate every field."""
    settings = default_settings()
    if raw is None:
        return settings
    if not isinstance(raw, dict):
        raise ValueError("hackathon settings must be a JSON object")
    settings["is_default"] = False

    name = raw.get("hackathon_name")
    if isinstance(name, str) and name.strip():
        settings["hackathon_name"] = re.sub(r"\s+", " ", name.strip())

    gates_raw = raw.get("gates", {})
    if gates_raw is None:
        gates_raw = {}
    if not isinstance(gates_raw, dict):
        raise ValueError("gates must be a JSON object")
    gates = settings["gates"]
    for key, value in gates_raw.items():
        if _is_private_key(key):
            continue
        if key == "max_slides":
            gates[key] = _coerce_positive_number(value, key, as_int=True)
        elif key == "max_video_sec":
            gates[key] = _coerce_positive_number(value, key, as_int=False)
        elif key in ("require_demo_file", "require_references", "require_ai_disclosure"):
            gates[key] = _coerce_bool(value, key)
        elif key == "required_language":
            gates[key] = _coerce_language(value)
        elif key == "required_keywords":
            gates[key] = _coerce_keywords(value)

    if "criteria" in raw:
        settings["criteria"] = _coerce_criteria(raw["criteria"])
    if "awards" in raw:
        settings["awards"] = _coerce_awards(raw["awards"])
    return settings


def load_settings_file(path: Path) -> dict[str, Any]:
    try:
        return normalize_settings(_read_json(path))
    except ValueError as e:
        raise ValueError(f"{Path(path).name}: {e}") from None


def resolve_settings(inp_dir: Path) -> dict[str, Any]:
    """Return settings from `<inp_dir>/hackathon_settings.json` if present, else the NASA defaults."""
    path = Path(inp_dir) / SETTINGS_FILENAME
    return load_settings_file(path) if path.is_file() else default_settings()


def criterion_names(settings: dict[str, Any]) -> list[str]:
    return [c["name"] for c in settings["criteria"]]


def max_total(settings_or_criteria: dict[str, Any] | list) -> int:
    """5 points per criterion: 25 for the 5 NASA criteria, 20 for K=4, etc."""
    crit = (
        settings_or_criteria["criteria"]
        if isinstance(settings_or_criteria, dict)
        else settings_or_criteria
    )
    return 5 * len(crit)


def uses_default_keywords(gates: dict[str, Any]) -> bool:
    return list(gates.get("required_keywords") or []) == DEFAULT_REQUIRED_KEYWORDS


# ---------------------------------------------------------------------------
# judges.json
# ---------------------------------------------------------------------------
def sanitize_judge_id(value: object, fallback: str) -> str:
    """Judge ids travel through shell commands and file names: keep [A-Za-z0-9_-] only."""
    jid = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "").strip()).strip("_-")
    return jid[:64] or fallback


_TIER_LABELS = {
    "TIER_1_LOCAL": "local hackathon",
    "TIER_2_SME": "subject-matter expert",
    "TIER_3_EXEC": "executive",
}

_ROLE_FIELDS: tuple[tuple[str, str], ...] = (
    ("bio", "Public professional profile"),
    ("expertise", "Expertise"),
    ("signature_criteria", "Signature criteria you reward most"),
    ("red_flags", "Red flags that make you lower a score"),
    ("judging_style", "Judging style"),
)


def _as_text(value: object) -> str:
    if isinstance(value, list):
        return "; ".join(str(v).strip() for v in value if str(v).strip())
    if isinstance(value, dict):
        return "; ".join(f"{k}: {_as_text(v)}" for k, v in value.items() if not _is_private_key(k))
    return str(value).strip() if value is not None else ""


def render_role(role: object, fallback: str) -> str:
    """Turn a role string, or a guided role object (title/bio/expertise/signature_criteria/red_flags),
    into the persona paragraph injected in the judge prompt."""
    if isinstance(role, str):
        return role.strip() or fallback
    if not isinstance(role, dict):
        return fallback
    parts: list[str] = []
    title = _as_text(role.get("title") or role.get("summary") or role.get("persona"))
    parts.append(f"You are {title.rstrip('.')}." if title else fallback)
    for key, label in _ROLE_FIELDS:
        txt = _as_text(role.get(key))
        if txt:
            parts.append(f"{label}: {txt.rstrip('.')}.")
    known = {"title", "summary", "persona"} | {k for k, _ in _ROLE_FIELDS}
    for key, value in role.items():
        if key in known or _is_private_key(key):
            continue
        txt = _as_text(value)
        if txt:
            parts.append(f"{str(key).replace('_', ' ').capitalize()}: {txt.rstrip('.')}.")
    return " ".join(parts)


def _normalize_one_judge(jid: str, spec: object, hackathon_name: str) -> dict[str, str]:
    if isinstance(spec, str):
        spec = {"role": spec}
    if not isinstance(spec, dict):
        raise ValueError(f"judge {jid!r} must be a JSON object, got {type(spec).__name__}")
    tier = normalize_tier(spec.get("tier"))
    try:
        temp = float(spec.get("temperature", 0.5))
    except (TypeError, ValueError):
        temp = 0.5
    if temp != temp or not 0.0 <= temp <= 2.0:
        temp = 0.5
    try:
        tlimit = int(float(spec.get("time_limit_sec", 300)))
    except (TypeError, ValueError):
        tlimit = 300
    if tlimit <= 0:
        tlimit = 300
    model = spec.get("preferred_model")
    model = model.strip() if isinstance(model, str) else ""
    queue = _as_text(spec.get("queue_pressure")) or (
        f"Project under review in the {hackathon_name} judging queue "
        f"(simulated {tlimit}-second review budget)"
    )
    role = render_role(spec.get("role"), fallback=f"You are a {_TIER_LABELS[tier]} judge at {hackathon_name}.")
    return {
        "tier": tier,
        "preferred_model": model,
        "temperature": f"{temp:.2f}",
        "time_limit_sec": str(tlimit),
        "queue_pressure": queue.rstrip("."),
        "role": role,
    }


def normalize_judges(raw: object, hackathon_name: str = DEFAULT_HACKATHON_NAME) -> dict[str, dict[str, str]]:
    """Accept `{"<id>": {...}}`, `{"judges": {...} | [...]}` or `[{"id": ...}, ...]` with 1..10 judges.

    Keys starting with "_" (e.g. `_AI_AGENT_INSTRUCTIONS`) are ignored. Ids are sanitized and de-duplicated.
    """
    if isinstance(raw, dict) and "judges" in raw and isinstance(raw["judges"], (dict, list)):
        raw = raw["judges"]
    items: list[tuple[object, object]] = []
    if isinstance(raw, dict):
        items = [(k, v) for k, v in raw.items() if not _is_private_key(k)]
    elif isinstance(raw, list):
        for spec in raw:
            jid = spec.get("id") or spec.get("judge_id") or spec.get("judge") if isinstance(spec, dict) else None
            items.append((jid, spec))
    else:
        raise ValueError("judges config must be a JSON object keyed by judge id (or a list of judges)")

    judges: dict[str, dict[str, str]] = {}
    for idx, (jid_raw, spec) in enumerate(items, 1):
        jid = sanitize_judge_id(jid_raw, fallback=f"J{idx}")
        base, n = jid, 2
        while jid in judges:
            jid = f"{base}_{n}"
            n += 1
        judges[jid] = _normalize_one_judge(jid, spec, hackathon_name)
    if not MIN_JUDGES <= len(judges) <= MAX_JUDGES:
        raise ValueError(
            f"judges config must define between {MIN_JUDGES} and {MAX_JUDGES} judges, found {len(judges)}"
        )
    return judges


def load_judges_file(path: Path, hackathon_name: str = DEFAULT_HACKATHON_NAME) -> dict[str, dict[str, str]]:
    try:
        return normalize_judges(_read_json(path), hackathon_name)
    except ValueError as e:
        raise ValueError(f"{Path(path).name}: {e}") from None


def resolve_judges(inp_dir: Path, hackathon_name: str = DEFAULT_HACKATHON_NAME) -> dict[str, dict[str, str]]:
    """Return judges from `<inp_dir>/judges.json` if present, else the 5 NASA v3.0 personas."""
    path = Path(inp_dir) / JUDGES_FILENAME
    return load_judges_file(path, hackathon_name) if path.is_file() else copy.deepcopy(DEFAULT_JUDGES)
