# NI Circular Minerals Policy Model — Technical Documentation

**Version:** June 2026 · **Repository:** `ni-circular-minerals-model` · **Status:** Tier-3 (fully coupled) · validated & CI-checked

This document describes the technical design of the Northern Ireland Circular
Minerals Policy Model, its data sources and provenance, and the assumptions and
limitations behind every component. It is written to be read alongside the code
in `model/src/` and the data in `model/data/`.

> For a 2–3 page non-technical, decision-maker overview of the findings, see
> [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).

> **Headline caveat.** This is a *policy-scenario simulator*, not a forecasting
> tool. Real, sourced anchors are used for validation and control totals; almost
> all economic-structure coefficients and behavioural parameters are **proxy**
> values, flagged as such in `model/data/data_register.csv`. Outputs are
> illustrative of model behaviour and policy direction, not predictions. Swapping
> the proxies for collected data (same interfaces) turns this into a calibrated
> tool — see §8 and §9.

---

## 1. Purpose and scope

The model answers the Department for the Economy (DfE) minerals & circular-economy
consultation questions **2.1–2.7** by simulating the Northern Ireland minerals
system end to end:

```
primary extraction → processing/refining → manufacturing use → in-use stock
   → end-of-life arisings → collection → recovery/recycling → secondary material
   → (imports/exports close the balance)
```

It is built around **circular supply security**, comparing not "mining vs
recycling" but *which mix* of primary extraction, recycling, substitution,
circular design, imports and public support delivers the best balance of
resilience, GVA, employment, environmental protection and community acceptance.

**Horizon:** 30 years (2026–2055), discounted at the **Social Time Preference
Rate of 3.5%** (HM Treasury Green Book / NIGEAE).

---

## 2. Architecture

Three soft-linked engines run on an annual time step, plus a physical backbone and
indicator/spatial layers:

```
            ┌──────────────── SCENARIO / POLICY LEVER LAYER ────────────────┐
            │ grants, permitting, ESG, finance, offtake, collection,        │
            │ procurement, design standards, skills, stockpile, shocks      │
            └───────────────────────────┬───────────────────────────────────┘
                                        │ policy parameters
   ┌────────────────────────────────────▼──────────────────────────────────┐
   │ ABM (abm_module)  — agents = NAMED NI firms                             │
   │  MiningFirm · RecyclerFirm · ManufacturerFirm · GovernmentCollector     │
   │  OUT: new_domestic, recovery_boost, collection_boost, substitution      │
   └───────────────┬───────────────────────────────┬────────────────────────┘
     physical signals│                              │ behaviour ← prices/wages (CGE)
   ┌────────────────▼─────────────┐   ┌─────────────▼──────────────┐
   │ MFA (mfa_module)             │   │ CGE (cge_module) Tier-2/3   │
   │ stock-flow per mineral;      │   │ CES/CD + Armington on the   │
   │ mass balance; supply shares; │   │ NI SAM (sam_module);        │
   │ shocks (import constraint)   │   │ prices, wages, GVA          │
   └────────────────┬─────────────┘   └─────────────┬──────────────┘
   final demand (£m)│                               │ feedback (price, wage)
   ┌────────────────▼──────────────────────────────▼──────────────┐
   │ Dynamic I-O (io_module): GVA, jobs, CO₂, PM; Type I/II;        │
   │ coefficients evolve (recycling substitution, local procurement)│
   └────────────────┬──────────────────────────────────────────────┘
   ┌────────────────▼──────────────┐   ┌────────────────────────────┐
   │ Spatial (spatial_module):     │   │ Indicators (indicators):    │
   │ jobs → 11 council areas       │   │ Q2.1–2.7 + Minviro validation│
   └───────────────────────────────┘   └────────────────────────────┘
```

**Coupling style:** *soft-linking* — sequential, annual, files/objects passed
between modules — not simultaneous solving. This is the debuggable choice and lets
each module be validated independently. The annual loop lives in
`coupling.CoupledModel.run()` (§3.7).

### 2.1 Sectors, minerals and products

