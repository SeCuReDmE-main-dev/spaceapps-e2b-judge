# Rapport de jugement v3.0 (Calibré sur Cohorte 10 Projets & 5 MicroVMs E2B) — marswalk (DRAFT - README used as stand-in for the submission text)
*Panel multi-modèles de 5 juges isolés E2B · 2026-11-15 23:03 UTC · défi : Interplanetary Survival Guide: Martian Map*

## Verdict & Probabilité Calibrée
- **Admissibilité : NON ADMISSIBLE au jugement mondial (portes obligatoires en échec)**
- **Score Panel Brut (Intervalle 95%) : `80.0% ± 4.3%`** (Médiane : **21 / 25 = `84.0%`**, Moyenne : **20 / 25**, Écart-type inter-juges : `4.9%`)
- **Score Corrigé Anti-Complaisance ( Ancrage historique Space Apps 3.0/5 ) : `76.0% / 100%`**
- **Classement à l'Aveugle dans la Cohorte de 10 Projets (`SYNTH_ARCH_01..09` + Candidat) : Rang Médian `#4 / 10`** (rangs par juge : `J1_local_ux_ai_reviewer`=#3, `J2_local_geomatics_data_reviewer`=#5, `J3_global_planetary_cartography_sme`=#5, `J4_global_geodesy_ivv_sme`=#4, `J5_exec_mission_directorate_reviewer`=#4)
- **Probabilité Estimée de Nomination / Prix Mondial (état actuel) : `0.0%`** *(Potentiel si portes `G-01`/`G-02`/`G-04` résolues avant 23h59 : **`~55.0%`**)*
- **Vote de nomination mondiale :** `J1_local_ux_ai_reviewer` = NON, `J2_local_geomatics_data_reviewer` = NON, `J3_global_planetary_cartography_sme` = NON, `J4_global_geodesy_ivv_sme` = NON, `J5_exec_mission_directorate_reviewer` = NON
- **Sondage officiel SME (`adds_professional_value`) :** `J1_local_ux_ai_reviewer` = OUI, `J2_local_geomatics_data_reviewer` = OUI, `J3_global_planetary_cartography_sme` = OUI, `J4_global_geodesy_ivv_sme` = OUI, `J5_exec_mission_directorate_reviewer` = OUI
- ⚠️ Au moins un juge a utilisé un modèle distinct ou de repli (voir manifeste).

## Contrôle d'admissibilité (déterministe, sans LLM)
| ID | Contrôle | Statut | Fait vérifié |
|---|---|---|---|
| G-01 | required_fields | ❌ FAIL | Missing required submission fields: ['public_url'] |
| G-02 | public_url_no_login | ❌ FAIL | No public project URL provided. |
| G-03 | repo_public | ✅ PASS | Anonymous git ls-remote https://github.com/SeCuReDmE-main-dev/marswalk -> exit 0 |
| G-04 | demo_limits | ❌ FAIL | No demo file provided (7-slide deck or <=30 s video is mandatory). |
| G-05 | english_language | ✅ PASS | Submission text language detection: [('en', 1.0)] |
| G-06 | nasa_data_cited | ✅ PASS | NASA data/mission terms found in submission text: ['crism', 'curiosity', 'hirise', 'jpl', 'mars 2020', 'meda', 'mola', 'mro', 'msl', 'nasa', 'perseverance', 'rad', 'themis', 'usgs'] |
| G-07 | references_listed | ✅ PASS | A References/Sources section is present. |
| G-08 | ai_disclosure | ✅ PASS | AI usage disclosure found (matched 'Use of AI'). |
| G-09 | deadline_context | ℹ️ INFO | Judge run at 2026-11-15 21:52:09 UTC; deadline Sunday Nov 15 2026 23:59 local time (Montreal, UTC-5). |

## Notes par critère (échelle officielle 1–5 & conversion sur 100%)
| Critère | Médiane (/5) | Médiane (%) | Moyenne (/5) | Moyenne (%) | J1_local_ux_ai_reviewer | J2_local_geomatics_data_reviewer | J3_global_planetary_cartography_sme | J4_global_geodesy_ivv_sme | J5_exec_mission_directorate_reviewer | Écart |
|---|---|---|---|---|---|---|---|---|---|---|
| **Impact** | **4/5** | **80.0%** | 4/5 | **80.0%** | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 0 |
| **Creativity** | **5/5** | **100.0%** | 4.6/5 | **92.0%** | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 1 |
| **Validity** | **5/5** | **100.0%** | 5/5 | **100.0%** | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 0 |
| **Relevance** | **5/5** | **100.0%** | 4.8/5 | **96.0%** | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 1 |
| **Presentation** | **2/5** | **40.0%** | 1.6/5 | **32.0%** | 2/5 (40%) | 1/5 (20%) | 1/5 (20%) | 2/5 (40%) | 2/5 (40%) | 1 |
| **TOTAL GLOBAL** | **21/25** | **84.0%** | **20/25** | **80.0%** | **20/25 (80.0%)** | **18/25 (72.0%)** | **20/25 (80.0%)** | **21/25 (84.0%)** | **21/25 (84.0%)** | — |

### Impact
- **`J1_local_ux_ai_reviewer` → 4/5** — The project tackles a critical, life-threatening problem for human Mars exploration: orbital models hide steep slopes that threaten astronauts. Citing SUB: 'the hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity (EVA) lives in the scale gap'. It sets a standard far beyond typical hackathons, though immediate public reach is dampened by missing live hosting (G-01, G-02).  
  Preuves : SUB, G-01, G-02 · Citation vérifiée : « the hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity (EVA) lives in the scale gap »
- **`J2_local_geomatics_data_reviewer` → 4/5** — Addresses a critical, unaddressed tactical hazard in human Mars surface operations by exposing how orbital terrain smoothing conceals steep slopes, directly aligning with domain knowledge on rover mobility safety. SUB shows 'the hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity (EVA) lives in the scale gap'.  
  Preuves : SUB, E-02 · Citation vérifiée : « the hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity (EVA) lives in the scale gap »
