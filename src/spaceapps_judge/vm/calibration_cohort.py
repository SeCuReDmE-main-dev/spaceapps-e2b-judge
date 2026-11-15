"""Synthetic Calibration Archetypes (`SYNTH_ARCH_01..09`) for Blind Cohort Ranking.

To prevent absolute-score inflation without naming real teams or individuals, every judge
ranks and scores a shuffled 10-project cohort consisting of 9 synthetic reference archetypes
across 4 defined quality tiers plus the candidate submission:
  - Tier 4 (`SYNTH_TIER4_EXEMPLARY`, top ~1% reference): expected 22-24 / 25
  - Tier 3 (`SYNTH_TIER3_FINALIST`, top ~5% reference): expected 19-21 / 25
  - Tier 2 (`SYNTH_TIER2_NOMINEE`, top ~15% reference): expected 15-18 / 25
  - Tier 1 (`SYNTH_TIER1_INCOMPLETE`, incomplete or missing gates): expected 5-16 / 25
"""

from __future__ import annotations

CALIBRATION_COHORT: list[dict] = [
    {
        "cohort_id": "SYNTH_ARCH_01_TIER4_COMPLETE_PORTAL",
        "ground_truth_tier": 4,
        "ground_truth_label": "SYNTH_TIER4_EXEMPLARY (Complete Multi-Layer Portal)",
        "expected_score_band": [22, 24],
        "title": "Synthetic Archetype 01 — Complete Multi-Layer Planetary Portal (All Gates PASS)",
        "summary_300w": (
            "Synthetic reference archetype representing a complete top-tier submission. Live web application "
            "deployed on a public URL with a compliant 7-slide deck and 30-second video demo. Integrates NASA "
            "Mars Trek WMTS tiles, MOLA global altimetry, CTX 5 m mosaics, and rover traverse logs into an "
            "accessible planetary exploration planner. Strengths: zero-friction live web UX, all mandatory "
            "submission gates passing, clear storytelling for non-specialists, and multi-dataset NASA WMTS "
            "integration. Limitations: uses regional MOLA/CTX elevation profiles without meter-scale stereo "
            "slope validation or suited metabolic/RF diffraction physics."
        ),
        "gates_status": "ALL PASS (PUBLIC_URL=PASS, 7_SLIDE_DEMO=PASS, REPO_PUBLIC=PASS, CITATIONS=PASS)",
    },
    {
        "cohort_id": "SYNTH_ARCH_02_TIER4_COMPLETE_PHYSICS",
        "ground_truth_tier": 4,
        "ground_truth_label": "SYNTH_TIER4_EXEMPLARY (Complete Physics & Live Demo)",
        "expected_score_band": [22, 25],
        "title": "Synthetic Archetype 02 — Validated Radiation & Habitat Physics Planner (All Gates PASS)",
        "summary_300w": (
            "Synthetic reference archetype representing a scientifically rigorous entry with full deliverables. "
            "Live hosted 3D web application with 30-second video demo and passing pytest suite. Models Martian "
            "surface radiation shielding using MSL Curiosity RAD GCR baselines (0.64 mSv/day), MOLA sky-view "
            "topographic occlusion inside lava tubes and crater rims, and regolith mass-thickness attenuation "
            "curves. Validated against published PDS RAD measurements with unit tests and interactive dose-budget "
            "sliders. Strengths: complete submission gates, live app, and peer-reviewed physical validation. "
            "Limitations: coarse 463 m MOLA resolution; does not resolve meter-scale boulder obstacles."
        ),
        "gates_status": "ALL PASS (PUBLIC_URL=PASS, 30S_VIDEO=PASS, REPO_PUBLIC=PASS, PYTEST=PASS)",
    },
    {
        "cohort_id": "SYNTH_ARCH_03_TIER3_3D_TERRAIN_VIEWER",
        "ground_truth_tier": 3,
        "ground_truth_label": "SYNTH_TIER3_FINALIST (Strong 3D Visuals, Geometric Only)",
        "expected_score_band": [19, 21],
        "title": "Synthetic Archetype 03 — WebXR 3D Terrain Mesh Inspector (All Gates PASS)",
        "summary_300w": (
            "Synthetic finalist archetype: browser-based Three.js / WebXR 3D terrain visualizer streaming USGS "
            "HiRISE DTM meshes and orthophotos for Jezero Crater with a working public URL and 7-slide pitch deck. "
            "Allows users to drop pins and view straight-line elevation profiles. Strengths: polished 3D visual "
            "presentation, responsive mobile/desktop UI, and working live demo link. Limitations: purely geometric "
            "single-scale visualization; straight-line connector ignores steep scarps, boulder fields, astronaut "
            "metabolic O2 limits, and comms line-of-sight; no automated test suite."
        ),
        "gates_status": "ALL PASS (PUBLIC_URL=PASS, 7_SLIDE_DEMO=PASS, REPO_PUBLIC=PASS, PYTEST=NONE)",
    },
    {
        "cohort_id": "SYNTH_ARCH_04_TIER3_PATH_PLANNER",
        "ground_truth_tier": 3,
        "ground_truth_label": "SYNTH_TIER3_FINALIST (Single-Scale A* Planner)",
        "expected_score_band": [19, 21],
        "title": "Synthetic Archetype 04 — Single-Scale Grid A* Traverse Planner (All Gates PASS)",
        "summary_300w": (
            "Synthetic finalist archetype: Python + Streamlit web application with 30-second demo video and "
            "hosted link. Implements 8-neighbor A* pathfinding over a single-resolution 20 m HRSC/CTX slope raster "
            "in Gale Crater, combining slope penalty and distance into a linear weighted sum with basic human O2 "
            "consumption estimates. Strengths: functional live dashboard, clear slide deck, and working A* "
            "pathfinder. Limitations: compensatory linear weighted sum allows high science weight to route "
            "astronauts across >22 deg lethal slopes; evaluates only a single coarse raster resolution."
        ),
        "gates_status": "ALL PASS (PUBLIC_URL=PASS, 30S_VIDEO=PASS, REPO_PUBLIC=PASS, PYTEST=12_PASSED)",
    },
    {
        "cohort_id": "SYNTH_ARCH_05_TIER2_ANALOG_MAPPER",
        "ground_truth_tier": 2,
        "ground_truth_label": "SYNTH_TIER2_NOMINEE (Creative Concept, Partial Scope)",
        "expected_score_band": [16, 18],
        "title": "Synthetic Archetype 05 — Terrestrial-to-Planetary Analog Comparison App (All Gates PASS)",
        "summary_300w": (
            "Synthetic local-nominee archetype: deployed web app comparing terrestrial desert/volcanic analog "
            "terrains with Martian orbital layers using satellite imagery and a clean frontend UI. Strengths: "
            "live deployed domain, polished visual layout, and creative educational framing. Limitations: focuses "
            "on visual Earth-Mars analogy rather than quantitative astronaut EVA survival constraints (no suited "
            "metabolic model, no multi-scale slope bias verification, no rover ground-truth tilt validation)."
        ),
        "gates_status": "ALL PASS (PUBLIC_URL=PASS, DEMO=PASS, REPO_PUBLIC=PASS)",
    },
    {
        "cohort_id": "SYNTH_ARCH_06_TIER2_TILE_VIEWER",
        "ground_truth_tier": 2,
        "ground_truth_label": "SYNTH_TIER2_NOMINEE (Standard Tile Overlay)",
        "expected_score_band": [15, 17],
        "title": "Synthetic Archetype 06 — 2D Leaflet WMTS Tile Viewer with Static Markers",
        "summary_300w": (
            "Synthetic local-nominee archetype: React + Leaflet 2D map displaying NASA Mars Trek MOLA colorized "
            "elevation tiles and 15 hardcoded JSON pins for famous Martian landmarks, accompanied by a 7-slide PDF "
            "and Netlify link. Strengths: clean UI, complete submission fields, and working WMTS tile loading. "
            "Limitations: zero custom terrain processing or mathematical modeling; all hazard ratings are manually "
            "typed strings in a static JSON file."
        ),
        "gates_status": "ALL PASS (PUBLIC_URL=PASS, 7_SLIDE_DEMO=PASS, REPO_PUBLIC=PASS)",
    },
    {
        "cohort_id": "SYNTH_ARCH_07_TIER1_BACKEND_NO_DEMO",
        "ground_truth_tier": 1,
        "ground_truth_label": "SYNTH_TIER1_INCOMPLETE (Strong Code, Missing Demo & URL Gates)",
        "expected_score_band": [12, 16],
        "title": "Synthetic Archetype 07 — Strong Geodesic Solver Without Demo or Public URL",
        "summary_300w": (
            "Synthetic incomplete-gate archetype: C++ and Python command-line repository computing geodesic slope "
            "and solar incidence angles on HiRISE DTMs with 84 passing unit tests and thorough mathematical "
            "documentation in the README. However, the team did not deploy a public web URL (G-01/G-02 FAIL) and "
            "did not upload a 7-slide deck or 30-second video demo (G-04 FAIL). Under official Space Apps rules, "
            "missing demo and live URL deliverables cap Presentation at <=2/5 and block Global Nomination."
        ),
        "gates_status": "GATE FAIL (PUBLIC_URL=FAIL, DEMO_FILE=FAIL, REPO_PUBLIC=PASS, PYTEST=84_PASSED)",
    },
    {
        "cohort_id": "SYNTH_ARCH_08_TIER1_CHAT_WRAPPER",
        "ground_truth_tier": 1,
        "ground_truth_label": "SYNTH_TIER1_INCOMPLETE (Prompt Wrapper Over Static Image)",
        "expected_score_band": [9, 13],
        "title": "Synthetic Archetype 08 — Generic LLM Chatbot Over Static Mars Background",
        "summary_300w": (
            "Synthetic low-validity archetype: Next.js page wrapping a single LLM chat prompt ('You are a Mars "
            "survival guide') next to a static JPEG of Mars. When asked for a route, the chatbot invents "
            "fictional coordinates and oxygen numbers with zero connection to real NASA datasets. No data pipeline, "
            "no unit tests, and broken external citation links in the README."
        ),
        "gates_status": "PARTIAL (PUBLIC_URL=PASS, 7_SLIDE_DEMO=PASS, NASA_DATA_PROCESSED=NONE)",
    },
    {
        "cohort_id": "SYNTH_ARCH_09_TIER1_BROKEN_SCAFFOLD",
        "ground_truth_tier": 1,
        "ground_truth_label": "SYNTH_TIER1_INCOMPLETE (Unfinished Scaffold)",
        "expected_score_band": [5, 9],
        "title": "Synthetic Archetype 09 — Unfinished Template Scaffold with Placeholder Mockups",
        "summary_300w": (
            "Synthetic baseline archetype: default Vite template containing 3 static UI screenshots in the README "
            "and an unimplemented Python stub (`pass`). `npm run build` fails with missing imports, no public URL "
            "is provided, no demo video or slide deck is attached, and no NASA datasets are loaded."
        ),
        "gates_status": "FAIL (PUBLIC_URL=FAIL, DEMO_FILE=FAIL, FRONTEND_BUILD=FAIL)",
    },
]