| Set | Members |
|---|---|
| **Sectors** (8) | Agriculture, **Mining_Quarrying**, **Recycling_Secondary**, Manufacturing, Energy_Utilities, Construction, Transport_Logistics, Services |
| **Minerals** (10) | REE_magnet, Lithium, Cobalt, Nickel, Copper, Aluminium, Antimony, Baryte, Salt, Zinc |
| **Critical minerals** (7) | REE_magnet, Lithium, Cobalt, Nickel, Copper, Aluminium, Antimony |
| **Products** | EV_battery, Permanent_magnet, Electronics_WEEE, Wind_turbine, Vehicle_ELV, Industrial_equipment |

Recycling_Secondary is split out as its own sector deliberately, so circular
activity is visible in the I-O. Critical minerals are reported separately from
bulk minerals (Salt, Baryte) because tonnage-weighting otherwise lets Salt
dominate the indicators.

---

## 3. Module specifications

### 3.1 Material Flow Account — `mfa_module.py`

Physical backbone. For each mineral *m* and year *t* it tracks a stock-flow account
and checks mass balance. Per-mineral seed parameters: `(demand0, lifetime, coll,
rec, dom0, imp_conc)`.

**Flows (per mineral, per year):**

- End-of-life arisings: `eol = inflow placed on market 'lifetime' years ago`
  (ring buffer `_inflow_hist`).
- Collected: `collected = eol · min(0.95, coll + collection_boost)`
- Recycled (secondary): `recycled = collected · min(0.98, rec + recovery_boost)`;
  `supplied_secondary = min(recycled, demand)`
- Domestic primary: `domestic_primary = demand · min(1, dom0 + new_domestic)`
- Imports close the balance, subject to a shock cap (§3.1.1):
  `remaining = max(0, demand − supplied_secondary − domestic_primary)`
- In-use stock updates by `inflow − eol`, with `inflow = demand − unmet`.

**Mass balance (checked every year, every mineral):**

```
domestic_primary + imports + supplied_secondary + unmet_demand = demand   (±1e-6)
```

**Supply-security indicators** (feed Q2.4 and the Vision-2035 target comparison):
`domestic_share`, `recycled_share`, `import_share`, `supply_gap_share`, and
`single_country_exposure = import_share · imp_conc`.

#### 3.1.1 Upstream supply shock (import constraint)

An optional `import_constraint = {mineral: max import as a fraction of demand}`
models a **dominant-supplier loss** (war / export ban / geopolitical fallout). If
capped imports + domestic + recycled cannot meet demand, the shortfall is recorded
as **`unmet_demand` (the supply gap)** rather than silently imported — this is the
threat that hits downstream firms (§5, Q2.3). Without a shock the cap is absent and
`unmet = 0` (verified).

### 3.2 Agent-Based Model — `abm_module.py`

**The ABM is firm-grounded: every agent is a named NI operator** parsed from
`company_register.csv` (via `company_data.parse_firms`). 21 firms instantiate, plus
geological-potential proxy agents for tracked minerals with no named operator
(Baryte, Aluminium), plus a `GovernmentCollector`. Built on **mesa 3.x**; Tier-1 is
rule-based, Tier-2 adds adaptive expectations and peer imitation.

**MiningFirm** — real-option development decision each year:

```
eff_wacc       = WACC · (1 − 0.5·finance_support)                 # WACC = 0.1126
deposit_quality= clip((0.65·resource + 0.35·capacity)·confidence, 0, 1)
margin         = deposit_quality·price_signal + exploration_grant + 0.05·skills
                 − esg_cost − 0.12·project_risk − eff_wacc
social_licence = 0.6 − 0.5·esg_cost − 0.25·project_risk + 0.30·community_benefit
develop if  margin > dev_hurdle (0.45)  AND  social_licence > 0.4
permit delay = max(1, permit_years) + round(3·project_risk·(1 − 0.5·skills))
```

`price_signal` uses adaptive expectations when `adaptive=True`. Operating assets
(e.g. Irish Salt) supply immediately; proposed/exploration projects must clear the
hurdle **and** the social-licence floor — so the best deposit (Dalradian, high
planning-risk) can stay blocked unless a community-benefit package lifts its social
licence (the central Q2.2 finding).