- **`J3_global_planetary_cartography_sme` → 4/5** — MarsWalk delivers high potential impact for astronaut surface safety by demonstrating how regional 64 m orbital maps mask life-threatening scarp slopes, proving a -5.05 degree underestimation bias ("-5.05° systematic negative bias"). However, its current execution is focused on a 2 km x 2 km window in Jezero Crater, which slightly restricts its immediate global operational reach compared to global planetary tools (SUB, E-01).  
  Preuves : SUB, E-01 · Citation vérifiée : « -5.05° systematic negative bias »
- **`J4_global_geodesy_ivv_sme` → 4/5** — The project directly solves a life-critical challenge in planetary exploration by exposing how coarse orbital elevation models hide steep drop-offs that threaten human spacewalkers. As noted in the submission, the hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity lives in the scale gap between coarse orbital rasters and the ground footprint. It surpasses finalist SYNTH_ARCH_04 by replacing arbitrary heuristic costs with empirical hazard detection, though its operational scope is currently confined to the Jezero fan.  
  Preuves : SUB, E-05 · Citation vérifiée : « hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity »
- **`J5_exec_mission_directorate_reviewer` → 4/5** — MarsWalk addresses a critical operational safety bottleneck for Moon-to-Mars human surface operations: orbital DTM resolution blindness that can lead to catastrophic spacesuit or rover rollover. As stated in SUB, 'the hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity (EVA) lives in the scale gap'. It beats SYNTH_ARCH_03 and SYNTH_ARCH_04 by anchoring safety directly to EVA metabolic constraints (EVA-EXP-0042) and verified rover tilts. It falls just short of a 5 only because its quantitative proof is demonstrated exclusively on a single 2x2 km window in Jezero Crater.  
  Preuves : SUB, E-04 · Citation vérifiée : « the hazard that breaks a rover wheel or exhausts an astronaut on an Extravehicular Activity (EVA) lives in the scale gap »

### Creativity
- **`J1_local_ux_ai_reviewer` → 4/5** — Confronting orbital DTM scales against actual rover tilt telemetry using a plithogenic neutrosophic framework is a completely original paradigm compared to traditional single-resolution GIS overlays in SYNTH_ARCH_03 and SYNTH_ARCH_06. Citing SUB: 'Multi-Scale Planetary Geodesy, Plithogenic Neutrosophic Hazard Verification', showing true inventive problem formulation.  
  Preuves : SUB · Citation vérifiée : « Multi-Scale Planetary Geodesy, Plithogenic Neutrosophic Hazard Verification »
- **`J2_local_geomatics_data_reviewer` → 4/5** — Introduces a plithogenic neutrosophic truth-indeterminacy-falsity framework to handle terrain uncertainty across scales, offering a much more sophisticated evaluation than typical linear weighted pathfinders. SUB notes 'Multi-Scale Hazard Verification & Plithogenic <T, I, F> Engine'.  
  Preuves : SUB, E-02 · Citation vérifiée : « Multi-Scale Hazard Verification & Plithogenic <T, I, F> Engine »
- **`J3_global_planetary_cartography_sme` → 5/5** — The project presents a groundbreaking cartographic concept by explicitly accounting for scale bias between orbital DTMs and human foot-scale hazards using a "Plithogenic Neutrosophic triplet <T, I, F>". It outperforms single-resolution pathfinders like SYNTH_ARCH_03 and SYNTH_ARCH_04 by evaluating 1m, 4m, 16m, and 64m Horn baselines simultaneously to enforce persistent-hazard overrides, preventing smooth regional maps from hiding deadly local cliffs (SUB, E-01).  
  Preuves : SUB, E-01 · Citation vérifiée : « Plithogenic Neutrosophic triplet <T, I, F> »
- **`J4_global_geodesy_ivv_sme` → 5/5** — MarsWalk introduces a truly original paradigm: The Map That Knows At Which Scale It Lies. Employing a Plithogenic Neutrosophic evaluation framework (<T, I, F>) to prevent fine-scale scarp hazards from being smoothed away by coarse regional orbital baselines is a groundbreaking mathematical contribution that stands far above standard hackathon pathfinders like SYNTH_ARCH_03 and SYNTH_ARCH_04.  
  Preuves : SUB · Citation vérifiée : « The Map That Knows At Which Scale It Lies »
- **`J5_exec_mission_directorate_reviewer` → 5/5** — MarsWalk introduces an entirely novel paradigm into planetary cartography: 'The Map That Knows At Which Scale It Lies'. While peer projects SYNTH_ARCH_03 and SYNTH_ARCH_04 rely on single-scale rasters and compensatory linear weighted sums that dangerously trade slope for science value, MarsWalk deploys multi-baseline Horn kernels (1m, 4m, 16m, 64m) combined with a non-compensatory plithogenic neutrosophic framework (<T, I, F>). This ensures steep scarp hazards trigger absolute safety vetoes, representing a major innovation over conventional GIS hackathon entries.  
  Preuves : SUB, E-02 · Citation vérifiée : « Multi-Scale Planetary Geodesy, Plithogenic Neutrosophic Hazard Verification »

### Validity
- **`J1_local_ux_ai_reviewer` → 5/5** — Scientifically peerless. It passes automated checks (E-06: 110 passed pytest tests; E-07: clean Vite frontend compilation). It decisively outperforms SYNTH_ARCH_03 and SYNTH_ARCH_04 by demonstrating quantitative validation against ground truth. Citing SUB: 'Even-Sol Ground-Truth Specificity | 97.7% (43 / 44 gentle even-sol Perseverance stops classified traversable)'. Domain knowledge confirms Horn multi-baseline filtering and neutrosophic uncertainty handle planetary scale gaps robustly.  
  Preuves : SUB, E-06, E-07 · Citation vérifiée : « Even-Sol Ground-Truth Specificity | 97.7% (43 / 44 gentle even-sol Perseverance stops classified traversable) »
- **`J2_local_geomatics_data_reviewer` → 5/5** — Demonstrates exceptional geodetic rigor, surpassing finalists SYNTH_ARCH_03 and SYNTH_ARCH_04 by validating orbital slope artifacts against 708 measured rover waypoints with full code reproducibility. E-06 and E-07 prove passing backend and frontend builds. E-08 verifies '11 cited external URLs checked, 0 unreachable.'.  
  Preuves : E-06, E-07, E-08 · Citation vérifiée : « 11 cited external URLs checked, 0 unreachable. »
