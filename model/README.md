# NI Circular Minerals Policy Model

A coupled **ABM × dynamic Input–Output × CGE** simulator of the Northern Ireland
minerals system (primary extraction → use → recycling), built to answer
consultation questions 2.1–2.7. The three tiers from
`../NI_Circular_Minerals_Model_Plan.md` are now all implemented:

- **Tier 1 (MVM)** — ABM → MFA → dynamic I-O, validated against Minviro anchors.
  The ABM is **firm-grounded**: each agent is a named NI operator from
  `company_register.csv`, so policy results emerge from real firms' attributes.
- **Tier 2** — adaptive agents; NI SAM; recursive-dynamic CGE (CES/Armington) with
  benchmark replication; spatial (11 council-area) employment layer.
- **Tier 3** — full ABM↔I-O↔CGE feedback: CGE prices feed back to agent decisions,
  wages raise the mining development hurdle, recovery capacity lifts recycling
  productivity.

## What it does
- Runs six policy-scenario families over a 30-year horizon (STPR 3.5% discounting).
- Each year: ABM agents decide under policy levers → physical material flows (MFA)
  → economic & environmental impact (dynamic I-O) → economy-wide adjustment (CGE)
  → feedback to next year → spatial job allocation → indicators for Q2.1–2.7.
- **Validated** against the Minviro report's scenario anchors (see below).

## Quick start
```bash
cd model
python run_mvm.py        # run scenarios, write outputs/
python make_plots.py     # render static figures to outputs/figures/
streamlit run dashboard.py   # interactive dashboard (Q2.1–2.7 tabs)
```
For online deployment, use the root-level `streamlit_app.py` with the root
`requirements.txt`; see `../DEPLOYMENT.md`.

Outputs land in `outputs/`:
- `validation.json` — I-O core vs Minviro anchors
- `scenario_timeseries.csv` — full 30-year annual results, all scenarios (incl. CGE
  wage index + per-council job columns)
- `scenario_comparison.csv` — side-by-side decision dashboard, including named-company evidence metrics
- `questions_summary.json` — indicators mapped to Q2.1–2.7 per scenario
- `spatial_jobs_by_district.csv` — end-year jobs by council area
- `ni_sam.csv` — constructed, balanced NI Social Accounting Matrix
- `figures/` — six PNG figures from `make_plots.py`

Requirements: Python 3.11+, `numpy`, `pandas`, `mesa>=3.0`, `scipy`, `matplotlib`,
`streamlit` (see `requirements.txt`).

## Structure
| File | Role |
|---|---|
| `data/data_register.csv` | every parameter → value → **source → status (real/proxy/gap)** |
| `data/company_register.csv` | named NI operators, public/desk-estimated scale signals, material streams, and planning/procurement scores |
| `data/ree_pilot.py` | REE/NdFeB permanent-magnet pilot data (researched values + provenance tags) |
| `src/data_register.py` | loads `data_register.csv` as the **single source of truth** for anchors, targets, recovery yields, collection rate and demand-growth drivers |
| `src/seed_parameters.py` | sectors, minerals, coefficients; real anchors & targets **read from the data register** |
| `src/company_data.py` | loads company evidence → ABM calibration signals (mining risk, recycler capacity, downstream demand, procurement) **plus firm capital pipeline, installed recycler capacity, recycling output floor, and firm employment-by-district** |
| `src/io_module.py` | dynamic Leontief I-O: Type I/II multipliers, GVA/jobs/CO₂/PM satellites |
| `src/mfa_module.py` | Material Flow Account: stock-flow per mineral, supply shares |
| `src/abm_module.py` | **firm-grounded** mesa agents — one per named NI operator (Dalradian, Ionic, Wrightbus, Re-Gen, Irish Salt ...) parsed from the register; real-option mining, recycler processors/collectors, downstream + equipment manufacturers, plus geological-potential proxies for uncovered minerals |
| `src/sam_module.py` | builds a balanced NI SAM from the I-O + institutional accounts |
| `src/cge_module.py` | recursive-dynamic CGE (CD value added, Hosoe Armington CES, export demand) + PE fallback |
| `src/spatial_module.py` | allocate sectoral jobs to the 11 NI council areas |
| `src/coupling.py` | annual soft-link loop ABM→MFA→I-O→CGE feedback + spatial + indicators |
| `src/indicators.py` | Minviro validation + Q2.1–2.7 mapping |
| `run_mvm.py` | scenario runner / entry point |
| `q2_1_circularity_interventions.py` | **Q2.1 policy experiment** — tests seven circular-innovation interventions (materials recovery, secondary markets, recycling/collection, circular design, skills) individually + as a package; writes `outputs/q2_1_interventions.csv` and a findings memo `outputs/q2_1_memo.md` |
| `q2_2_opportunities_challenges.py` | **Q2.2 experiment** — mineral-by-mineral opportunity ranking + constraint-relaxation scenarios (permitting, finance, community/social-licence, skills, energy) that identify the binding barrier; writes `outputs/q2_2_opportunity_ranking.csv`, `q2_2_constraint_scenarios.csv`, `q2_2_memo.md` |
| `q_demand_supply_strategy.py` | **Demand & supply analysis** — demand-growth scenarios from UK Vision 2035, the EU CRMA and the UK Industrial Strategy (run to ~2035 then plateau) for the sustainable-mining opportunity, plus a current circular-supply-chain capacity-gap table and a demand-sensitivity sweep; writes `outputs/q_demand_scenarios.csv`, `q_supply_capacity_gap.csv`, `q_demand_sensitivity.csv`, `q_demand_supply_memo.md` |
| `q2_3_business_support.py` | **Q2.3 experiment** — an upstream supply shock (import constraint + price spike) run with stage-targeted government support; reports the supply gap and jobs/GVA by stage (upstream/midstream/downstream/enabling) and the support each stage needs; writes `outputs/q2_3_support_scenarios.csv`, `q2_3_stage_support.csv`, `q2_3_memo.md` |
| `make_plots.py` | static matplotlib figures over the outputs |
| `dashboard.py` | Streamlit interactive dashboard |

