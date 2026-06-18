# Northern Ireland Circular Minerals Model — Technical Report

**Subject:** the model, methodology, mathematical specification, data and assumptions of the integrated Agent-Based × dynamic Input–Output × Computable General Equilibrium (CGE) model of the Northern Ireland minerals system (consultation questions 2.1–2.7).
**Status:** Tier-3 (fully coupled), calibrated to the Minviro anchors and the NI baseline, CI-checked (61-check verification harness).

> **Status of figures.** This is a *policy-scenario simulator*, not a forecasting tool. Real, sourced anchors are used for validation and control totals; most economic-structure coefficients and behavioural thresholds are **proxy** values, flagged in `model/data/data_register.csv`. Every quantity is model behaviour under stated assumptions — not a prediction. The *equations below are the permanent mathematical structure*; swapping the proxy coefficients for collected NI data (same equations) turns the model into a calibrated tool.

---

## 1. Methodology and model overview

The model simulates the NI minerals system end to end — primary extraction → processing/refining → manufacturing use → in-use stock → end-of-life → collection → recovery → secondary material, with imports/exports closing the balance — and compares **which mix** of extraction, recycling, substitution, circular design, imports and public support best balances supply resilience, GVA, employment, environmental protection and community acceptance.

**Coupling.** Four engines are **soft-linked** — solved sequentially on an annual time step `t = 0,…,T−1` (`T = 30`, 2026–2055), passing objects between them — rather than simultaneously. Soft-linking is the debuggable, independently-validatable choice and keeps each module's mathematics standard:

```
 policy levers θ  ─►  ABM (firm decisions)  ─►  signals s_t
                              │                     │
        price/wage feedback ◄─┘                     ▼
                              MFA (physical stock-flow, mass balance, shocks)
                                          │ final-demand vector f_t (£m)
                                          ▼
                        dynamic Leontief I-O  ─►  GVA, jobs, CO₂, PM
                                          │
                                          ▼
                       CGE on the NI SAM  ─►  prices PD, wage w  ─►  (feedback to ABM)
                                          │
                                          ▼
                  spatial allocation (11 councils) + indicators (Q2.1–2.7)
```

**Discounting.** All cumulative monetary/employment/emission quantities use the HM Treasury / NIGEAE Social Time Preference Rate `δ = 3.5%`:

```
PV = Σ_{t=0}^{T−1}  x_t / (1 + δ)^t ,    δ = 0.035 ,  T = 30
```

---

## 2. Sets and notation

| Symbol | Meaning |
|---|---|
| `i, j ∈ {1,…,N}` | economic sectors, `N = 8` (Agriculture, Mining_Quarrying, Recycling_Secondary, Manufacturing, Energy_Utilities, Construction, Transport_Logistics, Services) |
| `m ∈ M` | minerals, `|M| = 10` (REE_magnet, Lithium, Cobalt, Nickel, Copper, Aluminium, Antimony, Baryte, Salt, Zinc) |
| `M_c ⊂ M` | critical-mineral subset (REE, Li, Co, Ni, Cu, Al, Sb); copper is a UK *growth* (not critical) mineral and is reported separately |
| `t` | year index, `0,…,T−1` |
| `θ` | policy-lever vector (16 levers, default 0) |
| `A = [a_ij]` | I-O technical-coefficient matrix (input i per unit output j) |
| `L = (I−A)⁻¹` | Leontief inverse |

---

## 3. Mathematical specification

### 3.1 Material Flow Account (MFA) — physical backbone

For each mineral `m`, per-mineral seed parameters are `(D⁰_m, life_m, coll_m, rec_m, dom0_m, κ_m)` = (baseline demand, product lifetime, collection rate, recovery yield, domestic-primary share, single-country import concentration). Demand grows with an optional CAGR `g_m` (with a plateau year `t̄`) and a firm-derived downstream signal `φ`:

```
D_{m,t} = D⁰_m · φ · (1 + g_m)^min(t, t̄)
```

**Annual flows** (Δ· are ABM boosts; `Lᵐ = life_m`):

```
eol_{m,t}      = inflow_{m, t−Lᵐ}                                  end-of-life arisings (ring buffer)
c_rate         = min(0.95, coll_m + Δcoll_{m,t}) ,  capped at 0.25 for WEEE-stream {REE,Li,Co}
collected      = eol_{m,t} · c_rate
recycled       = collected · min(0.98, rec_m + Δrec_{m,t})
dom_{m,t}      = D_{m,t} · min(1, dom0_m + Δdom_{m,t})              domestic primary (allocated first)
sec_{m,t}      = min(recycled, max(0, D_{m,t} − dom_{m,t}))         secondary supply
remaining      = max(0, D_{m,t} − dom_{m,t} − sec_{m,t})
imports_{m,t}  = min(remaining, cap_{m,t} · D_{m,t})               cap_{m,t} = shock; else +∞
unmet_{m,t}    = remaining − imports_{m,t}                          supply gap (hits downstream)
```

**Mass-balance identity** — checked for every `(m,t)` (tolerance 1e-6):

```
dom_{m,t} + imports_{m,t} + sec_{m,t} + unmet_{m,t} = D_{m,t}
```

**Supply-security indicators** (shares of demand) and the **concentration-risk metrics**:

```
domestic_share = dom/D ,  recycled_share = sec/D ,  import_share = imports/D ,  gap_share = unmet/D
single_country_exposure   = import_share · κ_m · (1 − 0.45·diversification)
top3_exposure             = import_share · κ³_m · (1 − 0.20·diversification)      (IEA 2025)
refining_exposure         = import_share · κʳ_m                                   (not cut by diversification)
```