- **`J3_global_planetary_cartography_sme` → 5/5** — Technically flawless scientific execution, verified by 110 passing pytest cases ("pytest -q --tb=short exit 0") and successful production frontend compilation ("Frontend `npm run build` in frontend exit 0."). Unlike SYNTH_ARCH_03 and SYNTH_ARCH_04 which lack ground-truth validation, MarsWalk validates its multi-scale hazard model against 708 real Perseverance rover tilt measurements and integrates peer-reviewed bio-energetics, MKIII suit metabolic power, Curiosity RAD space radiation, and ITU-R P.526 knife-edge UHF diffraction (SUB, E-06, E-07).  
  Preuves : SUB, E-06, E-07 · Citation vérifiée : « pytest -q --tb=short exit 0 »
- **`J4_global_geodesy_ivv_sme` → 5/5** — Scientifically and mathematically impeccable under NASA IV&V criteria. The engine evaluates Horn 3x3 slope baselines, correctly accounts for spherical Mars geodesy (R = 3,396,190 m), incorporates Minetti/Pandolf metabolic loads, and empirically proves a systematic negative bias on steep delta scarps (-5.05 degrees at 64 m). The repository executes 110 clean pytests (E-06) and the TypeScript/Vite production frontend builds with zero errors (E-07), far exceeding the technical rigor of SYNTH_ARCH_03 and SYNTH_ARCH_04.  
  Preuves : SUB, E-06, E-07 · Citation vérifiée : « systematic negative bias on steep delta scarps »
- **`J5_exec_mission_directorate_reviewer` → 5/5** — The scientific validity of MarsWalk is outstanding and backed by exhaustive automated empirical evidence. While SYNTH_ARCH_04 lacks ground-truth verification against physical rover telemetry, MarsWalk validates its multi-scale models against 708 real Perseverance waypoints, proving a '-5.05° systematic negative bias' on steep scarps at 64m scale. The codebase passes all tests cleanly with 'pytest -q --tb=short exit 0' (E-06) covering 110 pytest tests and a successful production build (E-07). All 11 external research citations are verified live (E-08).  
  Preuves : SUB, E-06, E-07, E-08 · Citation vérifiée : « -5.05° systematic negative bias »

### Relevance
- **`J1_local_ux_ai_reviewer` → 5/5** — Directly targets the core challenge requirement of layered multi-mission NASA data for human Marswalks. Integrates HiRISE DTMs, MMGIS rover waypoints, and MSL radiation. Citing SUB: '708 real ground-truth waypoints and measured rover tilts (Sol 13 -> Sol 2022) recorded by NASA\'s Perseverance rover across Jezero Crater and the Western Delta Fan'. Beats SYNTH_ARCH_03 and SYNTH_ARCH_04 by utilizing both orbital and in-situ telemetry.  
  Preuves : SUB, G-06, E-08 · Citation vérifiée : « 708 real ground-truth waypoints and measured rover tilts (Sol 13 -> Sol 2022) recorded by NASA's Perseverance rover across Jezero Crater and the Western Delta Fan »
- **`J2_local_geomatics_data_reviewer` → 4/5** — Directly tackles the Interplanetary Survival Guide challenge by layering HiRISE DTM, M2020 waypoints, and SIM 3464 geologic data. SUB accurately cites 'USGS Astrogeology Mars 2020 TRN HiRISE 1 m/px Digital Terrain Model Blended with MOLA'.  
  Preuves : SUB, G-06 · Citation vérifiée : « USGS Astrogeology Mars 2020 TRN HiRISE 1 m/px Digital Terrain Model Blended with MOLA »
- **`J3_global_planetary_cartography_sme` → 5/5** — The project directly addresses the core challenge requirement of creating an integrated, multi-layered map for human Marswalk safety. It "Integrates 5 primary datasets (HiRISE 1 m DTM, HiRISE 25 cm WMTS, M20 708 Waypoints & 45.2 km Traverse, M20 Navcam/Mastcam-Z Raw Images, USGS SIM 3464 Geologic Map)" with strict data provenance contracts and citable NASA constraints, going far beyond regional portals like Mars Trek to solve hyper-local EVA survival (SUB, E-04).  
  Preuves : SUB, E-04 · Citation vérifiée : « Integrates 5 primary datasets (HiRISE 1 m DTM, HiRISE 25 cm WMTS, M20 708 Waypoints & 45.2 km Traverse, M20 Navcam/Mastcam-Z Raw Images, USGS SIM 3464 Geologic Map) »
- **`J4_global_geodesy_ivv_sme` → 5/5** — Directly and deeply addresses every facet of the Martian Map challenge prompt. It Integrates 5 primary datasets including HiRISE 1m DTM, 25cm orthomosaics, USGS SIM 3464 geologic units, and 708 actual Perseverance rover stops and tilt measurements. Missing layers like CRISM or MEDA are explicitly declared out-of-pack rather than fabricated, demonstrating exemplary provenance.  
  Preuves : SUB, E-04, E-08 · Citation vérifiée : « Integrates 5 primary datasets »
- **`J5_exec_mission_directorate_reviewer` → 5/5** — MarsWalk directly answers every mandate of the Interplanetary Survival Guide: Martian Map challenge. Unlike SYNTH_ARCH_03 and SYNTH_ARCH_06 which simply stream WMTS tiles, MarsWalk integrates MRO HiRISE 1m DTMs, USGS SIM 3464 geological units, MMGIS Perseverance traverse telemetry, and Hassler et al. MSL RAD radiation baselines into a unified astronaut safety corridor. As confirmed by probe E-04 with 53 HiRISE and 44 Perseverance references, NASA open data forms the core mathematical foundation of the project.  
  Preuves : SUB, E-04, E-05 · Citation vérifiée : « USGS Astrogeology Mars 2020 TRN HiRISE 1 m/px Digital Terrain Model Blended with MOLA »

