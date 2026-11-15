"""Anti-hallucination validator + 3-Tier Calibrated Final Report. Pure Python, no LLM.

Can run inside the E2B VM (/judge) or on the host report directory passed as sys.argv[1].
Also importable as a library (`from spaceapps_judge.vm.report import norm, compute_calibration_for_judge`)
without side effects.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibration_cohort import CALIBRATION_COHORT  # noqa: E402

CRITERIA = ["Impact", "Creativity", "Validity", "Relevance", "Presentation"]
AWARDS = {
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
}
JUDGE_ORDER = [
    "J1_local_ux_ai_reviewer",
    "J2_local_geomatics_data_reviewer",
    "J3_global_planetary_cartography_sme",
    "J4_global_geodesy_ivv_sme",
    "J5_exec_mission_directorate_reviewer",
]

BM_TIER_MAP = {b["cohort_id"]: b["ground_truth_tier"] for b in CALIBRATION_COHORT}
BM_BAND_MAP = {b["cohort_id"]: b["expected_score_band"] for b in CALIBRATION_COHORT}


def norm(s: str) -> str:
    """Normalize punctuation, markdown markers, and Unicode arrows/operators for verbatim substring checks."""
    s = (
        s.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("—", "-")
        .replace("–", "-")
        .replace("→", "->")
        .replace("≥", ">=")
        .replace("≤", "<=")
        .replace("×", "x")
    )
    s = re.sub(r"[*_`#\[\]\"']+", " ", s)
    s = re.sub(r"\s*([(),:;])\s*", r" \1 ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def compute_calibration_for_judge(data: dict) -> dict:
    """Evaluate Kendall-style monotonic concordance across the 9 synthetic calibration archetypes."""
    ranking = data.get("cohort_ranking") or []
    if not isinstance(ranking, list) or not ranking:
        return {"calibrated": False, "reason": "no cohort_ranking returned"}
    by_id = {
        r.get("cohort_id"): r
        for r in ranking
        if isinstance(r, dict) and r.get("cohort_id")
    }
    bm_scores: list[tuple[int, float]] = []
    band_hits = 0
    for cid, tier_gt in BM_TIER_MAP.items():
        if cid in by_id and isinstance(by_id[cid].get("total_25"), (int, float)):
            sc25 = float(by_id[cid]["total_25"])
            bm_scores.append((tier_gt, sc25))
            lo, hi = BM_BAND_MAP[cid]
            if (lo - 2) <= sc25 <= (hi + 2):
                band_hits += 1
    concordant, discordant = 0, 0
    for i in range(len(bm_scores)):
        for j_idx in range(i + 1, len(bm_scores)):
            t1, s1 = bm_scores[i]
            t2, s2 = bm_scores[j_idx]
            if t1 == t2:
                continue
            if (t1 > t2 and s1 >= s2) or (t1 < t2 and s1 <= s2):
                concordant += 1
            else:
                discordant += 1
    total_pairs = concordant + discordant
    tau_concordance = (
        round((concordant - discordant) / total_pairs, 3) if total_pairs else 0.0
    )
    cand = by_id.get("CANDIDATE_SUBMISSION", {})
    return {
        "calibrated": len(bm_scores) >= 7 and tau_concordance >= 0.60,
        "tau_concordance": tau_concordance,
        "benchmarks_scored": len(bm_scores),
        "band_hits_of_9": band_hits,
        "candidate_rank_of_10": cand.get("rank"),
        "candidate_cohort_score_25": cand.get("total_25"),
        "candidate_one_line": cand.get("one_line_verdict", ""),
    }


def run_report(out_dir: Path, inp_dir: Path) -> int:
    sub = json.loads((inp_dir / "submission.json").read_text(encoding="utf-8"))
    sub_text = (
        (inp_dir / sub["submission_text_file"]).read_text(encoding="utf-8", errors="replace")
        if sub.get("submission_text_file") and (inp_dir / sub["submission_text_file"]).exists()
        else ""
    )
    evidence = json.loads((out_dir / "evidence.json").read_text(encoding="utf-8"))
    raw_panel = json.loads((out_dir / "panel_raw.json").read_text(encoding="utf-8"))
    if isinstance(raw_panel, list):
        panel: dict[str, dict] = {
            item["judge"]: item
            for item in raw_panel
            if isinstance(item, dict) and item.get("judge")
        }
    elif isinstance(raw_panel, dict):
        panel = raw_panel
    else:
        panel = {}

    manifest = (
        json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        if (out_dir / "manifest.json").exists()
        else {}
    )
    ids = {e["id"] for e in evidence} | {"SUB"}
    corpus = norm(
        f"{sub.get('project_title', '')}\n{sub.get('challenge', '')}\n{sub_text}\n"
        + "\n".join(
            f"{e['id']} {e['probe']} {e['status']} {e['fact']}\n{e['excerpt']}"
            for e in evidence
        )
    )

    def check_ids(id_obj: object) -> list[str]:
        id_list = id_obj if isinstance(id_obj, list) else []
        return [i for i in id_list if i not in ids]

    rejections: list[str] = []
    valid_scores: dict[str, list[tuple[str, int, dict]]] = {c: [] for c in CRITERIA}
    judges_ok: list[str] = []
    for jid, data in panel.items():
        if not isinstance(data, dict) or "_error" in data:
            rejections.append(f"{jid}: judge call FAILED entirely (no output) -> excluded.")
            continue
        judges_ok.append(jid)
        seen: set[str] = set()
        for s in data.get("scores", []):
            c = s.get("criterion")
            why: list[str] = []
            if c not in CRITERIA:
                why.append(f"unknown criterion {c!r}")
            if c in seen:
                why.append("duplicate criterion")
            sc = s.get("score")
            if not isinstance(sc, int) or not 1 <= sc <= 5:
                why.append(f"score {sc!r} not an int 1-5")
            bad = check_ids(s.get("evidence_ids"))
            if not s.get("evidence_ids"):
                why.append("no evidence id cited")
            if bad:
                why.append(f"unknown evidence ids {bad}")
            quotes = s.get("quotes") or []
            if not quotes:
                why.append("no verbatim quote")
            for q in quotes:
                if len(norm(str(q))) < 10 or norm(str(q)) not in corpus:
                    why.append(f"quote not found verbatim: {str(q)[:90]!r}")
            if why:
                rejections.append(f"{jid} / {c}: REJECTED ({'; '.join(why)})")
            else:
                seen.add(c)
                valid_scores[c].append((jid, sc, s))
        w_list = data.get("weaknesses") or []
        if len(w_list) < 3:
            rejections.append(
                f"{jid} / severity_check: WARN (only {len(w_list)} weaknesses listed; v3.0 mandates >=3)"
            )
        for c in CRITERIA:
            if c not in seen and not any(r.startswith(f"{jid} / {c}") for r in rejections):
                rejections.append(f"{jid} / {c}: MISSING from judge output")

    calibration_by_judge = {j: compute_calibration_for_judge(panel[j]) for j in judges_ok}
    cand_ranks = [
        c["candidate_rank_of_10"]
        for c in calibration_by_judge.values()
        if isinstance(c.get("candidate_rank_of_10"), int)
    ]
    median_rank_10 = statistics.median(cand_ranks) if cand_ranks else None

    final: dict[str, dict] = {}
    for c in CRITERIA:
        vals = [v for _, v, _ in valid_scores[c]]
        med = statistics.median(vals) if vals else None
        mn = round(statistics.mean(vals), 2) if vals else None
        final[c] = {
            "median": med,
            "median_pct": round((med / 5.0) * 100.0, 1) if med is not None else None,
            "mean": mn,
            "mean_pct": round((mn / 5.0) * 100.0, 1) if mn is not None else None,
            "n": len(vals),
            "spread": (max(vals) - min(vals)) if vals else None,
            "by_judge": {j: v for j, v, _ in valid_scores[c]},
            "by_judge_pct": {j: round((v / 5.0) * 100.0, 1) for j, v, _ in valid_scores[c]},
        }
    total = sum(v["median"] for v in final.values() if v["median"] is not None)
    total_pct = round((total / 25.0) * 100.0, 1)
    total_mean = round(sum(v["mean"] for v in final.values() if v["mean"] is not None), 2)
    total_mean_pct = round((total_mean / 25.0) * 100.0, 1)

    ordered_judges = [j for j in JUDGE_ORDER if j in panel] + [
        j for j in panel if j not in JUDGE_ORDER
    ]
    judge_totals: dict[str, dict] = {}
    for j in ordered_judges:
        j_scores = {
            c: final[c]["by_judge"].get(j) for c in CRITERIA if j in final[c]["by_judge"]
        }
        if j_scores:
            j_sum = sum(j_scores.values())
            j_max = 5 * len(j_scores)
            judge_totals[j] = {
                "raw_total": j_sum,
                "max_possible": j_max,
                "pct_100": round((j_sum / j_max) * 100.0, 1),
                "criteria_pct": {
                    c: round((sc / 5.0) * 100.0, 1) for c, sc in j_scores.items()
                },
            }
    gate = [e for e in evidence if e["id"].startswith("G")]
    gate_fail = [e for e in gate if e["status"] == "FAIL"]
    votes = {j: bool(panel[j].get("nominate_global")) for j in judges_ok}
    omb_survey = {
        j: {
            "adds_professional_value": panel[j].get("adds_professional_value"),
            "rationale": panel[j].get("adds_professional_value_rationale", ""),
        }
        for j in judges_ok
        if panel[j].get("adds_professional_value") is not None
    }

    award_tally: dict[str, list[str]] = {}
    for j in judges_ok:
        for a in panel[j].get("award_fit", []) or []:
            if a.get("award") in AWARDS and not check_ids(a.get("evidence_ids")):
                award_tally.setdefault(a["award"], []).append(j)
            else:
                rejections.append(f"{j} / award_fit: rejected item {a.get('award')!r}")

    fixes: list[dict] = []
    for j in judges_ok:
        for f in panel[j].get("fixes_before_deadline", []) or []:
            if not check_ids(f.get("evidence_ids")) and f.get("criterion") in CRITERIA:
                fixes.append({**f, "judge": j})
    fixes.sort(
        key=lambda f: (
            -(f.get("expected_gain") or 0) / max(f.get("effort_minutes") or 60, 5)
        )
    )

    j_pcts = [v["pct_100"] for v in judge_totals.values()]
    pct_stdev = round(statistics.stdev(j_pcts), 1) if len(j_pcts) >= 2 else 0.0
    pct_ci95 = (
        round(1.96 * pct_stdev / math.sqrt(len(j_pcts)), 1) if len(j_pcts) >= 2 else 0.0
    )
    shrunk_pct = round(0.80 * total_mean_pct + 0.20 * 60.0, 1)
    if gate_fail:
        est_finalist_prob_pct = 0.0
        est_local_nominee_if_gates_fixed_pct = round(
            min(95.0, max(5.0, (total_mean_pct - 55.0) * 2.2)), 1
        )
    else:
        est_finalist_prob_pct = round(min(95.0, max(5.0, (total_mean_pct - 60.0) * 2.2)), 1)
        est_local_nominee_if_gates_fixed_pct = est_finalist_prob_pct

    lines: list[str] = []
    lines.append(
        f"# Rapport de jugement v3.0 (Calibré sur Cohorte 10 Projets & 5 MicroVMs E2B) — {sub.get('project_title', '?')}"
    )
    lines.append(
        f"*Panel multi-modèles de 5 juges isolés E2B · {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} "
        f"· défi : {sub.get('challenge')}*\n"
    )
    status = (
        "NON ADMISSIBLE au jugement mondial (portes obligatoires en échec)"
        if gate_fail
        else "ADMISSIBLE (contrôles automatiques)"
    )
    lines.append(f"## Verdict & Probabilité Calibrée\n- **Admissibilité : {status}**")
    lines.append(
        f"- **Score Panel Brut (Intervalle 95%) : `{total_mean_pct:.1f}% ± {pct_ci95:.1f}%`** "
        f"(Médiane : **{total:g} / 25 = `{total_pct:.1f}%`**, Moyenne : **{total_mean:g} / 25**, Écart-type inter-juges : `{pct_stdev:.1f}%`)"
    )
    lines.append(
        f"- **Score Corrigé Anti-Complaisance ( Ancrage historique Space Apps 3.0/5 ) : `{shrunk_pct:.1f}% / 100%`**"
    )
    if median_rank_10 is not None:
        rank_by_j = ", ".join(
            f"`{j}`=#{calibration_by_judge[j].get('candidate_rank_of_10', '?')}"
            for j in ordered_judges
            if j in calibration_by_judge
        )
        lines.append(
            f"- **Classement à l'Aveugle dans la Cohorte de 10 Projets (`SYNTH_ARCH_01..09` + Candidat) : Rang Médian `#{median_rank_10:g} / 10`** "
            f"(rangs par juge : {rank_by_j})"
        )
    lines.append(
        f"- **Probabilité Estimée de Nomination / Prix Mondial (état actuel) : `{est_finalist_prob_pct:.1f}%`** "
        f"*(Potentiel si portes `G-01`/`G-02`/`G-04` résolues avant 23h59 : **`~{est_local_nominee_if_gates_fixed_pct:.1f}%`**)*"
    )
    lines.append(
        "- **Vote de nomination mondiale :** "
        + ", ".join(f"`{j}` = {'OUI' if v else 'NON'}" for j, v in votes.items())
    )
    if omb_survey:
        omb_str = ", ".join(
            f"`{j}` = {'OUI' if v['adds_professional_value'] else 'NON'}"
            for j, v in omb_survey.items()
        )
        lines.append(
            f"- **Sondage officiel SME (`adds_professional_value`) :** {omb_str}"
        )
    if any(panel[j].get("_model") != manifest.get("model") for j in judges_ok):
        lines.append("- ⚠️ Au moins un juge a utilisé un modèle distinct ou de repli (voir manifeste).")
    lines.append("")
    lines.append(
        "## Contrôle d'admissibilité (déterministe, sans LLM)\n| ID | Contrôle | Statut | Fait vérifié |\n|---|---|---|---|"
    )
    for e in gate:
        st_icon = (
            "❌ FAIL"
            if e["status"] == "FAIL"
            else ("✅ PASS" if e["status"] == "PASS" else "ℹ️ INFO")
        )
        lines.append(
            f"| {e['id']} | {e['probe']} | {st_icon} | {e['fact'].replace('|', '/')} |"
        )

    cols_header = " | ".join(ordered_judges)
    cols_sep = "|".join(["---"] * (len(ordered_judges) + 6))
    lines.append(
        f"\n## Notes par critère (échelle officielle 1–5 & conversion sur 100%)\n"
        f"| Critère | Médiane (/5) | Médiane (%) | Moyenne (/5) | Moyenne (%) | {cols_header} | Écart |\n|{cols_sep}|"
    )
    for c in CRITERIA:
        f = final[c]
        bj = f["by_judge"]
        flag = " ⚠️ désaccord" if (f["spread"] or 0) >= 2 else ""
        j_cells = " | ".join(
            f"{bj[j]}/5 ({int(bj[j] * 20)}%)" if j in bj else "—" for j in ordered_judges
        )
        med_s = f"**{f['median']:g}/5**" if f["median"] is not None else "non noté"
        med_p = f"**{f['median_pct']:.1f}%**" if f["median_pct"] is not None else "—"
        mn_s = f"{f['mean']:g}/5" if f["mean"] is not None else "—"
        mn_p = f"**{f['mean_pct']:.1f}%**" if f["mean_pct"] is not None else "—"
        lines.append(
            f"| **{c}** | {med_s} | {med_p} | {mn_s} | {mn_p} | {j_cells} "
            f"| {f['spread'] if f['spread'] is not None else '—'}{flag} |"
        )
    j_tot_cells = " | ".join(
        f"**{judge_totals[j]['raw_total']}/{judge_totals[j]['max_possible']} ({judge_totals[j]['pct_100']:.1f}%)**"
        if j in judge_totals
        else "—"
        for j in ordered_judges
    )
    lines.append(
        f"| **TOTAL GLOBAL** | **{total:g}/25** | **{total_pct:.1f}%** | **{total_mean:g}/25** "
        f"| **{total_mean_pct:.1f}%** | {j_tot_cells} | — |"
    )
    lines.append("")
    for c in CRITERIA:
        lines.append(f"### {c}")
        for j, v, s in valid_scores[c]:
            lines.append(
                f"- **`{j}` → {v}/5** — {s.get('justification', '').strip()}  \n"
                f"  Preuves : {', '.join(s.get('evidence_ids', []))} · Citation vérifiée : « {s['quotes'][0]} »"
            )
        lines.append("")
    lines.append("## Corrections avant la date limite (classées gain / effort)")
    for f in fixes[:15]:
        lines.append(
            f"- **[{f['criterion']} +{f.get('expected_gain')} · ~{f.get('effort_minutes')} min]** "
            f"{f['action']} *(→ `{f['judge']}`, preuves {', '.join(f.get('evidence_ids', []))})*"
        )
    lines.append("\n## Faiblesses relevées")
    for j in judges_ok:
        for w in panel[j].get("weaknesses", []) or []:
            if not check_ids(w.get("evidence_ids")):
                lines.append(f"- [{w.get('criterion', '?')}] {w.get('text')} *(`{j}`)*")
    lines.append("\n## Forces relevées")
    for j in judges_ok:
        for w in panel[j].get("strengths", []) or []:
            if not check_ids(w.get("evidence_ids")):
                lines.append(f"- {w.get('text')} *(`{j}`)*")
    lines.append("\n## Prix mondiaux visables (sur les 10 officiels)")
    for a, js in sorted(award_tally.items(), key=lambda x: -len(x[1])):
        lines.append(f"- **{a}** — cité par {len(js)} juge(s) : {', '.join(js)}")
    lines.append(
        "\n## Calibration & Classement à l'Aveugle sur Cohorte de 10 Projets (`SYNTH_ARCH_01..09`)"
    )
    lines.append(
        "| Juge | Modèle utilisé | Concordance (`tau`) | Bandes de référence respectées (`/9`) | Rang du Candidat (`/10`) | Score Cohorte Candidat (`/25`) | Verdict comparatif |\n|---|---|---|---|---|---|---|"
    )
    for j in ordered_judges:
        if j in calibration_by_judge:
            cal = calibration_by_judge[j]
            m_used = panel[j].get("_model", "?")
            cal_icon = "✅ CALIBRÉ" if cal.get("calibrated") else "⚠️ PARTIEL"
            lines.append(
                f"| `{j}` | `{m_used}` | {cal_icon} (`{cal.get('tau_concordance', 0):.2f}`) "
                f"| `{cal.get('band_hits_of_9', 0)}/9` | **`#{cal.get('candidate_rank_of_10', '—')}/10`** "
                f"| `{cal.get('candidate_cohort_score_25', '—')}/25` | {str(cal.get('candidate_one_line', '')).replace('|', '/')} |"
            )

    lines.append(
        "\n## Parole aux Juges : Ce que j'ai jugé, Pourquoi, Comment faire basculer mon vote & Ce qu'il faut sanctuariser (`judge_debrief`)"
    )
    for j in ordered_judges:
        if j not in judges_ok:
            continue
        deb = panel[j].get("judge_debrief")
        tp = panel[j].get("time_pressure_audit") or {}
        m_used = panel[j].get("_model", "?")
        jt = judge_totals.get(j, {})
        lines.append(
            f"### 🎙️ `{j}` (Modèle `{m_used}` · Score `{jt.get('raw_total', '?')}/25 = {jt.get('pct_100', '?')}%` · Budget simulé `{tp.get('simulated_review_sec', '?')}s / {tp.get('time_limit_sec', '?')}s`)"
        )
        if tp.get("thirty_second_impression"):
            lines.append(
                f"- **Impression à 30 secondes :** *« {tp.get('thirty_second_impression')} »*"
            )
        if isinstance(deb, dict) and deb:
            lines.append(
                f"- **1. Ce que j'ai jugé et comment :** {deb.get('what_i_judged_and_how', '—')}"
            )
            lines.append(
                f"- **2. Pourquoi j'ai mis cette note :** {deb.get('why_this_score', '—')}"
            )
            lines.append(
                f"- **3. Ce qu'il faut améliorer pour faire basculer mon jugement :** {deb.get('what_would_change_my_verdict', '—')}"
            )
            lines.append(
                f"- **4. Le positif qui m'a marqué :** {deb.get('positive_highlights', '—')}"
            )
            sacred = deb.get("must_keep_sacred") or []
            if isinstance(sacred, list) and sacred:
                lines.append(
                    "- **5. À GARDER ABSOLUMENT (Sanctuarisé / Touche pas à ça) :**\n"
                    + "\n".join(f"  - 🔒 {item}" for item in sacred)
                )
            elif sacred:
                lines.append(f"- **5. À GARDER ABSOLUMENT :** 🔒 {sacred}")
        else:
            lines.append(f"- **Synthèse :** {panel[j].get('nominate_rationale', '—')}")
        lines.append("")

    lines.append(
        "\n## Justification des votes de nomination & valeur professionnelle (`adds_professional_value`)"
    )
    for j in judges_ok:
        omb_txt = ""
        if j in omb_survey:
            omb_txt = (
                f" · **`adds_professional_value`={omb_survey[j]['adds_professional_value']}** : "
                f"{omb_survey[j]['rationale']}"
            )
        tp = panel[j].get("time_pressure_audit")
        tp_txt = ""
        if isinstance(tp, dict):
            tp_txt = (
                f" · ⏱️ **Budget `{tp.get('simulated_review_sec', '?')}s / {tp.get('time_limit_sec', '?')}s`** "
                f"(30s : *« {tp.get('thirty_second_impression', '')} »*)"
            )
        lines.append(
            f"- **`{j}`** : {panel[j].get('nominate_rationale', '')}{omb_txt}{tp_txt}"
        )
    lines.append("\n## Rejets du validateur anti-hallucination")
    lines.append(
        "\n".join(f"- {r}" for r in rejections)
        if rejections
        else "- Aucun : toutes les notes citent des preuves existantes et des citations exactes."
    )
    lines.append("\n## Registre de preuves (sondes déterministes)")
    for e in evidence:
        if e["id"].startswith("E"):
            lines.append(
                f"- **{e['id']}** `{e['probe']}` ({e.get('tier', 'ALL')}) {e['status']} — {e['fact']}"
            )
    lines.append(
        "\n## Scellement (reproductibilité)\n```json\n"
        + json.dumps(manifest, indent=1)
        + "\n```"
    )
    lines.append(
        "\n*Limites : seuls les descripteurs « Score of 5 » sont officiels ; les ancres 1–4 et les 9 archétypes "
        "`SYNTH_ARCH_01..09` sont des profils synthétiques de calibration. Ce rapport est traçable aux preuves "
        "empiriques de la Vague 1, pas une prédiction garantie du jury.*"
    )

    report = "\n".join(lines)
    (out_dir / "JUDGEMENT_REPORT.md").write_text(report, encoding="utf-8")
    (out_dir / "judgement.json").write_text(
        json.dumps(
            {
                "total": total,
                "total_pct_100": total_pct,
                "total_mean": total_mean,
                "total_mean_pct_100": total_mean_pct,
                "pct_ci95": pct_ci95,
                "pct_stdev": pct_stdev,
                "shrunk_pct_100": shrunk_pct,
                "median_rank_of_10": median_rank_10,
                "est_finalist_prob_pct": est_finalist_prob_pct,
                "est_local_nominee_if_gates_fixed_pct": est_local_nominee_if_gates_fixed_pct,
                "calibration_by_judge": calibration_by_judge,
                "judge_totals": judge_totals,
                "criteria": final,
                "eligible": not gate_fail,
                "gate_failures": [e["id"] for e in gate_fail],
                "nomination_votes": votes,
                "omb_2700_0153_survey": omb_survey,
                "awards": award_tally,
                "rejections": rejections,
                "report_sha256": hashlib.sha256(report.encode()).hexdigest(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"REPORT DONE: median={total:g}/25 ({total_pct:.1f}%), mean={total_mean:g}/25 ({total_mean_pct:.1f}%), "
        f"eligible={not gate_fail}, rejections={len(rejections)}"
    )
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        out_dir = Path(sys.argv[1]).resolve()
        inp_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else out_dir
    else:
        root = Path("/judge")
        out_dir = root / "out"
        inp_dir = root / "input"
    return run_report(out_dir, inp_dir)


if __name__ == "__main__":
    raise SystemExit(main())