## Validation (I-O core vs Minviro)
| | model | Minviro anchor |
|---|---|---|
| One-mine: output / jobs / direct mining GVA | £7.3m / 73 / £1.58m | £7.3m / 73 / £1.6m |
| Two-mine (4b): output / jobs / direct mining GVA | £43.0m / 430 / £9.29m | £43m / 430 / £9.0m |

Note: Minviro's GVA figure is **direct mining GVA**, not economy-wide total — the
model compares like-with-like. The SAM balances to 0.0; the CGE replicates its
benchmark to ~1e-11.

## How outputs map to the seven questions
- **2.1 circularity** — recycling jobs, secondary-material value, critical recycled share over
  time; **`q2_1_circularity_interventions.py` ranks the policy mix** (recovery grants vs R&D
  innovation fund vs collection/DRS vs secondary-market offtake vs design standards vs skills)
  by recycled-share lift, recycling GVA/jobs, circular-design uptake and GVA-ROI. New ABM levers:
  `innovation_grant`, `skills_support`, `secondary_market_support`.
- **2.2 opportunities/challenges** — `q2_2_opportunities_challenges.py` ranks minerals by
  opportunity and runs constraint-relaxation scenarios. Finding: contested critical-mineral
  deposits (Dalradian) are blocked by **social licence, not economics** — a community-benefit
  package is the binding unlock; bulk minerals advance under finance/permitting; critical-mineral
  security is mainly a recycling/feedstock story (little domestic REE/Li/Co/Ni geology)
- **2.3 business support** — `q2_3_business_support.py` runs an upstream supply shock and
  stage-targeted support: the shock opens a critical-mineral supply gap that hits **downstream**
  firms; **midstream** support closes it (recovery capacity), **upstream** support brings domestic
  primary forward, and **downstream** support only pays off once midstream capacity exists
  (sequencing). Plus named-firm installed recycler capacity (tpa)
- **2.4 secure supply** — critical-mineral domestic / recycled / import shares & single-country
  exposure vs Vision 2035 targets (10% domestic, 20% recycling, ≤60% single-country)
- **2.5 employment/regional growth** — total, mining, recycling jobs; **by council area** (spatial shares now blended with the actual named-firm geography), plus named-company context counts
- **2.6 economic benefits** — GVA, output, cumulative discounted GVA; CGE economy-wide wage response; **firm capital-investment pipeline (operating vs proposed)**
- **2.7 negative impacts** — CO₂, PM, cumulative discounted CO₂

## IMPORTANT — data status
- **Real / sourced** (validation & control totals): Minviro scenario anchors, NI mining
  GVA £108m / 1,950 workers, Vision 2035 targets, STPR 3.5%, mining cost of equity 11.26%,
  REE/NdFeB pilot anchors (Ionic Technologies, Belfast).
- **Firm-grounded** (from `company_register.csv`, web/desk-verified): a £1,164m named-firm
  capital pipeline (operating £914m + proposed £250m), Ionic's 400 tpa REE recycling
  capacity (floors recycling-sector output), and firm headcount-by-district that now shapes
  the spatial employment map (mining→Fermanagh & Omagh, manufacturing→Belfast, etc.).
- **Strategy/evidence-grounded** (cited in `data_register.csv`): Vision 2035 Technical Annex
  UK demand signals (Cu 178k→3.6Mt, Li 2.5k→339kt by 2035); 2023 supply concentration
  (REE 74% China, Co 70% DRC, Li 44% Australia → MFA `imp_conc`); ~80% of UK-shredded
  e-/auto-metals exported for processing; NI recycling rate 50.4%; Windsor Framework Art.13(4)
  CRMA applicability; Curraghinalt 3.79 Moz Au + Sb/Te/Bi/Co — per GSNI/BGS *Critical Minerals
  & the Circular Economy in NI* (OR25042, 2025) and the UK/EU strategies.
- **Proxy** (flagged in `data_register.csv`): the I-O coefficient matrix (replace with a
  regionalised NISRA Supply-Use + Scottish 2017 table via FLQ+RAS), SAM sector structure,
  commodity prices, collection/recovery rates, deposit qualities, ABM behavioural
  thresholds, company employment/capacity/feedstock/planning-risk/local-procurement scores,
  CGE elasticities, council-area shares.
- **Gaps** to commission: up-to-date NI I-O/SAM; NI critical-mineral waste flows;
  firm-level local-procurement & skills survey; NISRA BRES employment-by-district.

**The numbers are therefore illustrative of model behaviour, not forecasts.** Swapping
proxies for collected data (same interfaces) turns this into a calibrated tool.