### Presentation
- **`J1_local_ux_ai_reviewer` → 2/5** — While the SVG map card and README text are written with extreme professional polish, the project fails mandatory Space Apps eligibility gates. Citing G-04: 'No demo file provided (7-slide deck or <=30 s video is mandatory).' and G-01: 'Missing required submission fields: [\'public_url\']'. Under official guidelines, absence of a demo presentation and live URL caps Presentation at 2.  
  Preuves : G-01, G-04 · Citation vérifiée : « No demo file provided (7-slide deck or <=30 s video is mandatory). »
- **`J2_local_geomatics_data_reviewer` → 1/5** — Mandatory gate failure: no presentation demo video or slide deck was submitted, and no public project URL was provided. Under judging rules, presentation cannot receive credit without deliverables. G-01 confirms 'Missing required submission fields: [public_url]' and G-04 confirms 'No demo file provided (7-slide deck or <=30 s video is mandatory).'.  
  Preuves : G-01, G-04 · Citation vérifiée : « No demo file provided (7-slide deck or <=30 s video is mandatory). »
- **`J3_global_planetary_cartography_sme` → 1/5** — The team failed mandatory Space Apps submission requirements by not providing a 7-slide presentation deck or 30-second demo video ("No demo file provided (7-slide deck or <=30 s video is mandatory)."). Additionally, no public URL was submitted ("No public project URL provided."), preventing zero-friction web access for judges despite the underlying software being fully functional (G-01, G-02, G-04).  
  Preuves : G-01, G-02, G-04 · Citation vérifiée : « No demo file provided (7-slide deck or <=30 s video is mandatory). »
- **`J4_global_geodesy_ivv_sme` → 2/5** — While the repository markdown and embedded SVG survival map card are remarkably thorough, the project fails mandatory Space Apps eligibility gates. As recorded in probe G-04, No demo file provided (7-slide deck or <=30 s video is mandatory). Under the official scoring guide, missing demo deliverables strictly caps Presentation at 2.  
  Preuves : G-01, G-04 · Citation vérifiée : « No demo file provided (7-slide deck or <=30 s video is mandatory). »
- **`J5_exec_mission_directorate_reviewer` → 2/5** — The textual documentation in the repository and submission text is exceptional, featuring clear markdown tables and a generated survival map card. However, probe G-01 confirms 'Missing required submission fields: [\'public_url\']' and probe G-04 notes 'No demo file provided (7-slide deck or <=30 s video is mandatory).' Under strict Space Apps rules, failing both mandatory presentation gates caps the score at 2.  
  Preuves : G-01, G-04 · Citation vérifiée : « Missing required submission fields: ['public_url'] »

## Corrections avant la date limite (classées gain / effort)
- **[Presentation +1 · ~15 min]** Deploy the built frontend/dist folder to Vercel, Netlify, or GitHub Pages and fill in the public_url field on the Space Apps submission portal. *(→ `J3_global_planetary_cartography_sme`, preuves G-01, G-02)*
- **[Presentation +1 · ~20 min]** Deploy the built frontend/dist folder to GitHub Pages or Vercel and paste the public link into the submission portal. *(→ `J1_local_ux_ai_reviewer`, preuves G-01, G-02, E-07)*
- **[Presentation +1 · ~20 min]** Deploy the pre-built frontend distribution to GitHub Pages or Vercel and paste the live link into the public_url field. *(→ `J2_local_geomatics_data_reviewer`, preuves G-01, E-07)*
- **[Presentation +1 · ~20 min]** Deploy the built frontend/dist folder to GitHub Pages or Vercel and paste the active URL into the submission public_url field. *(→ `J4_global_geodesy_ivv_sme`, preuves G-01, E-07)*
- **[Presentation +1 · ~20 min]** Deploy the already compiled frontend dist/ folder (E-07) to GitHub Pages or Vercel and paste the public link into the submission form. *(→ `J5_exec_mission_directorate_reviewer`, preuves G-01, E-07)*
- **[Presentation +1 · ~25 min]** Record and upload a 30-second video demo (or 7-slide PDF) demonstrating the interactive web app and SVG Map Card generator, and attach it to the project submission page. *(→ `J3_global_planetary_cartography_sme`, preuves G-04)*
- **[Presentation +1 · ~30 min]** Generate a compliant 7-slide PDF presentation deck showcasing the problem, Sol 700 scarp validation, and the SVG survival card, and upload it as the demo file. *(→ `J4_global_geodesy_ivv_sme`, preuves G-04, SUB)*
- **[Presentation +1 · ~35 min]** Export and upload a compliant 7-slide PDF presentation deck clearly showing the Sol 700 scarp trap and architecture. *(→ `J2_local_geomatics_data_reviewer`, preuves G-04)*
- **[Presentation +1 · ~35 min]** Export a compliant 7-slide PDF presentation summarizing the Sol 700 scarp trap discovery, multi-scale geodesy, and map card UI, and attach it to the demo field. *(→ `J5_exec_mission_directorate_reviewer`, preuves G-04, E-02)*
- **[Presentation +1 · ~45 min]** Create and attach a compliant 7-slide PDF presentation deck showcasing the core discovery, map card, and UI screenshots. *(→ `J1_local_ux_ai_reviewer`, preuves G-04)*