where `κ³_m` (top-three producer share, IEA ≈ 86% for key minerals) and `κʳ_m` (refining/processing share, China ≈ 70% for 19/20) are per-mineral vectors. The diversification lever reduces single-country exposure up to 45% (calibrated to Japan's post-2010 ~90%→~58% cut) and top-three up to 20%; **refining exposure falls only as the import share itself falls** (i.e. only by building domestic recovery/processing capacity) — the model's formal statement that the security problem is midstream.

**Upstream shock.** `cap_{m,t}` is either a static dict `{m: cap}` or a callable `f(t)` (time-varying onset), with `cap_{m} = 1 − loss · κ_m` (a dominant-supplier export ban). A **strategic stockpile** is a finite reserve `R_m = ρ·STOCKPILE_DEPTH` (ρ = lever, DEPTH = 0.5 demand-years ≈ 180 days) drawn down at ≤ `STOCKPILE_RATE·ρ` (RATE = 0.30) of demand per shock year until exhausted — a bridge, not a fix.

### 3.2 Agent-Based Model (ABM) — firm-grounded (mesa 3.x)

Each agent is a named NI firm with attributes (scores `s` ∈ [0,1], lifecycle, employees, capacity). Expectations are adaptive: `p̂_t = λ·p_t + (1−λ)·p̂_{t−1}`, `λ = 0.5`.

**MiningFirm — real-option development trigger.** A proposed deposit develops only if its margin clears the development hurdle **and** social licence clears the floor:

```
deposit_quality q = clip( (0.65·resource + 0.35·capacity) · confidence , 0, 1 )
eff_wacc          = WACC · (1 − 0.5·finance_support) ,        WACC = 0.1126
margin            = q·p̂  + exploration_grant + 0.05·skills − esg_cost − 0.12·project_risk − eff_wacc
social_licence    = 0.6 − 0.5·esg_cost − 0.25·project_risk + 0.30·community_benefit

develop  ⇔  margin > h  AND  social_licence > 0.4 ,           h = dev_hurdle = 0.45 (× CGE wage)
permit delay (yrs) = max(1, permit_years) + round( 3·project_risk·(1 − 0.5·skills) )
```

On development the firm adds `output_share = clip(0.05 + 0.13·capacity, 0.03, 0.18)` to domestic supply `Δdom_m`. Operating sites supply immediately; contested high-risk deposits (e.g. Dalradian) stay blocked unless `community_benefit` lifts social licence above 0.4 — the central Q2.2 mechanism.

**RecyclerFirm — processor (recovery) or collector (feedstock).** For a processor with target minerals `T`:

```
viability = recycling_grant + recycled_content_procurement + 0.5·secondary_market_support
            + (mean_{m∈T} p_m − 1) − 0.3·(energy_cost_index − 1)
            + 0.08·(capacity_signal − 0.5) + 0.04·equipment_support + 0.15·innovation_grant
            (+0.05 if an installed plant exists, e.g. Ionic 400 tpa)
if viability > 0.05:
    gain        = min(0.06, 0.06·viability·(0.75 + capacity_signal)·(1 + 0.3·skills))
    Δrec_m     += gain (+ 0.02·innovation_grant for process-yield gains),  capped at 0.35
```

A collector raises `Δcoll_m += 0.008·feedstock + 0.02·(collection_infrastructure + product_passport)·(0.5 + feedstock)`, capped at 0.50.

**ManufacturerFirm — recycled-content uptake** (drives the I-O mining→recycling coefficient shift):

```
ceiling = min(0.85, circularity + 0.15·innovation_grant + 0.05·secondary_market_support)
rate    = circularity·( 0.5·avail + 0.05·(design_standards+procurement) + 0.04·innovation
                        + 0.03·skills + 0.05·secondary_market )
uptake  = min(ceiling, uptake + rate)
```

with `avail = mean_{m∈M_c} Δrec_m`. The economy-wide **recycling-substitution signal** is the employment-weighted mean of firm uptake, `Σ uptake·wₖ / Σ wₖ`, `wₖ = ln(1+employeesₖ)`.

### 3.3 Dynamic Leontief Input–Output

`A` is the 8×8 proxy coefficient matrix scaled by `DOMESTIC_INTENSITY = 0.62` (high import leakage of a small open region). Production and impacts:

```
Type-I output:     x = L · f ,   L = (I − A)⁻¹
Satellites:        GVA = ĝ ⊙ x ,  jobs = ê ⊙ x ,  CO₂ = ĉ ⊙ x ,  PM = p̂ ⊙ x      (⊙ = elementwise)
```

**Type-II (induced)** effects via a *closed* model — augment `A` with a household row (income = wage share of GVA) and column (local consumption):

```
        ⎡ A          h_c ⎤             h_c[i] = HH_CONSUMPTION_i · LOCAL_CONSUMPTION_PROPENSITY (0.42)
A_c =   ⎢                ⎥ ,           h_r[j] = ĝ_j · WAGE_SHARE_OF_GVA (0.55)
        ⎣ h_r        0   ⎦
x_ext = (I − A_c)⁻¹ · [f ; 0] ,   output = x_ext[1:N]
```

Output multipliers are column sums of `L` (Type I) and of the closed inverse (Type II). Calibrated so a mining demand shock yields ≈ 10 total jobs/£m and a Type-II mining output multiplier ≈ 1.69 (verified in 1.3–2.2).

**Dynamic coefficients** (updated each year from ABM signals): recycling substitution shifts manufacturing's mining input to recycling, `a_{mine,man} −= σ·a_{mine,man}`, `a_{rec,man} += σ·a_{mine,man}`; local-procurement gain lowers mining import share; a small productivity gain shrinks all `a_ij`; `A` clipped to [0, 0.95].

### 3.4 Social Accounting Matrix (SAM)

NI has no published SAM, so one is **constructed** and balances by construction (Walras). The control total is pinned by the **real mining anchor** (£108m = 0.27% of NI GVA ⇒ total ≈ £40,000m):

```
GVA_i      = share_i · 40000 ,        share_{mining} = 0.0027 (real); others proxy NI structure
output_i   = GVA_i / ĝ_i
Z          = A ⊙ output (column-broadcast)                     domestic intermediate flows
imp_int_j  = max(0, output_j − Σ_i Z_ij − GVA_j)               imported intermediates (activity residual)
labour_i   = 0.60·GVA_i ,  capital_i = 0.40·GVA_i
exports_i  = ξ_i · output_i
base_fd_i  = max(0, output_i − Σ_j Z_ij − exports_i)
gov_i      = 0.18·base_fd_i ,  invest_i = 0.10·base_fd_i ,  household_i = base_fd_i − gov_i − invest_i
imp_com_i  = max(0, (Σ_j Z_ij + household + gov + invest) − (output_i − exports_i))   commodity residual
```

Institutional accounts close as residuals (direct tax = HH residual; gov savings = gov residual; foreign savings = capital residual), so **row sums = column sums** to ~1e-12 (verified), and the matrix reproduces the £108m mining-GVA anchor.

### 3.5 Computable General Equilibrium (CGE)

A compact recursive-dynamic, single-region open economy calibrated to the SAM. Unknowns: domestic prices `PD_i`, activity levels `X_i`, wage `w`, capital rental `r`. Numeraire: world price = exchange rate = 1.

**Value added — Cobb-Douglas** (calibrated so `VA⁰ = L⁰ + K⁰` replicates the benchmark exactly), labour cost share `α_i = L⁰_i/(L⁰_i+K⁰_i)`, scale `B^v_i = VA⁰_i / (L⁰_i^{α_i} K⁰_i^{1−α_i})`. Unit VA cost and conditional factor demands under productivity multiplier `π_i`:

```
c^v_i = (1/(B^v_i π_i)) · (w/α_i)^{α_i} · (r/(1−α_i))^{1−α_i}
L_i   = α_i c^v_i VA_i / w ,    K_i = (1−α_i) c^v_i VA_i / r ,    VA_i = (VA⁰_i/X⁰_i)·X_i
```

**Armington CES** (Hosoe form, σ_A = 2.0, base `PD=PM=1`), with share `δ_i` and scale `B^A_i` calibrated to the benchmark `D⁰_i, M⁰_i`:

```
PA_i = (1/B^A_i)·[ δ_i^{σ_A} PD_i^{1−σ_A} + (1−δ_i)^{σ_A} PM_i^{1−σ_A} ]^{1/(1−σ_A)}
D_i  = (QA_i/B^A_i)·( B^A_i δ_i PA_i / PD_i )^{σ_A}
M_i  = (QA_i/B^A_i)·( B^A_i (1−δ_i) PA_i / PM_i )^{σ_A}
```

**Households** spend a Cobb-Douglas budget (shares `β_i`, savings rate `σ_s`) out of factor income `Y_h = w·L̄ + r·K̄`. **Government & investment** are fixed real (× demand-shift `d_i`). **Exports** fall in the domestic price with elasticity σ_e = 2.0: `EX_i = EX⁰_i · PD_i^{−σ_e}`.

**Equilibrium system** — zero-profit prices, commodity market clearing, and factor-market clearing:

```
(price)     PD_i = Σ_j a^c_{ji} PA_j + c^v_i · (VA⁰_i/X⁰_i)
(commodity) X_i  = D_i + EX_i ,     QA_i = Σ_j io_{ij} X_j + C_i + G_i + I_i
(labour)    Σ_i L_i = L̄ ,    (capital)  Σ_i K_i = K̄
```

solved with `scipy.optimize.root` (hybr, xtol 1e-10). **Benchmark replication:** all excess demands ≈ 0 and `w = 1.000` at base. Feedback to the ABM (Tier-3): the relative mining price `PD_{mine}` (clipped to [0.8, 1.5]) sets next year's mineral-price index, and the wage index scales the development hurdle `h = 0.45·w`.

**Partial-equilibrium fallback** (used only if the full solve fails to converge): linear elasticity responses `Δw = 0.3·(extra labour-demand fraction)`, `Δp = 0.2·(extra output fraction)`, keeping the pipeline finite and bounded (a permanent regression test guards this path).

### 3.6 Spatial allocation (Q2.5 regional growth)

Sectoral jobs are allocated to the 11 NI Local Government Districts by a share matrix `S` (`Σ_d S_{d,i} = 1`), blended 50/50 between population-tilted proxy shares and the confidence-/lifecycle-weighted named-firm headcount geography: `jobs_{d} = Σ_i S_{d,i} · jobs_i`.

### 3.7 Employment, skills & retention (Q2.5)

```
skill split (high/mid/entry) per sector from ONS SOC;  wage_w = NI_median · sector_index
NI_median = £37,100 (NISRA ASHE 2025; £34,632 in 2024 retained as a sensitivity)
retention  = min(0.98, 0.70 + 0.20·local_supplier_support + 0.10·skills_support)
retained_jobs = retention · total_jobs ;     leakage = (1 − retention) · GVA
```

### 3.8 Economic negative impacts (Q2.7)

Five economic downsides of (primarily) primary extraction, each discounted; `m̂` = management intensity `clip(0.5·community_benefit + 0.5·min(1, esg_cost/0.18), 0, 1)`:

```
benefit_leakage      = (1 − retention) · minerals_GVA
closure_liability    = mines_opened · £35m · (1 − m̂)                public if unbonded
displacement         = (disc. active-mine-years) · £3m · (1 − 0.5·m̂)   agri + tourism
boom_bust_VaR        = 0.30 · (end-year mining GVA)                  annual revenue-at-risk
stranded_capital     = £250m · 0.5·(1 − 0.6·circular_hedge)   if a contested mine develops
net_local_GVA        = discounted GVA − (leakage + closure_liability + displacement)
```

Parameters (life-of-mine 18 yr, closure £35m/mine, agri+tourism £3m/mine-yr, volatility 0.30, contested capital £250m, base retention 0.70) are proxy/desk values in the register, grounded in the Minviro report (retained-employment §2.2.5; mine-closure §1.4.6.8; agriculture §3.4.2.4 / tourism §3.4.2.5; price volatility).

---

## 4. Data and provenance

Every parameter carries a status in `model/data/data_register.csv` (105 rows): 🟢 **real** (sourced/audited) · 🟡 **proxy** (desk/scaled) · 🔴 **gap** (placeholder). The pattern is honest: validation anchors, targets and concentration figures are real; economic-structure and behavioural coefficients are proxy.

**Real anchors & control totals**

| Item | Value | Source |
|---|---|---|
| NI mining & quarrying GVA (2018) | £108m (0.27% of NI GVA) | ONS Regional GVA / NISRA via Minviro |
| NI mining & quarrying workers | 1,950 | NISRA BRES |
| NI total employee jobs (Sep 2023) | 816,562 | NISRA BRES |
| Minviro one-mine / two-mine anchors | 73 jobs·£7.3m·£1.6m / 430·£43m·£9m p.a. | Minviro Final Report (Scen 3a / 4b) |
| STPR / mining WACC | 3.5% / 11.26% | Green Book–NIGEAE / Minviro (CAPM) |
| Vision-2035 targets (2035) | ≥10% domestic / ≥20% recycling / ≤60% single-country | Vision 2035 (GOV.UK) |
| EU-CRMA stretch (2030) | 25% recycling / ≤65% single third country | European Commission CRMA |
| NI median FT wage (2025) | £37,100/yr (£713/wk) | NISRA ASHE 2025 |
| 2023 single-country concentration | REE 74% China, Co 70% DRC, Li 44% Australia | BGS/Idoine 2025 |
| Top-three (2024) / refining / export controls | ~86% / 19-of-20 ~70% / ~55% | IEA 2025 |
| NI external trade (2024) | sales £109.3bn; exports £19.6bn; imports £11.2bn | NISRA NIETS 2024 |
| Vision-2035 annex 2035 demand (t) | Cu 3,619,000; Al 8,003,000; Ni 867,200; Li 339,200; Co 163,000; REE 37,940 | Vision 2035 Technical Annex (Annex 2) |

**Firm evidence.** `company_register.csv` — 21 named NI operators (13 web-verified, 8 desk-verified) with role, district, lifecycle, employees, investment, capacity and eight 0–1 scores driving the ABM. Derived: £1,164m capital pipeline; 400 tpa installed REE recovery (Ionic).

**Key calibrated parameters**

| Parameter | Value | Status |
|---|---|---|
| `DOMESTIC_INTENSITY` (A scaling) | 0.62 | proxy |
| mining GVA / employment coefficients | 0.35 / 11.5 jobs·£m⁻¹ | proxy, tuned to Minviro anchors |
| WAGE_SHARE_OF_GVA / LOCAL_CONSUMPTION_PROPENSITY | 0.55 / 0.42 | proxy (Type-II) |
| recovery yields REE/Li/Cu | 0.85 / 0.50 / 0.90 | desk-verified |
| WEEE collection ceiling | 0.25 | desk-verified |
| dev hurdle / social-licence floor | 0.45 / 0.40 | proxy behavioural thresholds |
| σ_Armington / σ_export | 2.0 / 2.0 | proxy |
| SAM factor split / savings / gov share | 0.60–0.40 / 0.10 / 0.18 | proxy |
| stockpile depth / release | 0.5 demand-yr (~180 d) / 0.30 | calibrated to JOGMEC/KOMIR |

**Source documents:** UK Critical Minerals Strategy *Vision 2035* + *Technical Annex*; UK *Modern Industrial Strategy* (2025); EU *Critical Raw Materials Act*; GSNI/BGS *Critical Minerals & the Circular Economy in NI* (OR25042); *Minviro Final Report* + *Appendix A*; BGS 2024 Criticality Assessment; NISRA (BRES, ASHE, NIETS); IEA 2025.

---

## 5. Assumptions and limitations

**Structural / economic**
1. The I-O coefficient matrix `A` is **proxy**, not a regionalised NI table — scaled for high import leakage and tuned to the Minviro anchors. *This is the single biggest calibration dependency* (replace with NISRA Supply-Use + Scottish 2017 I-O via FLQ + RAS).
2. The SAM structure is proxy (only mining GVA is a real anchor); the CGE is a compact reduced form with proxy elasticities (σ_A = σ_e = 2.0) and Cobb-Douglas (not CES) value added.
3. Multipliers/coefficients are calibrated to realistic ranges, not measured.

**Material-flow / behavioural**
4. MFA stock-flow seeds are UK data scaled to NI; NI critical-mineral waste flows are a known gap. Commodity prices are indicative.
5. ABM thresholds (dev hurdle 0.45, social-licence floor 0.40, risk→delay, lever→effect coefficients) are **proxy** and determine which marginal projects open — the first thing to calibrate with planning/licensing and firm-survey data.
6. Firm scores are desk estimates.

**Demand / shock / classification**
7. The seven core Q2 experiments use a shared `GREEN_DEMAND` policy-growth path; the **annex 2035 cumulative tonnages** anchor the separate demand-supply strategy experiment (the two layers are kept explicit).
8. The supply shock is a sustained (or onset-dated) import cap + price spike; the stockpile is a finite, depleting reserve.
9. Copper is treated as a UK **growth** (not critical) mineral, kept in the basket but flagged so critical-mineral shares are not overstated; Q2.7 covers **economic** negative impacts only (environmental CO₂/PM remain in the I-O satellites).

**Spatial / public-cost**
10. District shares blend proxy population-tilted weights with named-firm geography (replace with NISRA BRES-by-district).
11. Lever public costs and ROI are NI-scale figures benchmarked to UK programmes for *relative* ranking, not budget lines (a ±cost band is carried).

> **Bottom line:** the model's structure, internal consistency and direction of travel are robust and validated; the absolute magnitudes are illustrative until the proxy economic/behavioural layer is replaced with collected NI data.

---

## 6. Calibration, validation and verification

**(a) External calibration — Minviro anchors.** Injecting a mining final-demand shock sized to Minviro's one-mine (£7.3m) and two-mine (£43m) total output reproduces the published jobs and *direct* mining GVA:

| Scenario | Metric | Model | Anchor |
|---|---|---|---|
| One mine | output / jobs / direct GVA | 7.30 / 73.1 / 1.58 | 7.3 / 73 / 1.6 |
| Two mines | output / jobs / direct GVA | 43.0 / 430.4 / 9.29 | 43 / 430 / 9.0 |

**(b) Verification harness — 61 checks** (`verify_model.py`, gates CI). *Invariant:* MFA mass balance (baseline + shock), supply-share closure & bounds, no NaN/negatives, determinism (identical config → byte-identical output), SAM balance (~1e-12) + mining-GVA anchor, CGE benchmark replication (w = 1.000), CGE PE-fallback, spatial share closure, stockpile non-negativity/depletion, register integrity, economic-sanity ranges, geopolitical features (diversification, time-varying shock), the IEA top-three/refining/export-control metrics (top-three ≥ single-country; bounded), and the Q2.7 economic-negative layer. *Property-based:* 30 random valid policy bundles must all preserve mass balance, share closure, no-NaN/negatives and a non-negative reserve. **All 61 pass.**

**(c) SAM/CGE benchmark.** SAM row=column to ~1e-12; CGE benchmark `max|excess demand| ≈ 0`, base wage = 1.000.

---

## 7. Reproducibility and file map

```
cd model
pip install -r requirements.txt
python run_mvm.py                 # 6 scenario families → outputs/
python verify_model.py            # 61 invariant + property-based checks
python q2_1_circularity_interventions.py … q2_7_negative_impacts.py
python q_demand_supply_strategy.py
python make_supply_chain_fig.py && python make_plots.py
python validate_model_report.py   # validation artefacts + Word report
python export_word.py             # Word exports → ../word/
streamlit run ../streamlit_app.py
```

| File | Role |
|---|---|
| `src/seed_parameters.py` | sets, coefficients, anchors, targets (from the data register) |
| `src/mfa_module.py` | Material Flow Account (stock-flow, mass balance, shocks, IEA risk metrics) |
| `src/abm_module.py` | firm-grounded mesa agents (real-option mining, recycler, manufacturer) |
| `src/io_module.py` | dynamic Leontief I-O (Type I/II, satellites) |
| `src/sam_module.py` | balanced NI SAM builder |
| `src/cge_module.py` | recursive-dynamic CGE (+ PE fallback) |
| `src/econ_impact_module.py` | Q2.7 economic-negative-impact layer |
| `src/employment_module.py` · `src/spatial_module.py` | Q2.5 skills/wages · jobs→11 councils |
| `src/coupling.py` | annual ABM→MFA→I-O→CGE soft-link + discounting |
| `src/indicators.py` | Minviro validation + Q2.1–2.7 mapping |
| `data/company_register.csv` · `data/data_register.csv` | 21 firms · parameter provenance |

---

*Prepared as technical evidence supporting the DfE minerals & circular-economy consultation. All figures are model behaviour under stated assumptions, not forecasts; parameter-level provenance and status are in `model/data/data_register.csv`. A non-technical decision-maker overview is in `EXECUTIVE_SUMMARY.md`; the integrated findings report is `NI_MINERALS_MODEL_REPORT.md`.*