**RecyclerFirm** — processor (e.g. Ionic → REE recovery capacity) or feedstock
collector (Re-Gen, RiverRidge, Bryson → WEEE/ELV collection):

```
viability = recycling_grant + recycled_content_procurement + 0.5·secondary_market
            + (price − 1) − 0.3·(energy_cost_index − 1) + 0.08·(capacity_signal − 0.5)
            + 0.04·equipment_support + 0.15·innovation_grant (+0.05 if plant exists)
gain      = min(0.06, 0.06·viability·(0.75 + capacity_signal)·(1 + 0.3·skills))
recovery_boost[m] += gain (+0.02·innovation_grant for process-yield gains)
```

**ManufacturerFirm** — downstream demand + recycled-content uptake (drives the I-O
mining→recycling coefficient shift); supply-chain firms (CDE, Terex) provide static
`equipment_support` that eases recycler capex:

```
ceiling = min(0.85, circularity + 0.15·innovation_grant + 0.05·secondary_market)
uptake  = min(ceiling, uptake + 0.5·avail·circularity + 0.05·push·circularity
              + 0.04·innovation·circ + 0.03·skills·circ + 0.05·market·circ)
```

**GovernmentCollector** — policy-driven municipal collection across critical
minerals under `collection_infrastructure` / `product_passport`.

The model emits a `signals` dict each step (`new_domestic`, `recovery_boost`,
`collection_boost`, `recycling_substitution`, plus firm-context aggregates) which
the coupling layer reads. CGE feedback sets `dev_hurdle = 0.45·wage` and feeds a
mineral price signal back to mining decisions (Tier-3 loop).

### 3.3 Dynamic Input-Output — `io_module.py`

Leontief production accounting with dynamic coefficients.

- **Leontief inverse:** `L = (I − A)⁻¹`. `A` is the 8×8 proxy technical-coefficient
  matrix scaled by `DOMESTIC_INTENSITY = 0.62` (high import leakage of a small open
  region).
- **Type I** multipliers (direct + indirect) from `L`.
- **Type II** (direct + indirect + induced) via a **closed model** — augment `A`
  with a household row (income = `gva_coeff·WAGE_SHARE_OF_GVA`, 0.55) and column
  (consumption = `HH_CONSUMPTION·LOCAL_CONSUMPTION_PROPENSITY`, 0.42).
- **Satellite accounts** (per £m output): GVA, employment (jobs/£m), CO₂ (ktCO₂e),
  PM (t). Impact of a final-demand vector `fd`: `x = L·fd`; multiply by satellites.
- **Dynamic coefficients** (`update_coefficients`, driven by ABM each year):
  recycling substitution shifts `A[mine,man] → A[rec,man]`; local-procurement gain
  reduces mining import share (raising multipliers); a small productivity gain
  shrinks all coefficients.

Calibrated so a mining demand shock yields ~10 total jobs/£m and a Type-II mining
output multiplier of ~1.69 (verified in range 1.3–2.2).

### 3.4 Social Accounting Matrix — `sam_module.py`

NI has no published SAM, so one is **constructed** and balances by construction
(Walras): structural flows set first; imports, taxes and foreign savings are
residuals.

- **Control total:** total NI GVA ≈ £40,000m, pinned by the **real mining anchor**
  (£108m = 0.27% of regional GVA). Sector GVA shares are proxy NI structure.
- Output `= gva / GVA_COEFF`; intermediate flows `Z = A·output`; imported
  intermediates are the activity-column residual.
- Factor split: labour 60% / capital 40% of VA. Institutional closure: household
  savings 10%, government demand share 18%, export intensities per sector.
- Verified: **row sums = column sums to ~1e-12**, and it reproduces the £108m
  mining-GVA anchor.

### 3.5 Computable General Equilibrium — `cge_module.py`

Compact recursive-dynamic, single-region open economy, calibrated to the NI SAM.