## Faiblesses relevées
- [Presentation] Missing a public web application URL, preventing external evaluators and non-technical stakeholders from inspecting the live tool without local compilation. *(`J1_local_ux_ai_reviewer`)*
- [Presentation] Missing a mandatory short demo presentation (either a 7-slide deck or 30-second demo video), violating global eligibility requirements. *(`J1_local_ux_ai_reviewer`)*
- [Validity] The quantitative ground-truth validation is currently constrained to a single 2 km by 2 km window of Jezero Crater's Western Delta Fan, without automated testing on other candidate human landing sites. *(`J1_local_ux_ai_reviewer`)*
- [Presentation] Complete omission of mandatory demo file (7-slide deck or 30-second video), violating eligibility criteria. *(`J2_local_geomatics_data_reviewer`)*
- [Presentation] Missing live hosted public web application URL, preventing real-time browser evaluation during jury triage. *(`J2_local_geomatics_data_reviewer`)*
- [Validity] Spatial processing scope is constrained to a single 2 km by 2 km bounding tile of Jezero Western Delta rather than an expandable Mars-wide pipeline. *(`J2_local_geomatics_data_reviewer`)*
- [Presentation] Failed mandatory submission eligibility requirement G-04 by omitting a 30-second demo video or 7-slide presentation deck. *(`J3_global_planetary_cartography_sme`)*
- [Presentation] Failed mandatory submission requirement G-01/G-02 by leaving the public project URL field blank. *(`J3_global_planetary_cartography_sme`)*
- [Impact] Spatial demonstration scope is locked to a single 2 km x 2 km window on Jezero Western Fan, requiring manual CLI pack builds for other Martian sites. *(`J3_global_planetary_cartography_sme`)*
- [Presentation] Missing mandatory demo presentation deliverables: no 7-slide PDF deck or 30-second demo video was provided on the submission page. *(`J4_global_geodesy_ivv_sme`)*
- [Presentation] No live hosted public web link provided (G-01/G-02), preventing non-technical evaluators from interacting with the tool without local cloning and compilation. *(`J4_global_geodesy_ivv_sme`)*
- [Impact] Spatial scope is currently constrained to a pre-packaged 2 km x 2 km Delta Front window in Jezero Crater rather than arbitrary on-the-fly planetary coordinates. *(`J4_global_geodesy_ivv_sme`)*
- [Presentation] Missing mandatory presentation deliverables: no public web URL provided and no 7-slide deck or 30-second video demo attached. *(`J5_exec_mission_directorate_reviewer`)*
- [Impact] Geographic scope is currently restricted to a single 2 km x 2 km testbed across the Jezero Crater Western Delta Fan without automated pipeline expansion to Gale Crater or Artemis south polar sites. *(`J5_exec_mission_directorate_reviewer`)*
- [Validity] Dynamic environmental data (such as atmospheric pressure and dust optical depth from MEDA) are represented via static sealed packs rather than a live streaming API. *(`J5_exec_mission_directorate_reviewer`)*

## Forces relevées
- Confronts multi-scale orbital slope models against 708 measured Perseverance rover tilts to prove a -5.05 degree scarp underestimation bias. *(`J1_local_ux_ai_reviewer`)*
- Exceptional code quality and reproducibility, backed by passing test suites and clean frontend builds in an isolated environment. *(`J1_local_ux_ai_reviewer`)*
- Exemplary adherence to 'Thoughtful use of AI', documenting human architectural authority and deterministic verification. *(`J1_local_ux_ai_reviewer`)*
- Rigorous applied geomatics proving systematic -5.05 degree underestimation bias on steep scarps when using 64m coarse orbital grids compared to 1m/4m baselines. *(`J2_local_geomatics_data_reviewer`)*
- Complete, verifiable open-science engineering with 110 pytest passing and clean TypeScript frontend compilation. *(`J2_local_geomatics_data_reviewer`)*
- Impeccable data provenance with primary links to USGS, NASA PDS, and JPL MMGIS verified alive. *(`J2_local_geomatics_data_reviewer`)*
- Confronts multi-scale orbital scale bias by comparing 1m, 4m, 16m, and 64m Horn baselines against ground-truth Perseverance rover tilt measurements. *(`J3_global_planetary_cartography_sme`)*
- Implements rigorous physical models including Minetti bio-energetics, Pandolf-CSRM suited metabolic power, Curiosity RAD GCR dose, and ITU-R P.526 UHF radio diffraction. *(`J3_global_planetary_cartography_sme`)*
- Exemplary software engineering quality with 110 automated Pytest cases, 22 Vitest cases, and clean production build verification. *(`J3_global_planetary_cartography_sme`)*
- Empirical multi-scale validation against 708 real Perseverance rover tilt measurements proving a -5.05 degree slope underestimation bias in coarse 64 m orbital data. *(`J4_global_geodesy_ivv_sme`)*
- Production-grade software hygiene with 110 passing pytest unit tests, frozen data contracts, SHA-256 sealed static packs, and clean Vite frontend builds. *(`J4_global_geodesy_ivv_sme`)*
- Rigorous human EVA safety physics incorporating anisotropic metabolic cost (Minetti/Pandolf), Apollo slope limits, Bullington knife-edge UHF comms diffraction, and non-compensatory lexicographic safety vetoes. *(`J4_global_geodesy_ivv_sme`)*
- Empirical multi-scale terrain geodesy proving that 64m orbital DTMs underestimate scarp slopes by 5.05 degrees, successfully validated against 708 real Perseverance rover waypoints. *(`J5_exec_mission_directorate_reviewer`)*
- Flawless software engineering rigor with 110 pytest unit tests passing, zero broken external references, and a clean Vite production build. *(`J5_exec_mission_directorate_reviewer`)*
- Non-compensatory plithogenic safety veto architecture that strictly prevents high scientific interest from overriding fatal slope and metabolic thresholds. *(`J5_exec_mission_directorate_reviewer`)*

## Prix mondiaux visables (sur les 10 officiels)
- **Best Use of Data** — cité par 5 juge(s) : J1_local_ux_ai_reviewer, J2_local_geomatics_data_reviewer, J3_global_planetary_cartography_sme, J4_global_geodesy_ivv_sme, J5_exec_mission_directorate_reviewer
- **Best Use of Science** — cité par 5 juge(s) : J1_local_ux_ai_reviewer, J2_local_geomatics_data_reviewer, J3_global_planetary_cartography_sme, J4_global_geodesy_ivv_sme, J5_exec_mission_directorate_reviewer
- **Best Use of Technology** — cité par 1 juge(s) : J3_global_planetary_cartography_sme

