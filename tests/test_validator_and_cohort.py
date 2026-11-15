"""Unit tests for the 9 synthetic calibration archetypes and report.py's anti-hallucination functions."""

from __future__ import annotations

from spaceapps_judge.vm.calibration_cohort import CALIBRATION_COHORT
from spaceapps_judge.vm.report import JUDGE_ORDER, compute_calibration_for_judge, norm


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


def test_compute_calibration_for_judge_monotonic_ranking() -> None:
    fake_ballot = {
        "cohort_ranking": [
            {"cohort_id": "SYNTH_ARCH_02_TIER4_COMPLETE_PHYSICS", "rank": 1, "total_25": 24},
            {"cohort_id": "SYNTH_ARCH_01_TIER4_COMPLETE_PORTAL", "rank": 2, "total_25": 23},
            {"cohort_id": "SYNTH_ARCH_03_TIER3_3D_TERRAIN_VIEWER", "rank": 3, "total_25": 20},
            {"cohort_id": "CANDIDATE_SUBMISSION", "rank": 4, "total_25": 20, "one_line_verdict": "Strong math"},
            {"cohort_id": "SYNTH_ARCH_04_TIER3_PATH_PLANNER", "rank": 5, "total_25": 19},
            {"cohort_id": "SYNTH_ARCH_05_TIER2_ANALOG_MAPPER", "rank": 6, "total_25": 17},
            {"cohort_id": "SYNTH_ARCH_06_TIER2_TILE_VIEWER", "rank": 7, "total_25": 16},
            {"cohort_id": "SYNTH_ARCH_07_TIER1_BACKEND_NO_DEMO", "rank": 8, "total_25": 14},
            {"cohort_id": "SYNTH_ARCH_08_TIER1_CHAT_WRAPPER", "rank": 9, "total_25": 11},
            {"cohort_id": "SYNTH_ARCH_09_TIER1_BROKEN_SCAFFOLD", "rank": 10, "total_25": 7},
        ]
    }
    cal = compute_calibration_for_judge(fake_ballot)
    assert cal["calibrated"] is True
    assert cal["tau_concordance"] == 1.0
    assert cal["band_hits_of_9"] == 9
    assert cal["candidate_rank_of_10"] == 4
