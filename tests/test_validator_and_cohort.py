"""Unit tests for the 9 synthetic calibration archetypes, report.py's anti-hallucination functions,
and the universal hackathon / N-judge configuration (hackathon_settings.json + judges.json)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from spaceapps_judge import cli
from spaceapps_judge.vm import hackathon_config as hc
from spaceapps_judge.vm import panel, probes
from spaceapps_judge.vm.calibration_cohort import CALIBRATION_COHORT
from spaceapps_judge.vm.report import (
    JUDGE_ORDER,
    compute_calibration_for_judge,
    norm,
    resolve_report_config,
    run_report,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "templates"


def test_calibration_cohort_covers_all_four_tiers() -> None:
    assert len(CALIBRATION_COHORT) == 9
    tiers = {b["ground_truth_tier"] for b in CALIBRATION_COHORT}
    assert tiers == {1, 2, 3, 4}

    for b in CALIBRATION_COHORT:
        assert b["cohort_id"].startswith("SYNTH_ARCH_")
        lo, hi = b["expected_score_band"]
        assert 4 <= lo <= hi <= 25


def test_calibration_cohort_unique_ids_and_generic_judge_order() -> None:
    ids = [b["cohort_id"] for b in CALIBRATION_COHORT]
    assert len(ids) == len(set(ids)) == 9
    assert "SYNTH_ARCH_01_TIER4_COMPLETE_PORTAL" in ids
    assert "SYNTH_ARCH_09_TIER1_BROKEN_SCAFFOLD" in ids
    assert len(JUDGE_ORDER) == 5
    assert all(j.startswith("J") for j in JUDGE_ORDER)


def test_report_norm_handles_markdown_and_unicode_arrows() -> None:
    corpus = norm("**708 real ground-truth waypoints and measured rover tilts (Sol 13 → Sol 2022) recorded by**")
    quote = norm("708 real ground-truth waypoints and measured rover tilts (Sol 13 -> Sol 2022) recorded by")
    assert quote in corpus


FAKE_BALLOT_25 = [
    ("SYNTH_ARCH_02_TIER4_COMPLETE_PHYSICS", 1, 24),
    ("SYNTH_ARCH_01_TIER4_COMPLETE_PORTAL", 2, 23),
    ("SYNTH_ARCH_03_TIER3_3D_TERRAIN_VIEWER", 3, 20),
    ("CANDIDATE_SUBMISSION", 4, 20),
    ("SYNTH_ARCH_04_TIER3_PATH_PLANNER", 5, 19),
    ("SYNTH_ARCH_05_TIER2_ANALOG_MAPPER", 6, 17),
    ("SYNTH_ARCH_06_TIER2_TILE_VIEWER", 7, 16),
    ("SYNTH_ARCH_07_TIER1_BACKEND_NO_DEMO", 8, 14),
    ("SYNTH_ARCH_08_TIER1_CHAT_WRAPPER", 9, 11),
    ("SYNTH_ARCH_09_TIER1_BROKEN_SCAFFOLD", 10, 7),
]


def _cohort(max_total: int) -> list[dict]:
    key = f"total_{max_total}"
    return [
        {"cohort_id": cid, "rank": rank, key: round(score * max_total / 25), "one_line_verdict": "Strong math"}
        for cid, rank, score in FAKE_BALLOT_25
    ]


def test_compute_calibration_for_judge_monotonic_ranking() -> None:
    cal = compute_calibration_for_judge({"cohort_ranking": _cohort(25)})
    assert cal["calibrated"] is True
    assert cal["tau_concordance"] == 1.0
    assert cal["band_hits_of_9"] == 9
    assert cal["candidate_rank_of_10"] == 4
    assert cal["candidate_cohort_score_25"] == 20


def test_compute_calibration_rescales_bands_to_max_total_20() -> None:
    cal = compute_calibration_for_judge({"cohort_ranking": _cohort(20)}, max_total=20)
    assert cal["calibrated"] is True
    assert cal["tau_concordance"] == 1.0
    assert cal["band_hits_of_9"] == 9
    assert cal["candidate_cohort_score_20"] == 16
    assert cal["candidate_cohort_score"] == 16
    assert cal["cohort_max_total"] == 20
    # A /20 ballot read on the default /25 key finds no totals -> not calibrated (no silent scale mixing).
    assert compute_calibration_for_judge({"cohort_ranking": _cohort(20)})["benchmarks_scored"] == 0
    assert compute_calibration_for_judge({})["calibrated"] is False


# ---------------------------------------------------------------------------
# Tier normalization (EC5) & config validation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("TIER_1_LOCAL", "TIER_1_LOCAL"),
        ("tier_2_sme", "TIER_2_SME"),
        ("TIER_3_EXEC", "TIER_3_EXEC"),
        ("SME", "TIER_2_SME"),
        ("TECHNICAL", "TIER_2_SME"),
        ("technical expert", "TIER_2_SME"),
        ("LOCAL", "TIER_1_LOCAL"),
        ("Local Reviewer", "TIER_1_LOCAL"),
        ("EXEC", "TIER_3_EXEC"),
        ("VIP", "TIER_3_EXEC"),
        ("Sponsor VIP Judge", "TIER_3_EXEC"),
        (3, "TIER_3_EXEC"),
        ("wizard", "TIER_2_SME"),
        ("", "TIER_2_SME"),
        (None, "TIER_2_SME"),
        (True, "TIER_2_SME"),
    ],
)
def test_normalize_tier_aliases_and_unknown_default_to_sme(raw: object, expected: str) -> None:
    assert hc.normalize_tier(raw) == expected


def test_unknown_tier_is_never_truncated_to_350_words() -> None:
    long_text = " ".join(f"word{i}" for i in range(2000))
    assert panel.build_blind_triage_excerpt(long_text, "SOMETHING_UNKNOWN") == long_text
    assert len(panel.build_blind_triage_excerpt(long_text, "TIER_1_LOCAL").split()) <= 350


def test_settings_template_is_valid_and_equals_nasa_defaults() -> None:
    loaded = hc.load_settings_file(TEMPLATES / "hackathon_settings_template.json")
    defaults = hc.default_settings()
    assert loaded["is_default"] is False and defaults["is_default"] is True
    for key in ("hackathon_name", "gates", "criteria", "awards"):
        assert loaded[key] == defaults[key], key
    assert hc.uses_default_keywords(loaded["gates"])


def test_judge_panel_template_is_valid_and_normalizes_tier_aliases() -> None:
    judges = hc.load_judges_file(TEMPLATES / "judge_panel_template.json")
    assert list(judges) == [
        "J1_local_generalist_reviewer",
        "J2_technical_sme_reviewer",
        "J3_sponsor_exec_reviewer",
    ]
    assert [j["tier"] for j in judges.values()] == ["TIER_1_LOCAL", "TIER_2_SME", "TIER_3_EXEC"]
    role = judges["J2_technical_sme_reviewer"]["role"]
    assert role.startswith("You are a subject-matter expert judge")
    assert "Signature criteria you reward most:" in role and "Red flags that make you lower a score:" in role
    assert judges["J1_local_generalist_reviewer"]["temperature"] == "0.65"


def test_rules_template_has_ai_instructions_and_both_parts() -> None:
    text = (TEMPLATES / "hackathon_rules_template.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- AI AGENT INSTRUCTIONS -->")
    assert "PART A -> hackathon_rules.md" in text and "PART B -> challenge_brief.md" in text
    for name in ("hackathon_settings_template.json", "judge_panel_template.json"):
        raw = json.loads((TEMPLATES / name).read_text(encoding="utf-8"))
        assert raw["_AI_AGENT_INSTRUCTIONS"][0] == "<!-- AI AGENT INSTRUCTIONS -->"


def test_judges_config_validation_ids_bounds_and_shapes(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="between 1 and 10"):
        hc.normalize_judges({"_AI_AGENT_INSTRUCTIONS": ["x"]})
    with pytest.raises(ValueError, match="between 1 and 10"):
        hc.normalize_judges({f"J{i}": {"tier": "SME"} for i in range(11)})
    with pytest.raises(ValueError):
        hc.normalize_judges("not a panel")
    with pytest.raises(ValueError):
        hc.normalize_judges({"J1": 42})

    listed = hc.normalize_judges(
        {"judges": [{"id": "Dr. Ada / SME", "tier": "expert"}, {"id": "Dr. Ada / SME"}, {"role": "plain persona"}]}
    )
    assert list(listed) == ["Dr_Ada_SME", "Dr_Ada_SME_2", "J3"]
    assert listed["J3"]["role"] == "plain persona"
    weird = hc.normalize_judges({"J1": {"temperature": "hot", "time_limit_sec": -5, "preferred_model": 7}})["J1"]
    assert weird == {
        "tier": "TIER_2_SME",
        "preferred_model": "",
        "temperature": "0.50",
        "time_limit_sec": "300",
        "queue_pressure": (
            "Project under review in the NASA Space Apps Challenge 2026 judging queue "
            "(simulated 300-second review budget)"
        ),
        "role": "You are a subject-matter expert judge at NASA Space Apps Challenge 2026.",
    }

    bom = tmp_path / "judges.json"
    bom.write_text("﻿" + json.dumps({"J1": {"tier": "LOCAL"}}), encoding="utf-8")
    assert hc.resolve_judges(tmp_path)["J1"]["tier"] == "TIER_1_LOCAL"
    (tmp_path / "judges.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="judges.json: invalid JSON"):
        hc.resolve_judges(tmp_path)
    assert hc.resolve_judges(tmp_path / "missing") == hc.DEFAULT_JUDGES


def test_settings_validation_merges_defaults_and_rejects_nonsense() -> None:
    s = hc.normalize_settings(
        {
            "hackathon_name": "  Devpost   Demo Day ",
            "gates": {
                "max_slides": "15",
                "max_video_sec": None,
                "required_language": "any",
                "required_keywords": None,
                "require_references": "no",
                "_note": "ignored",
            },
            "criteria": ["Impact", {"criterion": "Design"}, {"name": "impact"}],
            "awards": [{"name": "Grand Prize"}, "Grand Prize", " "],
        }
    )
    assert s["hackathon_name"] == "Devpost Demo Day"
    assert s["gates"]["max_slides"] == 15 and s["gates"]["max_video_sec"] is None
    assert s["gates"]["required_language"] is None and s["gates"]["required_keywords"] == []
    assert s["gates"]["require_references"] is False
    assert s["gates"]["require_ai_disclosure"] is True  # omitted -> NASA default
    assert hc.criterion_names(s) == ["Impact", "Design"]
    assert hc.max_total(s) == 10
    assert s["awards"] == ["Grand Prize"]
    for bad in (
        {"gates": {"max_slides": "abc"}},
        {"gates": {"max_slides": 2.5}},
        {"gates": {"max_video_sec": 0}},
        {"gates": {"max_video_sec": True}},
        {"gates": {"require_demo_file": "maybe"}},
        {"gates": {"required_language": "english!"}},
        {"gates": {"required_language": 1}},
        {"gates": {"required_keywords": [1]}},
        {"gates": {"required_keywords": {}}},
        {"gates": []},
        {"criteria": []},
        {"criteria": [{"description": "no name"}]},
        {"criteria": [3]},
        {"criteria": "Impact"},
        {"awards": "Grand Prize"},
        {"awards": [3]},
        ["not", "an", "object"],
    ):
        with pytest.raises(ValueError):
            hc.normalize_settings(bad)
    assert hc.normalize_settings({"gates": None, "awards": None})["awards"] == []
    assert hc.normalize_settings({"gates": {"required_keywords": "solana"}})["gates"]["required_keywords"] == ["solana"]
    assert hc.normalize_settings({"gates": {"require_demo_file": 0}})["gates"]["require_demo_file"] is False


# ---------------------------------------------------------------------------
# Panel prompt (EC1/EC3/EC4): exact v3.0 default + dynamic K criteria
# ---------------------------------------------------------------------------
V30_INSTRUCTIONS_SHA256 = "616198dd0c8659ec8a4aa8f0c01d934c011469ad11b7ed9d276deb0f01f14227"


def test_panel_default_instructions_are_byte_identical_to_v30() -> None:
    assert hashlib.sha256(panel.INSTRUCTIONS.encode("utf-8")).hexdigest() == V30_INSTRUCTIONS_SHA256
    assert panel.JUDGES == hc.DEFAULT_JUDGES and len(panel.JUDGES) == 5
    assert "`total_25` score (5 to 25)" in panel.INSTRUCTIONS
    assert '"<one of the 10 official awards>"' in panel.INSTRUCTIONS


def test_panel_instructions_for_four_criteria_on_20_and_award_lists() -> None:
    crit = ["Innovation", "Technical Execution", "Impact", "Demo"]
    text = panel.build_instructions(crit, ["Best AI Agent"], "ETHGlobal Online 2026")
    assert "Score each of the 4 official criteria (Innovation, Technical Execution, Impact, Demo)" in text
    assert "`total_20` score (4 to 20)" in text and "total_25" not in text
    assert "sum of your 4 criterion scores" in text
    assert text.count('"criterion": ') == 4 + 2  # 4 score rows + weakness + fix examples
    assert '"criterion": "Demo",                "score": 1' in text
    assert ">=95% of ETHGlobal Online 2026 entries" in text
    assert "any presentation/demo-related criterion is capped" in text
    assert "<the 1 official award, only if it genuinely fits>" in text
    assert "no official award list" in panel.build_instructions(crit, [], "X")
    single = panel.build_instructions(["Overall"], [], "X")
    assert "`total_5` score (1 to 5)" in single and '"criterion": "Overall"' in single
    with pytest.raises(ValueError):
        panel.build_instructions([], [], "X")


def test_panel_criteria_section_only_for_custom_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    assert panel.build_criteria_section() == ""
    custom = hc.normalize_settings(
        {"hackathon_name": "ETHGlobal", "criteria": [{"name": "Originality", "description": "New idea."}, "Demo"]}
    )
    monkeypatch.setattr(panel, "SETTINGS", custom)
    section = panel.build_criteria_section()
    assert section.startswith("# HACKATHON SCORING CRITERIA (ETHGlobal — 2 criteria, each 1-5, total /10)")
    assert "- **Originality**: New idea." in section and "- **Demo**" in section


# ---------------------------------------------------------------------------
# End-to-end report fixtures (Wave 3 on the host, no network, no LLM)
# ---------------------------------------------------------------------------
SUB_TEXT = (
    "# AgentBridge\n"
    "AgentBridge routes support tickets to autonomous agents with deterministic guardrails.\n"
    "Every agent action is replayed in a sandbox before it touches production data.\n"
    "The live demo shows a ticket resolved end to end in under ten seconds.\n"
    "## References\n"
    "- https://example.org/agents-paper\n"
    "## AI disclosure\n"
    "I used generative AI tools for boilerplate and reviewed every line myself.\n"
)
QUOTES = [
    "routes support tickets to autonomous agents with deterministic guardrails",
    "Every agent action is replayed in a sandbox before it touches production data",
    "The live demo shows a ticket resolved end to end in under ten seconds",
    "I used generative AI tools for boilerplate and reviewed every line myself",
]
CUSTOM_CRITERIA = [
    {"name": "Innovation", "description": "Novelty of the agent design."},
    {"name": "Technical Execution", "description": "Working, tested, reproducible."},
    {"name": "Impact", "description": "Real users and measurable value."},
    {"name": "Demo", "description": "Clarity of the live demo."},
]
NON_NASA_SETTINGS = {
    "hackathon_name": "Agents Hack 2026",
    "gates": {
        "max_slides": 15,
        "max_video_sec": 180,
        "require_demo_file": True,
        "required_language": "en",
        "required_keywords": [],
        "require_references": True,
        "require_ai_disclosure": True,
    },
    "criteria": CUSTOM_CRITERIA,
    "awards": ["Best AI Agent"],
}
PASSING_GATES = [
    {"id": f"G-0{i}", "probe": p, "status": "PASS", "tier": "ALL", "fact": f"{p} ok", "excerpt": ""}
    for i, p in enumerate(
        ["required_fields", "public_url_no_login", "repo_public", "demo_limits", "english_language",
         "required_keywords_cited", "references_listed", "ai_disclosure"],
        1,
    )
] + [
    {"id": "E-01", "probe": "repo_clone", "status": "PASS", "tier": "ALL", "fact": "Cloned.", "excerpt": ""}
]


def _custom_judges(n: int) -> dict:
    tiers = ["LOCAL", "TECHNICAL", "VIP", "TIER_2_SME", "sme", "Local"]
    return {
        f"J{i}_reviewer_{i}": {
            "tier": tiers[(i - 1) % len(tiers)],
            "preferred_model": "gemini-3.8-flash",
            "temperature": 0.5,
            "time_limit_sec": 240,
            "role": {
                "title": f"judge number {i}",
                "expertise": ["agents"],
                "red_flags": ["no demo"],
                "notable_work": {"talk": "Agents at scale", "_private": "skip"},
                "_note": "ignored",
            },
        }
        for i in range(1, n + 1)
    }


def _ballot(jid: str, criteria: list[str], scores: list[int], max_total: int, award: str) -> dict:
    return {
        "judge": jid,
        "tier": "TIER_2_SME",
        "_model": "gemini-3.8-flash",
        "scores": [
            {
                "criterion": c,
                "score": s,
                "justification": f"{c} is supported by the submission text.",
                "evidence_ids": ["SUB", "E-01"],
                "quotes": [QUOTES[i % len(QUOTES)]],
            }
            for i, (c, s) in enumerate(zip(criteria, scores))
        ],
        "cohort_ranking": _cohort(max_total),
        "strengths": [{"text": "Sandbox replay.", "evidence_ids": ["SUB"]}],
        "weaknesses": [{"text": f"Gap {k}", "criterion": criteria[-1], "evidence_ids": ["SUB"]} for k in range(3)],
        "fixes_before_deadline": [
            {"action": "Record demo.", "criterion": criteria[-1], "expected_gain": 1, "effort_minutes": 20,
             "evidence_ids": ["SUB"]}
        ],
        "award_fit": [{"award": award, "rationale": "Fits.", "evidence_ids": ["SUB"]}],
        "nominate_global": True,
        "nominate_rationale": "Solid.",
        "judge_debrief": {"what_i_judged_and_how": "Demo.", "must_keep_sacred": ["replay"]},
        "time_pressure_audit": {"time_limit_sec": 240, "simulated_review_sec": 200},
    }


def _write_run(
    tmp_path: Path,
    evidence: list[dict],
    ballots: list[dict],
    settings: dict | None = None,
    judges: dict | None = None,
    manifest: dict | None = None,
) -> tuple[Path, Path]:
    inp = tmp_path / "submission"
    out = tmp_path / "report"
    inp.mkdir()
    out.mkdir()
    (inp / "submission.json").write_text(
        json.dumps({"project_title": "AgentBridge", "challenge": "Agents track",
                    "submission_text_file": "submission_text.md"}),
        encoding="utf-8",
    )
    (inp / "submission_text.md").write_text(SUB_TEXT, encoding="utf-8")
    if settings is not None:
        (inp / "hackathon_settings.json").write_text(json.dumps(settings), encoding="utf-8")
    if judges is not None:
        (inp / "judges.json").write_text(json.dumps(judges), encoding="utf-8")
    if manifest is not None:
        (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (out / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    (out / "panel_raw.json").write_text(json.dumps(ballots), encoding="utf-8")
    return out, inp


@pytest.mark.parametrize("n_judges", [4, 6])
def test_custom_panel_of_n_judges_scores_four_criteria_on_20(tmp_path: Path, n_judges: int) -> None:
    judges = _custom_judges(n_judges)
    norm_judges = hc.normalize_judges(judges)
    assert len(norm_judges) == n_judges
    assert norm_judges["J2_reviewer_2"]["tier"] == "TIER_2_SME"  # "TECHNICAL" alias
    assert norm_judges["J3_reviewer_3"]["tier"] == "TIER_3_EXEC"  # "VIP" alias
    assert norm_judges["J1_reviewer_1"]["role"] == (
        "You are judge number 1. Expertise: agents. Red flags that make you lower a score: no demo. "
        "Notable work: talk: Agents at scale."
    )
    assert set(j["tier"] for j in norm_judges.values()) <= set(hc.VALID_TIERS)

    names = [c["name"] for c in CUSTOM_CRITERIA]
    ballots = [_ballot(jid, names, [4, 3, 5, 4], 20, "Best AI Agent") for jid in norm_judges]
    out, inp = _write_run(tmp_path, PASSING_GATES, ballots, NON_NASA_SETTINGS, judges)

    # panel.py inside the VM resolves exactly the same N judges / K criteria from /judge/input
    assert list(hc.resolve_judges(inp)) == list(norm_judges)
    assert hc.criterion_names(hc.resolve_settings(inp)) == names

    assert run_report(out, inp) == 0
    res = json.loads((out / "judgement.json").read_text(encoding="utf-8"))
    assert res["max_total"] == 20 and res["judge_count"] == n_judges
    assert res["criteria_names"] == names
    assert res["total"] == 16 and res["total_pct_100"] == 80.0
    assert res["total_mean"] == 16 and res["total_mean_pct_100"] == 80.0
    assert res["rejections"] == []
    assert res["eligible"] is True
    assert res["awards"] == {"Best AI Agent": list(norm_judges)}
    assert all(t["max_possible"] == 20 and t["raw_total"] == 16 for t in res["judge_totals"].values())
    assert all(c["calibrated"] and c["candidate_cohort_score_20"] == 16 for c in res["calibration_by_judge"].values())

    md = (out / "JUDGEMENT_REPORT.md").read_text(encoding="utf-8")
    assert f"& {n_judges} MicroVMs E2B" in md and f"de {n_judges} juges isolés E2B · Agents Hack 2026" in md
    assert "**16/20**" in md and "16 / 20" in md and "`16/20`" in md
    assert "/25" not in md
    assert "Prix visables (sur les 1 officiels — Agents Hack 2026)" in md


def test_non_nasa_settings_gates_pass_and_report_on_20_without_award_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inp = tmp_path / "vm_input"
    inp.mkdir()
    (inp / "demo.mp4").write_bytes(b"\x00")
    settings = hc.normalize_settings(NON_NASA_SETTINGS)

    def fake_sh(cmd: str, timeout: int = 300, cwd: Path | None = None) -> tuple[int, str]:
        if cmd.startswith("curl"):
            return 0, "200 https://agentbridge.example.org/"
        return 0, "0123abcd\trefs/heads/main"

    monkeypatch.setattr(probes, "evidence", [])
    monkeypatch.setattr(probes, "INP", inp)
    monkeypatch.setattr(probes, "SETTINGS", settings)
    monkeypatch.setattr(probes, "SUB_TEXT", SUB_TEXT)
    monkeypatch.setattr(
        probes,
        "SUB",
        {"project_title": "AgentBridge", "challenge": "Agents track", "public_url": "https://agentbridge.example.org",
         "repo_url": "https://example.org/agentbridge.git", "demo_file": "demo.mp4",
         "deadline_local_iso": "2026-12-01T23:59:00-05:00"},
    )
    monkeypatch.setattr(probes, "sh", fake_sh)
    monkeypatch.setattr(probes, "_video_duration_sec", lambda p: 120.0)
    monkeypatch.setattr(probes, "_detect_langs", lambda text: [("en", 0.999)])

    probes.gate()
    gates = {e["id"]: e for e in probes.evidence}
    assert [e["id"] for e in probes.evidence] == [f"G-0{i}" for i in range(1, 10)]
    assert not [e for e in probes.evidence if e["status"] == "FAIL"], probes.evidence
    assert gates["G-04"]["fact"] == "Demo video duration 120.00 s (limit 180 s)."
    assert gates["G-05"]["probe"] == "english_language" and gates["G-05"]["status"] == "PASS"
    assert gates["G-06"]["probe"] == "required_keywords_cited"
    assert gates["G-06"]["status"] == "PASS"
    assert gates["G-06"]["fact"] == "No mandatory sponsor/dataset keywords required by hackathon settings."
    assert "2026-12-01T23:59:00-05:00 (Agents Hack 2026)" in gates["G-09"]["fact"]

    # Same submission under the NASA defaults would be blocked (30 s video limit, NASA keywords).
    nasa = hc.default_settings()["gates"]
    assert probes.check_demo_limits(inp, "demo.mp4", nasa) == ("FAIL", "Demo video duration 120.00 s (limit 30 s).")
    assert probes.check_required_keywords(SUB_TEXT, nasa["required_keywords"])[0] == "FAIL"

    names = [c["name"] for c in CUSTOM_CRITERIA]
    judges = _custom_judges(4)
    ballots = [_ballot(jid, names, [5, 4, 4, 3], 20, "Best AI Agent") for jid in hc.normalize_judges(judges)]
    evidence = probes.evidence + [PASSING_GATES[-1]]
    out, sub_dir = _write_run(tmp_path, evidence, ballots, NON_NASA_SETTINGS, judges)
    assert run_report(out, sub_dir) == 0
    res = json.loads((out / "judgement.json").read_text(encoding="utf-8"))
    assert res["eligible"] is True and res["gate_failures"] == []
    assert res["max_total"] == 20 and res["total"] == 16 and res["total_pct_100"] == 80.0
    assert res["official_awards"] == ["Best AI Agent"]
    assert sorted(res["awards"]["Best AI Agent"]) == sorted(hc.normalize_judges(judges))
    assert not [r for r in res["rejections"] if "award_fit" in r]
    md = (out / "JUDGEMENT_REPORT.md").read_text(encoding="utf-8")
    assert "ADMISSIBLE (contrôles automatiques)" in md and "NON ADMISSIBLE" not in md


def test_empty_awards_list_accepts_any_award_fit(tmp_path: Path) -> None:
    settings = {**NON_NASA_SETTINGS, "awards": []}
    names = [c["name"] for c in CUSTOM_CRITERIA]
    judges = _custom_judges(1)
    ballots = [_ballot("J1_reviewer_1", names, [3, 3, 3, 3], 20, "Totally Custom Prize")]
    ballots[0]["award_fit"] += ["Bare String Prize", {"award": "", "evidence_ids": []}, 7,
                                {"award": "Bad Ids", "evidence_ids": ["E-99"]}]
    out, inp = _write_run(tmp_path, PASSING_GATES, ballots, settings, judges)
    assert run_report(out, inp) == 0
    res = json.loads((out / "judgement.json").read_text(encoding="utf-8"))
    assert res["awards"] == {"Totally Custom Prize": ["J1_reviewer_1"], "Bare String Prize": ["J1_reviewer_1"]}
    award_rej = [r for r in res["rejections"] if "award_fit" in r]
    assert award_rej == [
        "J1_reviewer_1 / award_fit: rejected item ''",
        "J1_reviewer_1 / award_fit: rejected malformed item 7",
        "J1_reviewer_1 / award_fit: rejected item 'Bad Ids'",
    ]
    md = (out / "JUDGEMENT_REPORT.md").read_text(encoding="utf-8")
    assert "aucune liste officielle, catégories libres" in md


def test_default_nasa_run_is_unchanged_on_25(tmp_path: Path) -> None:
    names = [c["name"] for c in hc.DEFAULT_CRITERIA]
    ballots = [_ballot(jid, names, [4, 5, 5, 5, 2], 25, "Best Use of Data") for jid in hc.DEFAULT_JUDGE_ORDER]
    ballots[0]["award_fit"].append({"award": "Best AI Agent", "evidence_ids": ["SUB"]})
    ballots[1]["scores"].append(dict(ballots[1]["scores"][0], criterion="Innovation"))
    out, inp = _write_run(tmp_path, PASSING_GATES, ballots)
    assert run_report(out, inp) == 0
    res = json.loads((out / "judgement.json").read_text(encoding="utf-8"))
    assert res["hackathon_name"] == "NASA Space Apps Challenge 2026"
    assert res["max_total"] == 25 and res["judge_count"] == 5 and res["total"] == 21
    assert res["total_pct_100"] == 84.0
    assert "J1_local_ux_ai_reviewer / award_fit: rejected item 'Best AI Agent'" in res["rejections"]
    assert any("unknown criterion 'Innovation'" in r for r in res["rejections"])
    md = (out / "JUDGEMENT_REPORT.md").read_text(encoding="utf-8")
    assert "& 5 MicroVMs E2B" in md and "**21/25**" in md and "Prix visables (sur les 10 officiels" in md


def test_validator_rejects_hallucinated_scores_on_custom_scale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names = [c["name"] for c in CUSTOM_CRITERIA]
    good = _ballot("J1_reviewer_1", names, [5, 5, 5, 5], 20, "Best AI Agent")
    good.update(
        {
            "adds_professional_value": True,
            "adds_professional_value_rationale": "Useful.",
            "_model": "other-model",
            "judge_debrief": {"why_this_score": "Strong.", "must_keep_sacred": "the replay sandbox"},
            "time_pressure_audit": {"thirty_second_impression": "Clear demo.", "time_limit_sec": 240},
        }
    )
    hostile = _ballot("J2_reviewer_2", names, [5, 5, 5, 5], 20, "Best AI Agent")
    hostile["scores"] = [
        {"criterion": "Innovation", "score": 6, "evidence_ids": [], "quotes": []},
        {"criterion": "Impact", "score": 4, "evidence_ids": ["E-77"], "quotes": ["a fabricated quote nobody wrote"]},
        dict(good["scores"][1], criterion="Technical Execution"),
        dict(good["scores"][1], criterion="Technical Execution"),
    ]
    hostile["weaknesses"] = [{"text": "one", "evidence_ids": ["SUB"]}]
    hostile.pop("judge_debrief")
    hostile["cohort_ranking"] = list(reversed(_cohort(20)))
    for row, (cid, _, _) in zip(hostile["cohort_ranking"], FAKE_BALLOT_25):
        row["cohort_id"] = cid  # same scores, inverted identities -> discordant
    panel_dict = {
        "J1_reviewer_1": good,
        "J2_reviewer_2": hostile,
        "J3_reviewer_3": {"judge": "J3_reviewer_3", "_error": "VM failure"},
    }
    failing_gate = [dict(PASSING_GATES[3], status="FAIL", fact="No demo file provided.")]
    out, inp = _write_run(
        tmp_path, failing_gate + PASSING_GATES[4:], [], NON_NASA_SETTINGS, _custom_judges(3),
        manifest={"model": "gemini-3.8-flash"},
    )
    (out / "panel_raw.json").write_text(json.dumps(panel_dict), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["report.py", str(out), str(inp)])
    from spaceapps_judge.vm import report as report_mod

    assert report_mod.main() == 0
    res = json.loads((out / "judgement.json").read_text(encoding="utf-8"))
    rej = res["rejections"]
    assert "J3_reviewer_3: judge call FAILED entirely (no output) -> excluded." in rej
    assert any(r.startswith("J2_reviewer_2 / Innovation: REJECTED") and "score 6 not an int 1-5" in r
               and "no evidence id cited" in r and "no verbatim quote" in r for r in rej)
    assert any("unknown evidence ids ['E-77']" in r and "quote not found verbatim" in r for r in rej)
    assert any("J2_reviewer_2 / Technical Execution: REJECTED (duplicate criterion)" == r for r in rej)
    assert "J2_reviewer_2 / Demo: MISSING from judge output" in rej
    assert any("J2_reviewer_2 / severity_check: WARN (only 1 weaknesses" in r for r in rej)
    assert res["eligible"] is False and res["est_finalist_prob_pct"] == 0.0
    assert res["criteria"]["Technical Execution"]["by_judge"] == {"J1_reviewer_1": 5, "J2_reviewer_2": 5}
    assert res["criteria"]["Innovation"]["by_judge"] == {"J1_reviewer_1": 5}
    inverted = res["calibration_by_judge"]["J2_reviewer_2"]
    assert inverted["tau_concordance"] < -0.9 and inverted["calibrated"] is False
    md = (out / "JUDGEMENT_REPORT.md").read_text(encoding="utf-8")
    assert "NON ADMISSIBLE" in md and "🔒 the replay sandbox" in md and "Clear demo." in md
    assert "modèle distinct ou de repli" in md and "`J1_reviewer_1` = OUI" in md

    (out / "panel_raw.json").write_text('"garbage"', encoding="utf-8")
    assert report_mod.run_report(out, inp) == 0
    empty = json.loads((out / "judgement.json").read_text(encoding="utf-8"))
    assert empty["judge_count"] == 0 and empty["total"] == 0 and empty["max_total"] == 20
    monkeypatch.setattr("sys.argv", ["report.py", str(out)])
    with pytest.raises(FileNotFoundError):  # inp_dir defaults to out_dir, which has no submission.json
        report_mod.main()


def test_panel_vm_runtime_loads_custom_panel_and_guards_unknown_judge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "judge"
    for sub in ("rubric", "input", "out"):
        (root / sub).mkdir(parents=True)
    (root / "rubric" / "judging_guide_2026.md").write_text("# Agents Hack rules", encoding="utf-8")
    (root / "rubric" / "challenge_martian_map_2026.md").write_text("# Agents track brief", encoding="utf-8")
    (root / "input" / "submission.json").write_text(
        json.dumps({"project_title": "AgentBridge", "challenge": "Agents track",
                    "submission_text_file": "submission_text.md"}),
        encoding="utf-8",
    )
    (root / "input" / "submission_text.md").write_text(SUB_TEXT, encoding="utf-8")
    (root / "input" / "hackathon_settings.json").write_text(json.dumps(NON_NASA_SETTINGS), encoding="utf-8")
    (root / "input" / "judges.json").write_text(json.dumps(_custom_judges(4)), encoding="utf-8")
    (root / "out" / "evidence.json").write_text(json.dumps(PASSING_GATES), encoding="utf-8")

    for name in ("RUBRIC", "CHALLENGE", "SUB", "SUB_TEXT", "EVIDENCE", "SETTINGS", "JUDGES", "CRITERIA",
                 "AWARDS", "INSTRUCTIONS"):
        monkeypatch.setattr(panel, name, getattr(panel, name))  # restored after the test
    monkeypatch.setattr(panel, "ROOT", root)
    monkeypatch.setattr(panel, "INP", root / "input")
    monkeypatch.setattr(panel, "OUT", root / "out")

    panel.load_runtime()
    assert list(panel.JUDGES) == [f"J{i}_reviewer_{i}" for i in range(1, 5)]
    assert panel.CRITERIA == [c["name"] for c in CUSTOM_CRITERIA] and panel.AWARDS == ["Best AI Agent"]
    prompt = panel.build_prompt("J2_reviewer_2", panel.JUDGES["J2_reviewer_2"])
    assert prompt.startswith("# YOUR JUDGE ID: J2_reviewer_2 (TIER_2_SME)")
    assert "`total_20` score (4 to 20)" in prompt and ">=95% of Agents Hack 2026 entries" in prompt
    assert "# HACKATHON SCORING CRITERIA (Agents Hack 2026 — 4 criteria, each 1-5, total /20)" in prompt
    assert "# OFFICIAL JUDGING GUIDE\n# Agents Hack rules" in prompt
    assert '# OFFICIAL GLOBAL AWARDS LIST\n["Best AI Agent"]' in prompt
    assert SUB_TEXT.strip() in prompt  # SME tier sees the full text

    monkeypatch.setattr(panel, "SINGLE_JUDGE", "J9_unknown")
    assert panel.main() == 2
    err = json.loads((root / "out" / "panel_J9_unknown.json").read_text(encoding="utf-8"))
    assert err["_error"].startswith("unknown judge id 'J9_unknown'") and err["scores"] == []


def test_report_prefers_sealed_manifest_config_over_input_files(tmp_path: Path) -> None:
    manifest = {
        "model": "gemini-3.8-flash",
        "judges": ["JX_only"],
        "hackathon_settings": {"hackathon_name": "Manifest Hack", "criteria": ["A", "B"], "awards": []},
    }
    out, inp = _write_run(tmp_path, PASSING_GATES, [], NON_NASA_SETTINGS, _custom_judges(4), manifest)
    cfg = resolve_report_config(inp, json.loads((out / "manifest.json").read_text(encoding="utf-8")))
    assert cfg["hackathon_name"] == "Manifest Hack" and cfg["criteria"] == ["A", "B"]
    assert cfg["max_total"] == 10 and cfg["judge_order"] == ["JX_only"] and cfg["awards"] == set()
    no_manifest = resolve_report_config(inp, {})
    assert no_manifest["max_total"] == 20 and len(no_manifest["judge_order"]) == 4
    assert resolve_report_config(tmp_path, {})["judge_order"] == hc.DEFAULT_JUDGE_ORDER


# ---------------------------------------------------------------------------
# Probe gate checks with NASA defaults keep the exact v3.0 wording
# ---------------------------------------------------------------------------
def test_probe_gate_checks_keep_v30_wording_and_honor_optional_gates(tmp_path: Path) -> None:
    nasa = hc.default_settings()["gates"]
    assert probes.check_demo_limits(tmp_path, None, nasa) == (
        "FAIL", "No demo file provided (7-slide deck or <=30 s video is mandatory)."
    )
    assert probes.check_demo_limits(tmp_path, None, {**nasa, "require_demo_file": False})[0] == "INFO"
    assert "<= 15-slide deck or video of any length" in probes.check_demo_limits(
        tmp_path, None, {**nasa, "max_video_sec": None, "max_slides": 15}
    )[1]
    assert "slide deck of any length or <=180 s video" in probes.check_demo_limits(
        tmp_path, None, {**nasa, "max_slides": None, "max_video_sec": 180.0}
    )[1]
    assert "no length limit" in probes.check_demo_limits(tmp_path, None, {**nasa, "max_slides": None,
                                                                           "max_video_sec": None})[1]
    (tmp_path / "demo.key").write_bytes(b"x")
    assert probes.check_demo_limits(tmp_path, "demo.key", nasa)[0] == "FAIL"
    assert probes.check_demo_limits(tmp_path, "demo.key", {**nasa, "require_demo_file": False})[0] == "INFO"

    nasa_text = "Built on NASA HiRISE data."
    assert probes.check_required_keywords(nasa_text, nasa["required_keywords"]) == (
        "PASS", "NASA data/mission terms found in submission text: ['hirise', 'nasa']"
    )
    assert probes.check_required_keywords("Uses the Solana SDK", ["solana", "anchor"])[0] == "PASS"
    assert probes.check_required_keywords("Uses nothing", ["solana"])[0] == "FAIL"

    assert probes.check_references(SUB_TEXT, True) == ("PASS", "A References/Sources section is present.")
    assert probes.check_references("none", True) == ("FAIL", "No References/Sources section found in submission text.")
    assert probes.check_references("none", False)[0] == "INFO"
    assert probes.check_ai_disclosure("none", True) == ("FAIL", "No AI usage disclosure found.")
    assert probes.check_ai_disclosure("none", False)[0] == "INFO"
    assert probes.check_ai_disclosure(SUB_TEXT, True)[0] == "PASS"

    assert probes.check_language("texte", None)[0] == "PASS"


def test_probe_language_gate_uses_required_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probes, "_detect_langs", lambda text: [("fr", 0.97), ("en", 0.03)])
    assert probes.check_language("x", "fr") == (
        "PASS", "Submission text language detection: [('fr', 0.97), ('en', 0.03)] (required: fr)"
    )
    assert probes.check_language("x", "en") == (
        "FAIL", "Submission text language detection: [('fr', 0.97), ('en', 0.03)]"
    )


# ---------------------------------------------------------------------------
# Host CLI: auto-detection, explicit overrides, VM bundle
# ---------------------------------------------------------------------------
def test_cli_autodetects_configs_and_uploads_them_to_vms(tmp_path: Path) -> None:
    sub = tmp_path / "my_submission"
    sub.mkdir()
    (sub / "submission.json").write_text("{}", encoding="utf-8")
    (sub / "hackathon_settings.json").write_text(json.dumps(NON_NASA_SETTINGS), encoding="utf-8")
    (sub / "hackathon_rules.md").write_text("# Rules", encoding="utf-8")
    (sub / "challenge_brief.md").write_text("# Brief", encoding="utf-8")
    (sub / "judges.json").write_text(json.dumps(_custom_judges(6)), encoding="utf-8")

    cfg = cli.resolve_run_config(sub)
    assert cfg["judge_order"] == [f"J{i}_reviewer_{i}" for i in range(1, 7)]
    assert cfg["settings"]["hackathon_name"] == "Agents Hack 2026"
    assert all(src.startswith("auto-detected") for src in cfg["sources"].values())
    bundle = cli.build_bundle(cfg, sub)
    assert bundle["/judge/input/hackathon_settings.json"] == sub / "hackathon_settings.json"
    assert bundle["/judge/input/judges.json"] == sub / "judges.json"
    assert bundle["/judge/rubric/judging_guide_2026.md"] == sub / "hackathon_rules.md"
    assert bundle["/judge/rubric/challenge_martian_map_2026.md"] == sub / "challenge_brief.md"
    vm_scripts = {f"/judge/vm/{p.name}" for p in (cli.PKG_DIR / "vm").glob("*.py") if p.name != "__init__.py"}
    assert vm_scripts <= set(bundle), vm_scripts - set(bundle)

    other = tmp_path / "panel_4.json"
    other.write_text(json.dumps(_custom_judges(4)), encoding="utf-8")
    cfg2 = cli.resolve_run_config(sub, judges_config=other)
    assert len(cfg2["judge_order"]) == 4 and cfg2["sources"]["judges"] == "--judges-config (panel_4.json)"
    assert cli.build_bundle(cfg2, sub)["/judge/input/judges.json"] == other.resolve()

    with pytest.raises(SystemExit, match="--hackathon-settings file not found"):
        cli.resolve_run_config(sub, hackathon_settings=tmp_path / "nope.json")
    (sub / "judges.json").write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit, match="Invalid hackathon configuration: judges.json"):
        cli.resolve_run_config(sub)


def test_cli_defaults_to_nasa_space_apps_without_config(tmp_path: Path) -> None:
    sub = tmp_path / "plain"
    sub.mkdir()
    cfg = cli.resolve_run_config(sub)
    assert cfg["judge_order"] == cli.JUDGE_ORDER == hc.DEFAULT_JUDGE_ORDER
    assert cfg["settings"]["is_default"] is True
    assert cfg["guide_path"] == cli.DEFAULT_JUDGING_GUIDE and cfg["challenge_path"] == cli.DEFAULT_CHALLENGE_BRIEF
    bundle = cli.build_bundle(cfg, sub)
    assert "/judge/input/judges.json" not in bundle and "/judge/input/hackathon_settings.json" not in bundle