## Calibration & Classement à l'Aveugle sur Cohorte de 10 Projets (`SYNTH_ARCH_01..09`)
| Juge | Modèle utilisé | Concordance (`tau`) | Bandes de référence respectées (`/9`) | Rang du Candidat (`/10`) | Score Cohorte Candidat (`/25`) | Verdict comparatif |
|---|---|---|---|---|---|---|
| `J1_local_ux_ai_reviewer` | `gemini-3.8-flash` | ✅ CALIBRÉ (`1.00`) | `9/9` | **`#3/10`** | `19/25` | Highest scientific and algorithmic depth in the cohort, but penalized by missing live public URL and demo presentation gates. |
| `J2_local_geomatics_data_reviewer` | `gemini-3.8-flash` | ✅ CALIBRÉ (`1.00`) | `9/9` | **`#5/10`** | `18/25` | World-class geodetic science and verified test suite, severely penalized by missing demo and public URL. |
| `J3_global_planetary_cartography_sme` | `gemini-3.5-flash` | ✅ CALIBRÉ (`0.87`) | `9/9` | **`#5/10`** | `20/25` | World-class planetary cartography and scale-bias math, heavily penalized by missing public URL and demo presentation gates. |
| `J4_global_geodesy_ivv_sme` | `gemini-3.8-flash` | ✅ CALIBRÉ (`1.00`) | `9/9` | **`#4/10`** | `21/25` | Highest scientific and algorithmic validity in the cohort, but penalized by missing demo deck and public URL gates. |
| `J5_exec_mission_directorate_reviewer` | `gemini-3.7-flash` | ✅ CALIBRÉ (`1.00`) | `9/9` | **`#4/10`** | `21/25` | Peerless scientific geodesy and test coverage, ranked 4th solely due to missing demo deck and public URL gates. |

## Parole aux Juges : Ce que j'ai jugé, Pourquoi, Comment faire basculer mon vote & Ce qu'il faut sanctuariser (`judge_debrief`)
### 🎙️ `J1_local_ux_ai_reviewer` (Modèle `gemini-3.8-flash` · Score `20/25 = 80.0%` · Budget simulé `172s / 180s`)
- **Impression à 30 secondes :** *« Unbelievable algorithmic and cartographic rigor in the README, but disqualified from global nomination right now due to missing public URL and missing demo presentation. »*
- **1. Ce que j'ai jugé et comment :** Under our Montreal 180-second clock, I immediately looked for the live interactive cartographic artifact and demo deck. Finding neither (G-01 and G-04 FAIL), I checked the repo build and test suite, which verified 110 pytest and complete Vite frontend compilation. I evaluated whether the multi-scale slope math and plithogenic neutrosophic framework represented genuine graph/traversability engineering or superficial AI wrappers.
- **2. Pourquoi j'ai mis cette note :** Total score is 19/25. Algorithmic validity, multi-scale geodesy, and NASA data integration are world-class (scoring 5 on Validity and Relevance, beating SYNTH_ARCH_03 and SYNTH_ARCH_04). However, Space Apps Presentation rules are strict: lacking a public web URL and a 7-slide deck or 30s video caps Presentation at 2/5 and prevents ranking above complete global champions like SYNTH_ARCH_02 or SYNTH_ARCH_01.
- **3. Ce qu'il faut améliorer pour faire basculer mon jugement :** Deploy the built Vite frontend to GitHub Pages / Vercel and attach an exported 7-slide PDF or 30-second walkthrough before 23:59. That would immediately elevate Presentation from 2 to 5 and make this Montreal's #1 contender for Global Nomination.
- **4. Le positif qui m'a marqué :** The discovery of the -5.05 degree coarse-scale underestimation bias confronting 64m orbital grids with 708 Perseverance ground-truth stops is extraordinary peer-review-grade work.
- **5. À GARDER ABSOLUMENT (Sanctuarisé / Touche pas à ça) :**
  - 🔒 The plithogenic <T, I, F> multi-scale hazard verification engine and strict veto logic
  - 🔒 The deterministic SHA-256 sealed static pack architecture (public_packs/jezero/v1/manifest.json)
  - 🔒 The SVG xEVA Survival Map Card generation pipeline

### 🎙️ `J2_local_geomatics_data_reviewer` (Modèle `gemini-3.8-flash` · Score `18/25 = 72.0%` · Budget simulé `245s / 300s`)
- **Impression à 30 secondes :** *« Incredible geodetic depth and rigorous multi-scale slope proof, but immediate disqualification danger due to missing public URL and missing demo file. »*
- **1. Ce que j'ai jugé et comment :** Under my strict 5-minute stopwatch as an applied geomatics and open data lead, I checked data provenance first: verified USGS HiRISE 1m DTM, MMGIS waypoints, and SIM 3464 citations against live URLs, followed by multi-scale slope bias math and test suites. I then checked delivery gates G-01 and G-04.
- **2. Pourquoi j'ai mis cette note :** The core science, data contracts, and code execution are global-winner caliber (passing 110 pytest and frontend build), but failing both the public URL and demo presentation gates caps Presentation at 2 and blocks immediate Global Nominee recommendation.
- **3. Ce qu'il faut améliorer pour faire basculer mon jugement :** Uploading a compliant 7-slide PDF demo deck and linking a deployed web URL (e.g., GitHub Pages or Vercel) before the 23:59 deadline would immediately elevate this submission to a top-2 local nomination.
- **4. Le positif qui m'a marqué :** The empirical confrontation of orbital scale bias against 708 Perseverance ground-truth tilt points is outstanding applied geomatics that directly exposes real terrain hazards.
- **5. À GARDER ABSOLUMENT (Sanctuarisé / Touche pas à ça) :**
  - 🔒 The multi-scale Horn slope comparison (1m vs 4m vs 16m vs 64m) exposing the Sol 700 scarp trap
  - 🔒 The cryptographic manifest.json SHA-256 data contract separating MEASURED, DERIVED, and SIMULATED datasets

### 🎙️ `J3_global_planetary_cartography_sme` (Modèle `gemini-3.5-flash` · Score `20/25 = 80.0%` · Budget simulé `240s / 300s`)
- **Impression à 30 secondes :** *« Stunning scientific rigour and multi-scale geodesy in the repository, but missing public URL and demo presentation video gates. »*
- **1. Ce que j'ai jugé et comment :** Under severe 300-second triage pressure, I audited the data contracts, multi-scale terrain slope math, and automated test outputs against NASA SSERVI / Mars Trek standards. I verified that the Python engine and React/Three.js frontend pass build and test suites, while noting the administrative failure on demo and public URL submission gates.
- **2. Pourquoi j'ai mis cette note :** MarsWalk achieves flawless 5/5 scores in Creativity, Validity, and Relevance by rigorously proving the -5.05 degree scale-gap bias using 708 Perseverance ground-truth stops and multi-baseline DTM funnels. However, because no demo video or slide deck was attached (G-04), Presentation is capped at 1/5.
- **3. Ce qu'il faut améliorer pour faire basculer mon jugement :** To jump to the #1 or #2 spot in this cohort, the team must record a 30-second video demo of their HUD/Map Card generator and live deploy the built WebGL interface to Vercel or GitHub Pages before the 23:59 deadline tonight.
- **4. Le positif qui m'a marqué :** The non-compensatory safety veto engine, ITU-R P.526 UHF radio shadow modeling, and ground-truth validation against Perseverance rover tilt sensors represent the single best scientific geodesy implementation in this hackathon.
- **5. À GARDER ABSOLUMENT (Sanctuarisé / Touche pas à ça) :**
  - 🔒 public_packs/jezero/v1/manifest.json provenance contract with strictly declared MEASURED vs DERIVED tags
  - 🔒 src/marswalk/engine/obstacles_m1.py persistent-hazard override funnel logic