- **Value added:** Cobb-Douglas in capital & labour (calibrated so `VA0 = L0 + K0`
  replicates the benchmark exactly; labour cost share `alphaL = L0/(L0+K0)`).
- **Armington** CES (Hosoe form) domestic vs imported per commodity, **σ_arm =
  2.0**.
- **Households:** Cobb-Douglas demand; fixed real government & investment.
- **Exports:** constant-elasticity demand falling in domestic price, **σ_e = 2.0**.
- **Closure:** flexible wage & capital rental clear factor markets; fixed factor
  supplies; numeraire = world price = 1.
- Solved with `scipy.optimize.root` (hybr). **Benchmark replication:** all excess
  demands ≈ 0 at base prices (wage = 1.000). A partial-equilibrium fallback
  (`PEPriceLabour`) is provided. (Declared `SIGMA_VA = 0.8` is retained as a
  parameter; the calibrated VA nest is Cobb-Douglas for exact benchmark
  replication.)

**Feedback to ABM (Tier-3):** the relative mining price `PD[mine]` (clipped 0.8–1.5)
feeds next year's mineral price index; the wage index raises the mining
development hurdle (labour scarcity).

### 3.6 Spatial layer — `spatial_module.py`

Allocates sectoral employment to the **11 NI Local Government Districts**. Base
shares follow population, tilted by sector. For the three minerals-relevant sectors
(Mining_Quarrying, Recycling_Secondary, Manufacturing) the proxy shares are
**blended 50/50 with the actual named-firm geography** (confidence- and
lifecycle-weighted firm headcount by district) — so mining concentrates in
Fermanagh & Omagh (Dalradian/Mannok), manufacturing in Belfast (Spirit/H&W) and
Mid & East Antrim (Wrightbus), etc. District shares sum to 1 per sector (verified).

### 3.7 Coupling loop — `coupling.py`

`CoupledModel.run()` executes the annual soft-link for `t = 0 … horizon-1`:

1. Price index `= (1 + price_path)^t · cge_feedback_price`; passed to ABM.
2. **ABM step** → `signals` (decisions).
3. **Strategic stockpile drawdown** (§5): a finite reserve tops up the import cap
   each shock year until depleted.
4. **MFA step** with demand multiplier (incl. plateau), collection/recovery boosts,
   new domestic supply, and the effective import constraint → physical flows.
