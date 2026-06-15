# NI Circular Minerals Policy Model

A coupled **ABM × dynamic Input–Output × CGE** simulator of the Northern Ireland
minerals system (primary extraction → use → recycling), built to answer
consultation questions 2.1–2.7. The three tiers from
`../NI_Circular_Minerals_Model_Plan.md` are now all implemented:

- **Tier 1 (MVM)** — ABM → MFA → dynamic I-O, validated against Minviro anchors.
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
| `src/seed_parameters.py` | sectors, minerals, coefficients, real anchors & targets |
| `src/company_data.py` | loads company evidence and turns it into cautious ABM calibration signals for mining risk, recycler capacity, downstream demand, and procurement |
| `src/io_module.py` | dynamic Leontief I-O: Type I/II multipliers, GVA/jobs/CO₂/PM satellites |
| `src/mfa_module.py` | Material Flow Account: stock-flow per mineral, supply shares |
| `src/abm_module.py` | mesa agents: mining (real-option), recyclers, councils, manufacturers; adaptive expectations + imitation |
| `src/sam_module.py` | builds a balanced NI SAM from the I-O + institutional accounts |
| `src/cge_module.py` | recursive-dynamic CGE (CD value added, Hosoe Armington CES, export demand) + PE fallback |
| `src/spatial_module.py` | allocate sectoral jobs to the 11 NI council areas |
| `src/coupling.py` | annual soft-link loop ABM→MFA→I-O→CGE feedback + spatial + indicators |
| `src/indicators.py` | Minviro validation + Q2.1–2.7 mapping |
| `run_mvm.py` | scenario runner / entry point |
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
- **2.1 circularity** — recycling jobs, secondary-material value, critical recycled share over time
- **2.2 opportunities/challenges** — mines opened vs binding constraints in the ABM
- **2.3 business support** — recycling capacity build-out; firm states needing finance/skills
- **2.4 secure supply** — critical-mineral domestic / recycled / import shares & single-country
  exposure vs Vision 2035 targets (10% domestic, 20% recycling, ≤60% single-country)
- **2.5 employment/regional growth** — total, mining, recycling jobs; **by council area** (spatial layer), plus named-company context counts
- **2.6 economic benefits** — GVA, output, cumulative discounted GVA; CGE economy-wide wage response
- **2.7 negative impacts** — CO₂, PM, cumulative discounted CO₂

## IMPORTANT — data status
- **Real / sourced** (validation & control totals): Minviro scenario anchors, NI mining
  GVA £108m / 1,950 workers, Vision 2035 targets, STPR 3.5%, mining cost of equity 11.26%,
  REE/NdFeB pilot anchors (Ionic Technologies, Belfast).
- **Proxy** (flagged in `data_register.csv`): the I-O coefficient matrix (replace with a
  regionalised NISRA Supply-Use + Scottish 2017 table via FLQ+RAS), SAM sector structure,
  commodity prices, collection/recovery rates, deposit qualities, ABM behavioural
  thresholds, company employment/capacity/feedstock/planning-risk/local-procurement scores,
  CGE elasticities, council-area shares.
- **Gaps** to commission: up-to-date NI I-O/SAM; NI critical-mineral waste flows;
  firm-level local-procurement & skills survey; NISRA BRES employment-by-district.

**The numbers are therefore illustrative of model behaviour, not forecasts.** Swapping
proxies for collected data (same interfaces) turns this into a calibrated tool.
