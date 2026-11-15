<div align="center">

# MarsWalk — *The Map That Knows At Which Scale It Lies*

**Multi-Scale Planetary Geodesy, Plithogenic Neutrosophic Hazard Verification (`<T, I, F>`), and Obstacle-Aware Astronaut xEVA Route Planning for Jezero Crater, Mars (`18.38° N, 77.58° E`)**

[![NASA Space Apps Challenge 2026](https://img.shields.io/badge/NASA_Space_Apps_2026-Interplanetary_Survival_Guide:_Martian_Map-0B3D91?style=for-the-badge)](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-2563EB?style=for-the-badge)](LICENSE)
[![Data Contract: v1.1.0 Frozen](https://img.shields.io/badge/Data_Contract-v1.1.0_Frozen-16A34A?style=for-the-badge)](docs/contracts/10_CONTRAT_DONNEES.md)
[![Pytest & Vitest Verified](https://img.shields.io/badge/Tests-110_Pytest_%2B_22_Vitest_Passing-10B981?style=for-the-badge)](tests/)
[![Provenance: SHA-256 Sealed](https://img.shields.io/badge/Provenance-SHA--256_Sealed_Pack-D97706?style=for-the-badge)](public_packs/jezero/v1/manifest.json)

<br/>

<img src="docs/assets/jezero_eva_survival_map.svg" alt="MarsWalk Jezero Crater Western Delta Fan xEVA Survival Map Card" width="100%"/>

*Standalone print/tablet/HUD-ready xEVA Survival Map Card generated deterministically from `public_packs/jezero/v1/` (`python -m marswalk.middleware.cli generate-map-card --site jezero`).*

</div>

---

## Table of Contents

1. [Executive Summary & The Core Discovery](#1-executive-summary--the-core-discovery)
2. [How MarsWalk Answers Every Challenge Requirement](#2-how-marswalk-answers-every-challenge-requirement)
3. [Multi-Scale Hazard Verification & Plithogenic `<T, I, F>` Engine](#3-multi-scale-hazard-verification--plithogenic-t-i-f-engine)
4. [Two-Track Architecture (Static Cryptographic Pack + FastAPI)](#4-two-track-architecture-static-cryptographic-pack--fastapi)
5. [Quickstart (Frontend Web App & Python Engine)](#5-quickstart-frontend-web-app--python-engine)
6. [References & Data Sources](#6-references--data-sources)
7. [Thoughtful Use of AI (AI Usage Disclosure)](#7-thoughtful-use-of-ai-ai-usage-disclosure)

---

## 1. Executive Summary & The Core Discovery

Most planetary mapping portals treat an orbital Digital Terrain Model (DTM) as ground truth. Yet on Mars, **the hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity (EVA) lives in the scale gap** between coarse orbital pixels (`64 m` regional grids, `20 m` HRSC, `463 m` MOLA) and the `1 m–4 m` human or rover footprint on the ground.

**MarsWalk** solves the *Interplanetary Survival Guide: Martian Map* challenge by confronting multi-scale orbital terrain slopes (`1 m`, `4 m`, `16 m`, and `64 m` Horn `3×3` baselines derived from the USGS Astrogeology Mars 2020 TRN HiRISE `1 m/px` DTM) against **708 real ground-truth waypoints and measured rover tilts (`Sol 13 → Sol 2022`)** recorded by NASA's Perseverance rover across **Jezero Crater and the Western Delta Fan** (`18.38° N, 77.58° E`).

| Metric / Engineering Proof | Verified Value on Jezero Western Fan (`2 km × 2 km` Window) | Source / Verification |
| :--- | :--- | :--- |
| **Perseverance Ground-Truth Stops** | `708` total (`147` stops inside the `2×2 km` Delta Front window, `Sol 13–2022`) | `SRC-M20-WAYPOINTS` (`MEASURED`) |
| **64 m Orbital Scale Underestimation Bias** | **`-5.05°` systematic negative bias** on steep delta scarps (`> 10°`), hiding `> 20°` suit-limit walls | `validation_report.json` (`DERIVED`) |
| **Benchmark Sol 700 Scarp Trap** | Coarse `64 m` map reads **`11.2°` (`CAUTION`)**, whereas local `4 m` slope is **`22.1°` (`NO_GO` Veto)** and Perseverance measured **`20.5°` tilt** | `waypoints.geojson` / `hazard_grid.json` |
| **Even-Sol Ground-Truth Specificity** | **`97.7%` (`43 / 44` gentle even-sol Perseverance stops classified traversable)** | Disjoint Odd/Even Sol Split (`test_b2_split_and_eval.py`) |
| **xEVA Obstacle-Aware Corridor (`M2`)** | `1,669.9 m` path connecting `Sol 413 → Sol 609 → Sol 753`, max `4 m` slope **`13.3° ≤ 20.0°`**, max walkback **`1,430 m ≤ 2,000 m`** | `route.geojson` (`ROUTE-EVA-M2-OBSTACLE-AWARE`) |

---

## 2. How MarsWalk Answers Every Challenge Requirement

| NASA Challenge Prompt Dimension | MarsWalk Engineering Implementation | Where to Inspect |
| :--- | :--- | :--- |
| **>= 3 NASA / Planetary Datasets Integrated** | Integrates **5 primary datasets** (`HiRISE 1 m DTM`, `HiRISE 25 cm WMTS`, `M20 708 Waypoints & 45.2 km Traverse`, `M20 Navcam/Mastcam-Z Raw Images`, `USGS SIM 3464 Geologic Map`) + **5 peer-reviewed human/rover safety references**. | [`public_packs/jezero/v1/manifest.json`](public_packs/jezero/v1/manifest.json) |
| **Strict Provenance (`MEASURED` vs. `DERIVED` vs. `SIMULATED`)** | Every numeric `Quantity` carries a mandatory provenance tag and `source_id`. Missing orbital layers in this window (`THEMIS thermal inertia`, `CRISM mineralogical cubes`, live `MEDA` wind) are **explicitly declared out-of-pack (`0%` fabricated)** rather than hallucinated. | [`docs/contracts/10_CONTRAT_DONNEES.md`](docs/contracts/10_CONTRAT_DONNEES.md) |
| **Obstacle-Aware Routing Around Rock Formations (`>= 4 m`)** | Connected components of `>= 16 px` (`4 m × 4 m` footprint) exceeding slope/roughness limits are extracted at `1 m/px`, dilated by `0.85 m` (`0.55 m` xEVA suit half-width + `0.30 m` TRN `1σ`), and routed via 16-neighbor anisotropic `A*` (`V_MAX = 2.4 km/h` at `-5%` grade). | [`src/marswalk/engine/obstacles_m1.py`](src/marswalk/engine/obstacles_m1.py), [`planner_m2.py`](src/marswalk/engine/planner_m2.py) |
| **Suited Metabolic Power, O2 Budget & Radiation (`M3` / `M4`)** | Implements Minetti (2002) Table 1 (`MEASURED`) & quintic (`DERIVED`), Pandolf-CSRM Mars `0.3794 g` suited power (`121 kg` MKIII suit), Curiosity RAD GCR dose (`0.64 mSv/day`), and analytical finite-wall scarp-toe sky-view occlusion (`[7.0%, 9.1%]` GCR reduction, zero SPE shelter delusion). | [`src/marswalk/engine/kinematics_m4.py`](src/marswalk/engine/kinematics_m4.py), [`topographic_refuge_m3.py`](src/marswalk/engine/topographic_refuge_m3.py) |
| **UHF 414.2 MHz Comms Shadowing (`M6`)** | Evaluates 1st Fresnel zone (`F1`) and Bullington knife-edge diffraction (`ITU-R P.526`) between the `3.0 m` rover mast and `1.8 m` suit antenna over the `R = 3,396,190 m` Mars sphere. | [`src/marswalk/engine/eva_human_rf.py`](src/marswalk/engine/eva_human_rf.py) |
| **Multi-Format Output (Interactive 2D/3D Web App + Standalone Map Generator)** | Interactive React + MapLibre GL + Three.js 3D terrain inspector (`frontend/`) **plus** a deterministic vector SVG Survival Map Card generator (`docs/assets/jezero_eva_survival_map.svg`) for habitat screens, wrist tablets, or offline mission binders. | [`frontend/`](frontend/), [`src/marswalk/middleware/map_card.py`](src/marswalk/middleware/map_card.py) |

---

## 3. Multi-Scale Hazard Verification & Plithogenic `<T, I, F>` Engine

Instead of collapsing terrain risk into an opaque single number, MarsWalk evaluates every cell as a **Plithogenic Neutrosophic triplet `<T, I, F>`** (Smarandache 2017, [`docs/ENGINE_MATH.md`](docs/ENGINE_MATH.md)):

1. **Multi-Scale Concordance Funnel (`1 m / 4 m / 16 m / 64 m`)**:
   - The `1 m` stereo pixel scale is retained for raw display and `>= 4 m` boulder/scarp clustering (`M1`), while the concordance funnel evaluates `4 m`, `16 m`, and `64 m` baselines across **10 normalized terrain carriers** (slope, roughness, scale divergence, curvature, Hurst exponent `H`, rock CFA, sky-view factor, solar shadow, walkback, and Area of Applicability `AoA`).
   - **Persistent-Hazard Override (`B3`)**: if two neighboring scales (`4 m` and `16 m`) both flag a steep scarp while the `64 m` orbital baseline smooths it out, the funnel **forbids pruning the fine-scale hazard**.
2. **Non-Compensatory Lexicographic Safety Veto**:
   - No amount of high scientific value (`A6`) or prime delta geology (`A5`, `NHjf1`) can ever compensate for a physical safety limit violation:
     - `slope_4m > 20.0°` (`SRC-NASA-XEVA` suit limit) $\rightarrow$ immediate **`NO_GO` (`SAFETY VETO`)**;
     - `walkback_distance > 2,000 m` (`SRC-NASA-XEVA` walkback limit) $\rightarrow$ immediate **`NO_GO` (`SAFETY VETO`)**;
     - Active Solar Particle Event (`spe_alert = True`) $\rightarrow$ immediate **`NO_GO` (`ABORT_TO_HABITAT`)**.

---

## 4. Two-Track Architecture (Static Cryptographic Pack + FastAPI)

To guarantee zero frontend blocking and instant static deployment alongside full dynamic route planning, MarsWalk ships a **SHA-256-verified static site pack** (`< 5 MB` total) under [`public_packs/jezero/v1/`](public_packs/jezero/v1/manifest.json) paired with a FastAPI query and custom route-planning service:

```text
NASA M20 / HiRISE 1m DTM / USGS SIM 3464 Raw Data (datalake/ — gitignored)
       │
       ▼  python -m marswalk.middleware.cli build-pack --site jezero
┌──────────────────────────────────────────────────────────────────────────┐
│ public_packs/jezero/v1/  (17 Committed Files, < 5 MB, SHA-256 Verified)  │
│  ├─ manifest.json            (CRS: Mars Sphere R=3,396,190 m + SHA-256)  │
│  ├─ waypoints.geojson        (708 Perseverance stops + tilt + Navcam)    │
│  ├─ route.geojson            (MEASURED traverse + DERIVED M2 EVA route)  │
│  ├─ obstacles.geojson        (>= 4 m rock/scarp formations + 0.85m buf)  │
│  ├─ planner_grid_10m.png     (Lossless 200x190 10m routing cost/mask)    │
│  ├─ hazard_grid.json         (1600 cells: 1m/4m/16m/64m + <T,I,F> + RF)  │
│  ├─ hazard_overlay.png       (Transparent RGBA hazard heatmap overlay)   │
│  ├─ validation_report.json   (Scale-gap bias & even-sol metrics)         │
│  ├─ eva_constraints.json     (Citable NASA xEVA + JPL + RAD thresholds)  │
│  └─ panoramas/sol_*.jpg      (5 bundled NASA M20 Navcam JPEGs)           │
└──────────────┬───────────────────────────────────────────┬───────────────┘
               │ Direct static fetch() / Offline Fallback  │ Dynamic API (:8000)
               ▼                                           ▼
   [frontend/ React + MapLibre + 3D Mesh]     [FastAPI /v1/sites/jezero/plan-route]
```

---

## 5. Quickstart (Frontend Web App & Python Engine)

### A. Launch the Interactive Frontend (`frontend/`)

The frontend works out of the box against the committed static pack in `public_packs/jezero/v1/` (and automatically connects to FastAPI on `:8000` when running for live click-to-plan `A*` routing):

```bash
cd frontend
npm install
npm run dev          # Starts Vite dev server
npm test             # Runs 22 Vitest unit & integration tests
npm run build        # Production TypeScript + Vite bundle
```

### B. Run the Python Engine, Pack Verifier & Test Suite (`src/marswalk/`)

```bash
# 1. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 2. Verify cryptographic SHA-256 integrity and provenance of the Jezero v1 pack
python -m marswalk.middleware.cli verify-pack --site jezero

# 3. Generate the standalone SVG xEVA Survival Map Card
python -m marswalk.middleware.cli generate-map-card --site jezero

# 4. Run the FastAPI middleware server (CORS enabled, SAFE_MODE & FAIL_SAFE guards)
uvicorn marswalk.middleware.api:app --reload --port 8000

# 5. Run ruff and the automated test suite
ruff check src/ tests/
pytest -q --tb=short
```

---

## 6. References & Data Sources

Every `MEASURED`, `DERIVED`, and `SIMULATED` quantity in `public_packs/jezero/v1/` is cryptographically bound via `manifest.json` (`SHA-256`) to the following official NASA, JPL, USGS, and peer-reviewed planetary science sources:

1. **NASA/JPL-Caltech Mars 2020 Mission Operations MMGIS Waypoints (`SRC-M20-WAYPOINTS`, `708` stops, Sol 13–2022):** https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json
2. **NASA/JPL-Caltech Mars 2020 Mission Operations MMGIS Traverse Path (`SRC-M20-TRAVERSE`, `45.2 km`):** https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_traverse.json
3. **NASA/JPL-Caltech/ASU Mars 2020 Raw Images Archive (`SRC-M20-RAW-IMAGES`, Navcam & Mastcam-Z):** https://mars.nasa.gov/mars2020/multimedia/raw-images/
4. **NASA Solar System Treks / MRO HiRISE 25 cm/px Orthorectified Mosaic (`SRC-TREK-HIRISE-25CM`, Fergason et al. 2020):** https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars
5. **USGS Astrogeology Mars 2020 TRN HiRISE 1 m/px Digital Terrain Model Blended with MOLA (`SRC-USGS-HIRISE-DTM-1M`, Fergason et al. 2020):** https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif
6. **USGS Scientific Investigations Map 3464 — Geologic Map of Jezero Crater (`SRC-USGS-SIM3464`, Sun & Stack 2020):** https://doi.org/10.3133/sim3464
7. **NASA Extravehicular Activity (xEVA) System Concept of Operations (`SRC-NASA-XEVA`, EVA-EXP-0042 Rev B, 2020):** https://www.nasa.gov/wp-content/uploads/2017/02/eva-exp-0042_xeva_system_con_ops_rev_b_final_dtd_10192020_ref_doc.pdf
8. **JPL Mars 2020 Surface Traversability Analysis (`SRC-JPL-TRAVERSABILITY`, Ono et al. 2016, IEEE Aerospace Conference):** https://www-robotics.jpl.nasa.gov/media/documents/Data-driven%20surface%20traversability%20analysis%20for%20Mars%202020%20landing%20site%20selection.pdf
9. **MSL Curiosity Radiation Assessment Detector (`SRC-RAD-GALE`, Hassler et al. 2014, *Science* 343(6169), 1244797, 0.64 mSv/day GCR baseline):** https://doi.org/10.1126/science.1244797 (Open summary: https://www.swri.org/newsroom/press-releases/swri-scientists-publish-first-radiation-measurements-the-surface-of-mars)
10. **Apollo EVA Slope & Elevation Envelope (`SRC-APOLLO-SLOPE`, Iqbal et al. 2024, *Acta Astronautica* 223, 184–196):** https://doi.org/10.1016/j.actaastro.2024.07.006

---

## 7. Thoughtful Use of AI (AI Usage Disclosure)

This project was engineered through an iterative, human-directed collaboration between **Jean-Sébastien Beaulieu** (Engine, Plithogenic Math, Geodesy & Middleware Lead) and **Philippe Pierre** (Frontend Cartography, 3D Terrain & UX Lead), using AI coding assistants (Claude Code, Google Gemini / Antigravity, and OpenAI Codex) strictly as verification, code-generation, and hostile-audit instruments under human architectural authority. All scientific equations, physical thresholds, dataset choices, and safety vetoes were defined, cross-checked against primary NASA/USGS data, and verified by deterministic automated test suites (`pytest` + `vitest`) by the human authors. See [`docs/AI_USAGE.md`](docs/AI_USAGE.md) and [`HUMAN.md`](HUMAN.md) for the complete module-by-module AI disclosure and licence attribution ([`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)).