### 🎙️ `J4_global_geodesy_ivv_sme` (Modèle `gemini-3.8-flash` · Score `21/25 = 84.0%` · Budget simulé `240s / 300s`)
- **Impression à 30 secondes :** *« Unparalleled multi-scale photogrammetric and geodesic rigor in the repo, but a catastrophic omission of the required demo slides/video and live URL. »*
- **1. Ce que j'ai jugé et comment :** Under the 5-minute triage clock, I inspected the geodetic handling (Mars sphere R=3,396,190 m), Horn 3x3 multi-baseline slope kernels (1m/4m/16m/64m), and ground-truth validation against the 708 Perseverance rover tilt records. I then cross-referenced the automated test execution (E-06, E-07) and verified whether delivery gates (G-01 to G-04) were met.
- **2. Pourquoi j'ai mis cette note :** Scientifically and mathematically, this is a masterclass in planetary GIS and landing hazard verification, easily beating finalist benchmarks. However, failing mandatory eligibility gates G-01 (public URL) and G-04 (demo file) caps Presentation at 2 and prevents ranking it above complete global winners SYNTH_ARCH_01 and SYNTH_ARCH_02.
- **3. Ce qu'il faut améliorer pour faire basculer mon jugement :** Uploading a 7-slide PDF demo walk-through and deploying the frontend to a public Vercel/Pages URL before the 23:59 deadline would immediately lift Presentation from 2 to 5 and elevate MarsWalk to the #1 spot in the cohort.
- **4. Le positif qui m'a marqué :** The empirical identification of the -5.05 degree slope underestimation bias at 64 m orbital resolution and the non-compensatory lexicographic safety veto backed by 110 clean pytests.
- **5. À GARDER ABSOLUMENT (Sanctuarisé / Touche pas à ça) :**
  - 🔒 The Horn 3x3 multi-baseline concordance funnel (1m, 4m, 16m, 64m) and persistent-hazard override rule.
  - 🔒 The SHA-256 cryptographic site pack manifest and data contract separating MEASURED, DERIVED, and SIMULATED quantities.
  - 🔒 The non-compensatory safety vetoes (slope > 20 deg, walkback > 2000 m, active SPE alert).

### 🎙️ `J5_exec_mission_directorate_reviewer` (Modèle `gemini-3.7-flash` · Score `21/25 = 84.0%` · Budget simulé `215s / 240s`)
- **Impression à 30 secondes :** *« Stunning scientific rigor confronting orbital DTMs with rover tilt ground truth, but severely crippled on executive presentation by missing demo deck and public URL. »*
- **1. Ce que j'ai jugé et comment :** Under 4-minute executive pressure during the executive review window, I scrutinized whether MarsWalk delivers actionable Moon-to-Mars planetary surface safety. I evaluated the multi-scale Horn slope calculations, tested whether the codebase compiles and passes test assertions, and checked whether the safety vetoes hold against real Perseverance telemetry.
- **2. Pourquoi j'ai mis cette note :** Scientifically and architecturally, MarsWalk is arguably the most sophisticated technical project in the entire challenge cohort. However, under non-negotiable Space Apps rules, failing to submit a 7-slide deck or 30-second video (G-04) and omitting a public URL (G-01) imposes a hard ceiling of 2 on Presentation, holding its total to 21/25.
- **3. Ce qu'il faut améliorer pour faire basculer mon jugement :** If the team deploys the pre-built Vite bundle (E-07) to Vercel/GitHub Pages and links a 7-slide PDF or 30s MP4 before the 23:59 Montreal deadline, Presentation jumps from 2 to 5, propelling MarsWalk straight to Global Winner status (#1 overall) and Best Use of Science nomination.
- **4. Le positif qui m'a marqué :** The empirical demonstration of a -5.05 degree slope underestimation bias at 64m orbital resolution versus 4m ground truth and the non-compensatory plithogenic safety veto on the Sol 700 scarp directly advance NASA and CSA surface rover/astronaut mission safety.
- **5. À GARDER ABSOLUMENT (Sanctuarisé / Touche pas à ça) :**
  - 🔒 The frozen data contract in docs/contracts/10_CONTRAT_DONNEES.md
  - 🔒 The 110 automated pytest fixtures in tests/ verifying rover tilt ground truth
  - 🔒 The deterministic SVG xEVA survival map card generator