5. **Dynamic I-O coefficient update** from ABM signals.
6. Convert physical flows to a final-demand vector (£m, priced); apply a
   **firm-grounded recycling-output floor** (Ionic's installed capacity); compute
   impacts (GVA, jobs, CO₂, PM).
7. **CGE solve** (if enabled) → wage, GVA; feedback to ABM.
8. Spatial allocation of jobs; discount by STPR; record annual row.

Demand growth optionally **plateaus** after a given year (`demand_plateau_years`,
e.g. 9 → demand grows to ~2035 then holds) so document-anchored CAGRs do not
compound unrealistically over 30 years.

### 3.8 Indicators & validation — `indicators.py`

Maps the time series to the seven consultation questions (§5) and validates the I-O
core against the Minviro anchors by injecting a mining final-demand shock sized to
hit Minviro's one-mine (£7.3m) and two-mine (£43m) total output, then comparing
jobs and **direct** mining GVA (like-with-like; Minviro's GVA is direct, not
economy-wide).

---

## 4. Policy levers

Every lever maps to a **named real-world instrument**. Default 0 (so the baseline
is undisturbed).

| Lever | Range | Acts on | Named instrument |
|---|---|---|---|
| `exploration_grant` | 0–~0.2 | mining margin | exploration support |
| `finance_support` | 0–1 | mining cost of capital | **NWF + UKEF** |
| `permit_years` | yrs | mining delay | **EA priority-tracked service** |
| `community_benefit` | 0–1 | social licence | community-benefit/ESG scheme |
| `esg_cost` | 0–~0.2 | margin & licence | ESG/compliance cost |
| `recycling_grant` | 0–1 | recycler viability | capital recovery grants (Vision 2035 DBT) |
| `innovation_grant` | 0–1 | recovery yield + design | **CLIMATES £15m + Faraday/ReLiB £34m** |
| `energy_cost_index` | ~0.9–1.1 | recycler viability | **BICS** energy support |
| `secondary_market_support` | 0–1 | recycler + manufacturer | **UKEF offtake + price floor** (cf. MP Materials) |
| `collection_infrastructure` | 0–1 | collection rates | WEEE/**DRS** |
| `product_passport` | 0–1 | collection + design | digital passports / EPR |
| `recycled_content_procurement` | 0–1 | substitution | minimum recycled-content procurement |
| `design_standards` | 0–1 | substitution | ecodesign / design-for-disassembly |
| `local_supplier_support` | 0–1 | I-O local procurement | supplier development (Invest NI) |
| `skills_support` | 0–1 | capacity build + mining | **Skills England + DWP** |
| `strategic_stockpile` | 0–1 | import buffer | **defence stockpile** (Japan/Korea practice) |
| `diversification` | 0–1 | single-country concentration | **international partnerships** (Vision 2035) — cuts effective `imp_conc` up to 50% |

The upstream **supply shock** itself (not a lever) is an `import_constraint` —
either a static `{mineral: cap}` or a **callable `f(t)`** for time-varying shocks
with an onset year (used by the Q2.4 Monte-Carlo). Caps are set to
`1 − loss_factor·(single-country concentration)`.

---

## 5. Consultation-question experiments

Each is a standalone script writing CSVs + a findings memo to `model/outputs/`, and
a tab in the Streamlit app.

| Q | Script | What it does |
|---|---|---|
| **2.1 Circularity innovation** | `q2_1_circularity_interventions.py` | 7 interventions (materials recovery, secondary markets, recycling/collection, circular design, skills) individually + as a package; ranks by recycled-share lift, recycling GVA/jobs, circular-design uptake and **GVA-ROI with a cost-uncertainty band** |
| **2.2 Opportunities & challenges** | `q2_2_opportunities_challenges.py` | mineral-by-mineral opportunity ranking + **constraint-relaxation scenarios** (permitting, finance, community/social-licence, skills, energy) → the **binding constraint is social licence** |
| **2.3 Business support** | `q2_3_business_support.py` | **dominant-supplier shock** (per-mineral caps = 1 − concentration) + price spike; stage-targeted support (upstream/midstream/downstream/enabling); **finite, depleting stockpile**; severity sweep; per-mineral exposure |
| **2.4 Secure supply** | `q2_4_secure_supply.py` | **geopolitical shocks** (escalating dominant-supplier export ban; caps = 1 − concentration) × five government **roles**; **Monte-Carlo** over uncertain shocks (random onset/minerals/severity) → resilience distribution + HHI-style supply-risk index vs Vision-2035 targets → the **strategic-coordinator/insurer** role is most robust |
| **Demand & supply** | `q_demand_supply_strategy.py` | demand scenarios from Vision 2035, EU CRMA and the UK Industrial Strategy (annex-derived CAGRs, plateau at 2035); circular-supply-chain **capacity-gap** analysis; **±50% demand sensitivity** |

**The strategic stockpile** (Q2.3) is a finite reserve sized to real targets
(Japan/JOGMEC 60–180 days, Korea/KOMIR 100 days): `STOCKPILE_DEPTH = 0.5`
demand-years (~180 days) drawn down at up to `STOCKPILE_RATE = 0.30` of demand per
shock year → ~1.5–2 years of cover, then it depletes and the gap reopens. So it is
a *bridge, not a fix*.

---

## 6. Data sources & provenance

Every parameter carries a status in `model/data/data_register.csv`:
🟢 **real** (sourced/audited) · 🟡 **proxy** (desk/scaled) · 🔴 **gap** (placeholder).

### 6.1 Real anchors and control totals (used for validation)

| Item | Value | Source |
|---|---|---|
| NI mining & quarrying GVA (2018) | £108m (0.27% of NI GVA) | ONS Regional GVA / NISRA via Minviro |
| NI mining & quarrying workers | 1,950 | NISRA BRES |
| NI total employee jobs (Sep 2023) | 816,562 | NISRA BRES |
| Minviro one-mine scenario | 73 jobs / £7.3m output / £1.6m GVA p.a. | Minviro Final Report |
| Minviro two-mine (4b) scenario | 430 jobs / £43m output / £9m GVA p.a. | Minviro Final Report |
| STPR (discount rate) | 3.5% | Green Book / NIGEAE |
| Mining cost of equity (WACC) | 11.26% | Minviro (CAPM) |
| Vision 2035 targets (2035) | 10% domestic / 20% recycling / ≤60% single-country | Vision 2035 (GOV.UK) |
| BGS 2024 Criticality Assessment | 82 candidates → 34 critical | BGS/CMIC |
| GSNI Tellus | 55 elements geochemical baseline | GSNI |

### 6.2 Strategy-grounded demand & policy data

| Item | Value | Source |
|---|---|---|
| UK growth-sector demand (Cu/Li/Co/Ni…) 2024–2035 | annex Annex-2 cumulative tonnes | **Vision 2035 Technical Annex** |
| Annex-derived annual demand CAGRs | Li 26.5%, Ni 10.8%, Al 9.3%, Co 9.2%, REE 8.8%, Cu 4.3% | derived from Annex 2 (cumulative → annual increment → CAGR), IEA-cross-checked |
| IEA net-zero demand | Cu/Co/REE/Ni ~2× by 2040; Li ~9× | IEA via GSNI OR25042 |
| 2023 single-country supply concentration | REE 74% China, Co 70% DRC, Li 44% Australia | BGS/Idoine et al. 2025 |
| UK metals exported for processing | ~80% | GSNI/BGS OR25042 |
| NI municipal recycling rate (2024/25) | 50.4% (household 51%) | DAERA LAC municipal waste |
| Windsor Framework CRMA applicability | Art. 13(4) | DBT Explanatory Memorandum (Apr 2025) |
| Curraghinalt (Dalradian) resource | 3.79 Moz Au M&I (+Cu/Sb/Te/Bi/Co) | Dalradian 2021 feasibility study |
| Belfast Harbour throughput (2024) | 24.1 Mt | Belfast Harbour via OR25042 |

### 6.3 Support-mechanism evidence (Q2.3)

| Item | Value | Source |
|---|---|---|
| Strategic-stockpile targets | Japan 60–180 days, Korea 100 days | IEA; CSEP 2025 |
| FOAK cost-share (pilot→commercial) | 20% prototype / 50% pilot | US DOE Critical Minerals Accelerator |
| Blended finance fund | US$500m | US–Australia Critical Minerals Partnership Fund |
| Offtake + price floor | 10-yr / $110/kg NdPr | US DoD–MP Materials (CSIS 2025) |
| EU CRMA strategic-project package | 15-mo processing / 27-mo extraction permits + finance + offtake | European Commission |
| Lever public costs (NI-scale £m/yr) | CLIMATES £15m, ReLiB £34m, DBT £50m, DEFRA DRS £632m/£1.065bn, bootcamps ~£3,152/learner | Innovate UK / DEFRA / DfE |

### 6.4 Firm evidence — `company_register.csv`

21 named NI operators across stages, web/desk-verified, with role, district,
lifecycle, employees, investment, capacity and 0–1 scores (resource, capacity,
feedstock, demand, local-procurement, planning-risk, skills, circularity). Examples:
**Ionic Technologies** (Belfast, 400 tpa REE recovery), **Plaswire** (Lurgan,
turbine-blade composites), **Dalradian/Curraghinalt**, **Wrightbus, Seagate,
Encirc, Spirit, Harland & Wolff**, **CDE, Terex**, Re-Gen/RiverRidge/Bryson. Derived
aggregates: £1,164m named-firm capital pipeline; 400 tpa installed REE recovery.

### 6.5 Source documents

UK Critical Minerals Strategy *Vision 2035* (DBT) and its *Technical Annex*; UK
*Modern Industrial Strategy* (2025); EU *Critical Raw Materials Act* (2024); GSNI/BGS
*Critical Minerals and the Circular Economy in NI* (OR25042, 2025); *Minviro Final
Minerals Research Report* + Appendix A; BGS UK 2024 Criticality Assessment; DAERA,
NISRA, GSNI Tellus, IEA, Met4Tech/Faraday, and the cited US/EU policy analyses.

---

## 7. Key parameters & calibration (selected)

| Parameter | Value | Status |
|---|---|---|
| `DOMESTIC_INTENSITY` (A scaling) | 0.62 | proxy (import leakage of a small open region) |
| `GVA_COEFF` (mining) | 0.35 | proxy, tuned to Minviro direct-GVA anchors |
| `EMP_COEFF` (mining) | 11.5 jobs/£m | proxy, anchored to 1,950 jobs / GVA |
| `WAGE_SHARE_OF_GVA` / `LOCAL_CONSUMPTION_PROPENSITY` | 0.55 / 0.42 | proxy (Type-II induced) |
| Recovery yields REE/Li/Cu | 0.85 / 0.50 / 0.90 | desk-verified (Met4Tech, ReLiB, Ionic) |
| WEEE collection baseline | 0.25 | desk-verified (UN Global E-waste Monitor) |
| Concentration `imp_conc` REE/Co/Li | 0.74 / 0.70 / 0.44 | real (BGS/Idoine 2025) |
| Dev hurdle / social-licence floor | 0.45 / 0.40 | **proxy** behavioural thresholds |
| CES elasticities σ_arm / σ_e | 2.0 / 2.0 | proxy |
| Stockpile depth / rate | 0.5 demand-yr (~180 d) / 0.30 | calibrated to JOGMEC/KOMIR |

---

## 8. Assumptions and limitations

**Structural / economic**
1. **The I-O coefficient matrix is proxy**, not a regionalised NI table. It is
   scaled for high import leakage and tuned to the Minviro mining anchors. *Replace
   with NISRA Supply-Use + Scottish 2017 I-O via FLQ + RAS.* This is the single
   biggest calibration dependency.
2. **The SAM structure is proxy** (only mining GVA is a real anchor); the CGE is a
   compact reduced-form, not a full intertemporal optimisation. CGE elasticities
   are proxy.
3. Multipliers, GVA/output ratios and jobs/£m are calibrated to land in realistic
   ranges (Type-II output ~1.4–1.8) but are not measured.

**Material-flow / circular**
4. MFA stock-flow seeds (demand, lifetimes, collection, recovery, domestic share)
   are **UK data scaled to NI** — NI-level critical-mineral waste flows are a known
   gap. Commodity prices are indicative, not market series.
5. Recovery yields are *process* yields; the binding constraint is *collection*
   (feedstock), reflecting the reality that only ~1% of REE demand is met from
   recycling.

**Behavioural / ABM**
6. Agent decision rules are deliberately simple (real-option NPV trigger, viability
   scores). **Behavioural thresholds (dev hurdle, social-licence floor, risk→delay,
   lever→effect coefficients) are proxy** and are what determine which marginal
   projects open — the first thing to calibrate with planning/licensing and firm
   survey data.
7. Firm scores (capacity/feedstock/planning-risk/local-procurement/circularity) are
   desk estimates; Plaswire's role is verified but several firms need facility-level
   confirmation.

**Demand & shock**
8. Demand CAGRs are **UK-national figures scaled uniformly to NI's base**; a true NI
   demand series needs NI-specific sector activity (not yet public). The annex
   figures are read as *cumulative* demand (reconciled against the aluminium total
   and IEA); this interpretation, while well-supported, is not stated outright in
   the PDF.
9. The supply shock is modelled as a sustained import constraint from year 0 (not a
   discrete event) plus a price spike; the strategic stockpile draws down at the
   release rate during shock years (a slight over-depletion if the annual gap is
   smaller than the release).

**Spatial / environmental**
10. District allocation blends proxy population-tilted shares with named-firm
    geography — *replace with NISRA BRES employment-by-district.*
11. Environmental satellites (CO₂, PM) are proxy coefficients — *replace with
    NAEI/DAERA + ecoinvent/EXIOBASE.* The model does **not** do site-specific
    impact assessment (Q2.7 should be read with the Minviro Appendix A, which
    stresses impacts are site-specific).

**Public cost / ROI**
12. Lever public costs and the GVA-ROI are NI-scale figures **benchmarked to UK
    programmes by population**, used only for *relative* ranking — not budget lines.
    A ±cost band is provided for sensitivity.

---

## 9. Validation, verification & CI

- **Validation** against Minviro anchors (`indicators.validate_against_minviro`):
  one-mine 7.3/73.1/£1.58m and two-mine 43.0/430.4/£9.29m — all within tolerance.
- **Verification harness** (`verify_model.py`): **50 checks** — *invariant*: MFA mass
  balance (baseline + shock), supply-share bounds/closure, no NaN/negatives,
  determinism, SAM balance (~1e-12) + mining-GVA anchor, CGE benchmark replication
  (wage = 1.000), spatial share closure, stockpile reserve non-negativity/depletion,
  register integrity, economic-sanity ranges, geopolitical features (diversification,
  time-varying shock); plus **property-based/fuzz** — 30 random valid policy bundles
  (random lever subsets, demand growth, static/time-varying shocks, plateau, CGE
  on/off) must all preserve mass balance, share closure, no NaN/negatives and a
  non-negative reserve. **All 50 pass.**
- **Continuous integration** (`.github/workflows/verify.yml`): every push/PR
  installs dependencies, runs `run_mvm.py`, runs `verify_model.py` (gates the
  build) and smoke-tests all experiments. The model is **deterministic** (identical
  config → byte-identical output; idempotent price/parameter overrides).

---

## 10. Reproducibility

```bash
cd model
pip install -r requirements.txt          # numpy, pandas, mesa, networkx, scipy, matplotlib, streamlit
python run_mvm.py                         # 6 scenario families → outputs/
python verify_model.py                    # 50 invariant + property-based checks
python q2_1_circularity_interventions.py  # Q2.1
python q2_2_opportunities_challenges.py   # Q2.2
python q2_3_business_support.py           # Q2.3
python q_demand_supply_strategy.py        # demand & supply
python make_plots.py                      # figures
streamlit run ../streamlit_app.py         # interactive dashboard
```

Environment: Python ≥ 3.11 (CI uses 3.12). Outputs are committed and deterministic.

---

## 11. File map

| File | Role |
|---|---|
| `src/seed_parameters.py` | sectors, minerals, proxy coefficients, real anchors/targets (read from the data register) |
| `src/data_register.py` | loads `data_register.csv` as the single source of truth |
| `src/company_data.py` | parses the firm register → ABM signals + stage/spatial aggregates |
| `src/mfa_module.py` | Material Flow Account (stock-flow, mass balance, shocks) |
| `src/io_module.py` | dynamic Leontief I-O (Type I/II, satellites) |
| `src/abm_module.py` | firm-grounded mesa agents |
| `src/sam_module.py` | balanced NI SAM builder |
| `src/cge_module.py` | recursive-dynamic CGE (+ PE fallback) |
| `src/spatial_module.py` | jobs → 11 council areas (firm-blended) |
| `src/coupling.py` | annual ABM→MFA→I-O→CGE soft-link |
| `src/indicators.py` | Minviro validation + Q2.1–2.7 mapping |
| `data/company_register.csv` | 21 named NI firms + scores |
| `data/data_register.csv` | every parameter → value → source → status |
| `data/ree_pilot.py` | REE/NdFeB magnet pilot thread |
| `run_mvm.py` · `q2_*.py` · `q_demand_supply_strategy.py` | entry points / experiments |
| `verify_model.py` | verification & validation harness |
| `make_plots.py` · `dashboard.py` · `../streamlit_app.py` | figures & dashboard |

---

*Prepared as evidence supporting DfE minerals & circular-economy policy. All figures
are model behaviour under stated assumptions, not forecasts. See
`data/data_register.csv` for parameter-level provenance and status.*