## Justification des votes de nomination & valeur professionnelle (`adds_professional_value`)
- **`J1_local_ux_ai_reviewer`** : Cannot be nominated for Global Judging in its current state due to hard gate failures G-01 (missing public URL) and G-04 (missing demo file). If the team uploads a 7-slide deck and deploys their working build before 23:59, this becomes an immediate Global Nominee. · **`adds_professional_value`=True** : The demonstrated multi-scale terrain bias methodology provides actionable insights for cartographic data-mapping and traversability algorithms. · ⏱️ **Budget `172s / 180s`** (30s : *« Unbelievable algorithmic and cartographic rigor in the README, but disqualified from global nomination right now due to missing public URL and missing demo presentation. »*)
- **`J2_local_geomatics_data_reviewer`** : Cannot be nominated for Global Judging in its current state due to failing mandatory eligibility gates G-01 (missing public URL) and G-04 (missing demo slide deck/video). · **`adds_professional_value`=True** : The empirical demonstration of orbital slope bias across different geodetic baselines directly informs how space agencies should evaluate landing site safety and human rover traversability. · ⏱️ **Budget `245s / 300s`** (30s : *« Incredible geodetic depth and rigorous multi-scale slope proof, but immediate disqualification danger due to missing public URL and missing demo file. »*)
- **`J3_global_planetary_cartography_sme`** : Despite world-class scientific validity and technical execution, the project fails mandatory Space Apps eligibility requirements (missing public web URL and demo video/deck) and cannot advance to Global Finalist status unless these submission fields are populated. · **`adds_professional_value`=True** : As NASA planetary cartography SME, the team's demonstration of scale-gap bias (-5.05 degree slope underestimation at 64 m scale) provides direct utility for evaluating future Human Exploration Zone maps and astronaut EVA routing tools. · ⏱️ **Budget `240s / 300s`** (30s : *« Stunning scientific rigour and multi-scale geodesy in the repository, but missing public URL and demo presentation video gates. »*)
- **`J4_global_geodesy_ivv_sme`** : While the scientific validity is top 1% global caliber, Global Nomination cannot be approved until the mandatory public URL and demo presentation gates (G-01, G-04) are rectified before tonight's 23:59 deadline. · **`adds_professional_value`=True** : The multi-scale Horn kernel slope concordance analysis and persistent-hazard override framework provide immediate operational utility for future Mars 2020 and human xEVA landing site hazard assessments. · ⏱️ **Budget `240s / 300s`** (30s : *« Unparalleled multi-scale photogrammetric and geodesic rigor in the repo, but a catastrophic omission of the required demo slides/video and live URL. »*)
- **`J5_exec_mission_directorate_reviewer`** : While the scientific depth is worthy of a Global Winner, Space Apps eligibility rules strictly disqualify entries missing mandatory public URL and demo presentation files (G-01, G-04) from global nomination until cured. · **`adds_professional_value`=True** : The quantitative proof of multi-scale slope underestimation bias directly impacts CSA and NASA planning for lunar south pole Artemis xEVA corridors and Mars Sample Return rover operations. · ⏱️ **Budget `215s / 240s`** (30s : *« Stunning scientific rigor confronting orbital DTMs with rover tilt ground truth, but severely crippled on executive presentation by missing demo deck and public URL. »*)

## Rejets du validateur anti-hallucination
- Aucun : toutes les notes citent des preuves existantes et des citations exactes.

## Registre de preuves (sondes déterministes)
- **E-01** `repo_clone` (ALL) PASS — Cloned branch 'main' anonymously: 190 files; top extensions [('.py', 65), ('.md', 35), ('.json', 33), ('.ts', 12), ('.png', 8), ('.svg', 8), ('(none)', 7), ('.jpg', 5), ('.geojson', 3), ('.tsx', 3), ('.toml', 2), ('.mjs', 2)].
- **E-02** `repo_readme` (ALL) PASS — README present (15105 bytes).
- **E-03** `repo_license` (ALL) PASS — LICENSE file present.
- **E-04** `repo_nasa_data_refs` (SME) INFO — Files mentioning each NASA dataset/mission: {'HiRISE': 53, 'MOLA': 3, 'CTX': 5, 'CRISM': 11, 'THEMIS': 11, 'Mars Trek': 20, 'PDS': 3, 'MEDA (Perseverance weather)': 6, 'RAD (radiation)': 4, 'Mars 2020/Perseverance': 44, 'Curiosity/MSL': 19, 'USGS geologic map': 48, 'Jezero': 68, 'Gale/Mount Sharp': 11}
- **E-05** `repo_data_files` (SME) INFO — 19 data/imagery files under data/pack folders.
- **E-06** `repo_pytest` (ALL) PASS — pytest -q --tb=short exit 0: tte.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
- **E-07** `repo_frontend_build` (ALL) PASS — Frontend `npm run build` in frontend exit 0.
- **E-08** `citations_live` (ALL) PASS — 11 cited external URLs checked, 0 unreachable.

## Scellement (reproductibilité)
```json
{
 "project_title": "marswalk (DRAFT - README used as stand-in for the submission text)",
 "model": "gemini-3.1-pro-preview",
 "fallback_model": "gemini-3.8-flash",
 "gemini_cli_version": "0.68.0",
 "parallel_vms": true,
 "judges": [
  "J1_local_ux_ai_reviewer",
  "J2_local_geomatics_data_reviewer",
  "J3_global_planetary_cartography_sme",
  "J4_global_geodesy_ivv_sme",
  "J5_exec_mission_directorate_reviewer"
 ],
 "host_started_utc": "2026-11-15T22:30:41Z",
 "sha256": {
  "/judge/input/submission.json": "a233e5e8b95372449c3473d296f355fc4a3b94f3f3e7eedf20b91ac24ac83079",
  "/judge/input/submission.md": "37d58744da7c9b82639fc60c2573284bb3d44c4f2feac0a255de868360c1747a",
  "/judge/input/submission_text.md": "37d58744da7c9b82639fc60c2573284bb3d44c4f2feac0a255de868360c1747a",
  "/judge/rubric/challenge_martian_map_2026.md": "463b428c3b5ae4533c4eea619fcbd3222dedd76749a81e65d73359f14e418d1e",
  "/judge/rubric/judging_guide_2026.md": "68d5b91c14f92251d258a9d917839844807a4879a5c09765fe60e8cbe8f29c58",
  "/judge/vm/calibration_cohort.py": "bd08df599881f169406d89ef4e122b572b0acaba7292fd34be1280606520f350",
  "/judge/vm/panel.py": "e6f0ce6fa4ccf54e2c630822ce8ae8158e90d9b98f5f572116cf4aa3b982c0d1",
  "/judge/vm/probes.py": "91a8934b4a89ac231b1c4350c2f1423f06884922c5653a70096e603c83b79e22",
  "/judge/vm/report.py": "289dc8513369417cc1e755404d968e7094f3076981a0dda0e46aba15df72db43"
 }
}
```

*Limites : seuls les descripteurs « Score of 5 » sont officiels ; les ancres 1–4 et les 9 archétypes `SYNTH_ARCH_01..09` sont des profils synthétiques de calibration. Ce rapport est traçable aux preuves empiriques de la Vague 1, pas une prédiction garantie du jury.*