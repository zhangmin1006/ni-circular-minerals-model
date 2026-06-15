# Northern Ireland Circular Minerals Policy Model — Build Plan

**Prepared for:** evidence submission / model build supporting DfE minerals & circular economy policy
**Date:** June 2026
**Purpose:** an integrated **dynamic Input–Output + CGE + Agent-Based Model** of the NI minerals system (primary extraction → use → recycling), built around a circular-economy supply chain, designed to answer consultation questions 2.1–2.7.

---

## 0. How this plan differs from the original proposal

The `model proposal.docx` architecture is sound and is kept: **ABM as the supply-chain engine, dynamic I-O as the impact-accounting layer, CGE as the economy-wide adjustment layer.** The changes below are all about *data realism* — the user's explicit instruction was "adjust it based on the data you could collect."

| Issue in original proposal | Reality | Adjustment in this plan |
|---|---|---|
| Assumes usable NISRA NI Input-Output tables | NI's own analytical I-O tables are **out of date relative to GB**; Minviro itself had to use **Scottish 2017 I-O tables as a proxy** because NI tables were insufficient | I-O module built as a **regionalised/updated hybrid** (NISRA Supply-Use + Scottish/UK tables + RAS/FLQ regionalisation), not an off-the-shelf NI table |
| Full NI CGE with SAM | NI has **no published Social Accounting Matrix**; a full regional CGE is the single most data- and labour-hungry component | CGE **de-scoped to Phase 2 / "stretch"**; deliver a **recursive-dynamic reduced-form CGE** only after the SAM is built, and make the I-O+ABM core usable *without* it |
| Mineral-by-mineral NI material flows in the ABM | NI-level stock/flow and WEEE/recycling data are **sparse**; most exist only at UK level | ABM backbone = a **Material Flow Account (MFA)** parameterised with UK/EU stock-flow data **scaled to NI**, with explicit uncertainty bands |
| 9–18 month single build | Realistic, but back-loads all answers | Re-sequenced around a **Minimum Viable Model (MVM)** that answers 2.1, 2.5, 2.6, 2.7 at ~month 6 |

**Headline recommendation:** build a **Minimum Viable Model first** (MFA + dynamic I-O + a light ABM), get defensible answers to most questions, then add the CGE and ABM behavioural richness. Do not let the CGE (the hardest piece) gate the whole project.

---

## 1. Modelling philosophy: three tiers

- **Tier 1 — Minimum Viable Model (MVM):** Material Flow Account + dynamic I-O multipliers + a *deterministic* scenario ABM (rules, no learning). Answers 2.1, 2.4 (partial), 2.5, 2.6, 2.7. Deliverable ~month 6.
- **Tier 2 — Behavioural ABM + soft-linked CGE:** add adaptive agents (investment, collection, procurement decisions) and a recursive-dynamic CGE soft-linked to the I-O. Answers 2.2, 2.3, and strengthens 2.4. Deliverable ~month 12.
- **Tier 3 — Fully coupled policy simulator:** iterative ABM↔I-O↔CGE feedback, stochastic supply shocks, full scenario suite + dashboard. Deliverable ~month 18.

Each tier is independently useful and publishable as evidence.

---

## 2. Overall architecture

```
                 ┌─────────────────────────────────────────────┐
                 │  SCENARIO / POLICY LEVER LAYER               │
                 │  grants, permitting, procurement, targets,   │
                 │  ESG conditions, skills funding, offtake      │
                 └───────────────┬─────────────────────────────┘
                                 │ policy parameters
        ┌────────────────────────▼─────────────────────────────┐
        │  ABM — minerals supply-chain & circular-economy engine │
        │  agents + Material Flow Account (by mineral & product) │
        │  OUT: mine openings, recycling capacity, collection &  │
        │  recovery rates, secondary prices, local procurement   │
        │  share, skills bottlenecks, tonnes by pathway          │
        └───────────────┬───────────────────────┬───────────────┘
          physical flows │                       │ behaviour params ↑
          & final demand ▼                       │ (prices, wages from CGE)
        ┌──────────────────────────┐   ┌─────────▼───────────────┐
        │ DYNAMIC I-O               │   │ CGE (Tier 2/3)          │
        │ GVA, jobs, wages, tax,    │◄─►│ prices, wages, trade    │
        │ direct/indirect/induced,  │   │ substitution, energy,   │
        │ CO₂, PM, local procurement│   │ public finance, welfare │
        └───────────────┬──────────┘   └─────────────────────────┘
                        ▼
        ┌──────────────────────────────────────────────────────┐
        │  INDICATOR / DASHBOARD LAYER  → maps to Q2.1–2.7       │
        └──────────────────────────────────────────────────────┘
```

**Coupling style:** *soft-linking* (sequential, annual time-step, files passed between modules), **not** hard-coded simultaneous solving. This is the realistic, debuggable choice for a small team and lets each module be validated independently.

---

## 3. Module A — ABM (the core the consultation needs)

### 3.1 The physical backbone: a Material Flow Account (MFA)
Before agents, build a stock-flow account per mineral and product group:

`primary extraction → processing/refining → manufacturing use → in-use product stock → end-of-life arisings → collection → reuse/repair → recycling/recovery → secondary material → (imports/exports close the balance)`

Tracked minerals (prioritised by NI relevance from Minviro + Vision 2035): **REE/permanent magnets, lithium, cobalt, nickel, copper, aluminium/bauxite/gallium, antimony, baryte, salt, zinc**. Mass-balance must close each period (inflows = outflows + stock change).

### 3.2 Agents
| Agent | Key decisions | Drives questions |
|---|---|---|
| Exploration & mining firms | invest / explore / develop / pause / abandon — based on price, permitting time, finance, ESG cost, social licence | 2.2, 2.4, 2.6, 2.7 |
| Processors / refiners / recyclers (e.g. Ionic Technologies-type) | invest in recovery/separation/refining capacity; accept feedstock | 2.1, 2.3, 2.4 |
| Manufacturers / downstream users (renewables, aerospace, electronics, life sciences, construction) | use primary vs imported vs secondary material | 2.1, 2.4, 2.6 |
| Waste collectors / councils / WEEE-battery-ELV stewardship | collection routes, sorting, contracts, recovery pathway | 2.1, 2.5 |
| Households & businesses | generate end-of-life stock; participate in collection/repair | 2.1, 2.5 |
| Regulator / government | sets the policy levers (this is the scenario layer) | all |
| Communities & local labour markets | social licence, planning delay, labour availability, local retention | 2.5, 2.7 |

### 3.3 Behavioural logic (kept deliberately simple & data-driven)
- **Investment**: NPV/real-options trigger using commodity price path, capex/opex, permitting lag, WACC (~11.26% nominal mining cost-of-equity per Minviro), and an ESG/social-licence cost adder.
- **Local procurement / leakage**: explicit *local content share* parameter per input — this is the mechanism that fixes Minviro's key limitation (benefits leaking out of NI when labour/equipment are imported). Directly feeds I-O Type I/II multipliers.
- **Circular pathways**: collection rate × sorting yield × recovery yield per product→mineral, with secondary-material price competing against primary/import price.
- **Skills bottleneck**: vacancy-to-supply ratio raises wages / delays projects (links to CGE labour market in Tier 3).

Tier 1 = fixed rules. Tier 2 = adaptive (agents update expectations / imitate successful peers).

---

## 4. Module B — Dynamic Input-Output (impact accounting)

**The honest data position:** there is no current, ready-to-use NI analytical I-O table; Minviro used **Scottish 2017 tables as a proxy**. So this module is a *construction task*, not a lookup.

**Build approach:**
1. Start from **NISRA Supply-Use tables** + most recent NISRA analytical I-O as structural base.
2. **Regionalise** GB/Scottish coefficients to NI using location quotients (FLQ) and RAS/GRAS balancing to NISRA control totals (regional GVA, BRES employment).
3. Add a **disaggregated mining/quarrying, recycling, and secondary-materials** sector split (standard tables bury these) using BRES + company accounts + recycler surveys.
4. **Dynamic coefficients:** let technical coefficients evolve annually for recycling substitution, import-share shifts, energy transition, productivity, and local-supplier development (fed from the ABM).
5. Type I and Type II multipliers → GVA, output, employment, wages, tax proxy, direct/indirect/induced, local procurement effect.
6. **Environmental extension** (Minviro's CLCA template): bolt CO₂, particulates, energy, waste onto output via NAEI/DAERA emission factors and ecoinvent/EXIOBASE/UK-MRIO coefficients.

Baseline anchor facts (for validation): NI mining & quarrying **GVA ≈ £108m (2018, ~0.27% of regional total)**, **~1,950 sector workers**; Minviro scenario range **3 jobs → 430 jobs / £43m output / £9m GVA p.a.**

---

## 5. Module C — CGE (de-scoped, Tier 2/3 only)

**Why de-scoped:** NI has no published SAM; a regional CGE for a *very open, small* economy is the highest-effort, highest-uncertainty component. Do not let it gate Tiers 1–2.

**Realistic build:**
1. **Construct an NI SAM** from the balanced I-O + NISRA economic accounts + HMRC regional trade + government revenue/expenditure. (This is itself ~3 months.)
2. **Recursive-dynamic, comparative-static-per-year CGE** (not full intertemporal optimisation) — appropriate to the data quality.
3. Closures/features: **Armington** import substitution (GB / Ireland / EU / RoW), **primary↔secondary mineral substitution**, skilled/unskilled labour, energy-price sensitivity, public-budget constraint.
4. Use CGE **only** for the questions I-O genuinely cannot answer: price/wage pressure, crowding-out, trade substitution, welfare, public-finance effects.

**Fallback if SAM proves infeasible in time:** replace full CGE with a **partial-equilibrium price/labour module** (elasticity-based) soft-linked to I-O — captures 70% of the policy-relevant feedback at a fraction of the cost. Recommend this as the pragmatic default and treat full CGE as the stretch goal.

---

## 6. How the modules interact (soft-linked, annual)

1. **ABM → I-O:** physical flows + final demand + local-procurement shares → short-run GVA/jobs/emissions.
2. **I-O → CGE:** sectoral demand shock → economy-wide prices, wages, trade, public finance.
3. **CGE → ABM:** updated prices/wages/energy costs feed next-year agent decisions (e.g. higher wages worsen mining labour shortage; higher mineral price triggers investment; higher energy cost erodes recycling viability).
4. Iterate per year over the 30-year horizon (matching Minviro), discounting at **STPR 3.5%** (Green Book / NIGEAE).

Tier 1 runs steps 1–2 only. Tier 3 closes the full loop.

---

## 7. Scenario suite (six families, from the proposal, retained)

1. **Baseline** — current exploration, recycling, supply-chain capacity; no policy change.
2. **Circular innovation** — grants/R&D, better collection, digital product passports, secondary-materials marketplace, design-for-disassembly standards, recycled-content public procurement.
3. **Primary extraction** — moderate (one-mine) and significant (two-mine) development on Minviro exploration-to-mine timelines.
4. **Integrated circular + primary** — mining + recovery + manufacturing developed together with local-procurement & ESG conditions.
5. **Supply shock** — global disruption / price spike / export restriction in Li, REE, Co, Ni or Cu.
6. **High-ESG / low-impact** — stricter water/biodiversity/carbon/closure/community-benefit requirements; higher cost, lower risk.

Run each across the three NI demand drivers (EV uptake, wind deployment, grid investment) from Vision 2035.

---

## 8. Data sources — mapped, with a feasibility rating

Rating: 🟢 available & usable · 🟡 partial / needs work · 🔴 gap, needs primary collection or proxy.

### Economic / I-O
- 🟡 **NISRA Supply-Use & analytical I-O tables** — structural base, but dated → must regionalise/update.
- 🟢 **ONS Regional GVA**, **NISRA economic accounts / business demography**.
- 🟡 **HMRC Regional Trade Statistics** — import/export exposure; note NI-EU uses Intrastat, customs covers other flows (messy post-Windsor Framework).
- 🟡 **Company accounts** (FAME/Companies House) — to split mining/recycling/secondary sectors.

### Employment, skills, business
- 🟢 **NISRA BRES** (sectoral employment; NI ≈ 816,562 employee jobs, Sep 2023), **ASHE** earnings, **Census 2021** qualifications.
- 🟢 **FE / apprenticeship data**, **Invest NI** business directories.
- 🟡 Firm-level surveys of manufacturers/recyclers/mining suppliers → **primary collection needed** for procurement & skills detail.

### Geology, resources, licensing
- 🟢 **GSNI Tellus** geochemical/geophysical data (55 elements; Au/PGE/base-metal anomalies).
- 🟢 **GSNI mineral resource maps**; 🟢 **DfE minerals licensing maps & licence data** (current/potential exploration).

### Circular economy / waste
- 🟢 **DAERA LAC municipal waste statistics** (arisings, recycling, recovery, landfill).
- 🔴 **WEEE / batteries / ELV / magnets / industrial scrap at NI level** — weak; mostly UK-level producer-responsibility data → combine DAERA/NIEA + EA producer data + **recycler surveys/interviews** + scheme data; scale UK→NI.
- 🟡 UK strategy context: recycling constrained by low critical-mineral-rich waste availability, low collection rates, technical recovery limits.

### Demand & supply-chain resilience
- 🟢 **Vision 2035 demand estimates** (Cu, Li, Ni, Co, REE… 2027/30/35), **CMIC** criticality, **UK Technology Metals Observatory**, **Met4Tech** roadmaps.
- 🟢 **BGS UK 2024 Criticality Assessment** (82 candidates → 34 critical).
- 🟡 **NI energy scenarios, EV/wind/grid deployment** — for demand drivers.

### Environmental & spatial (for 2.7)
- 🟢 **DAERA GHG inventory, air quality, waterbody status, abstraction/discharge permits**; **NIEA protected sites (ASSI/SAC/SPA)**, land cover, flood risk.
- 🟢 **Agriculture & tourism statistics** (displacement effects).
- 🟢 **LCA databases**: ecoinvent / EXIOBASE / UK-MRIO environmental extensions; Minviro CLCA as template.

**Critical data gaps to flag to the Department now:** (1) up-to-date NI I-O / SAM; (2) NI-level critical-mineral waste & recycling flows; (3) firm-level local-procurement and skills data. All three are addressable but need either commissioning or surveys — worth securing early.

---

## 9. Model outputs mapped to the seven questions

| Q | Indicators the model produces | Primary module |
|---|---|---|
| **2.1** Innovation for circularity | recovery rates, secondary-material volumes & value, recycling GVA/jobs, innovation ROI, best policy mix (grants vs standards vs procurement vs collection infra) | ABM + I-O |
| **2.2** Opportunities & challenges | mineral-by-mineral opportunity ranking; binding constraints (geology, finance, skills, energy, permitting, water, biodiversity, social licence) | ABM + geology data |
| **2.3** Business support | which firm types need finance / skills / data / permits / offtake / export support / supplier development | ABM |
| **2.4** Secure-supply role | domestic primary share, recycling share, import dependency, **supply-concentration HHI**, stock-flow resilience, strategic intervention points vs Vision 2035 targets (10% domestic / 20% recycling / ≤60% single-country) | ABM (MFA) + CGE |
| **2.5** Employment, skills, regional growth | jobs by council area / occupation / skill / wage band, **retained local** employment, training needs, supplier opportunities | I-O + ABM |
| **2.6** Economic benefits | GVA, output, tax proxy, exports, investment, productivity, manufacturing resilience, **avoided import costs** | I-O + CGE |
| **2.7** Negative impacts | CO₂, particulates, water risk, land take, biodiversity, waste, traffic, agriculture/tourism displacement, wage inflation, boom-bust, public-sector costs | I-O env-extension + CGE + spatial data |

Note (per proposal): the **Minviro Appendix A** is the reference for 2.7 — impacts are site-specific and depend on receptors, design, operation and closure (land transformation, water, carbon, air, noise, hazards, socio-economic).

---

## 10. Adjusted work programme

| Phase | Months | Output | Tier |
|---|---|---|---|
| 1. Scoping & policy logic | 1 | minerals, products, sectors, geographies, levers, indicators for 2.1–2.7 | — |
| 2. Data architecture & baseline | 2–3 | MFA + economic account + waste-flow account + supply-chain map; **gap register** | 1 |
| 3. Dynamic I-O module | 2 | regionalised/updated NI I-O + dynamic coefficients + env extension | 1 |
| 4. ABM prototype (rule-based) | 3 | agents, material flows, investment & collection/recovery logic | 1 |
| **MVM milestone (~month 6):** answers 2.1, 2.5, 2.6, 2.7 + partial 2.4 | | | **1** |
| 5. ABM behavioural enrichment | 2 | adaptive investment, procurement, skills bottlenecks | 2 |
| 6. NI SAM + reduced-form CGE (or PE fallback) | 4 | price/wage/trade/public-finance feedback | 2 |
| 7. Coupling & validation | 2–3 | ABM↔I-O↔CGE soft-link; validate vs historical mining/recycling/employment/trade | 3 |
| 8. Scenario runs & dashboard | 2 | six scenario families → policy dashboard answering 2.1–2.7 | 3 |

**Credible first version: ~6 months (MVM). Robust calibrated version: 12–18 months.**

---

## 11. Tooling recommendation

- **ABM:** Python (Mesa) or NetLogo for prototyping; Python preferred for integration with the other modules.
- **I-O:** Python (`pymrio`, NumPy/pandas) — handles MRIO, multipliers, environmental extensions natively.
- **CGE:** GAMS or Python (with a CGE library) on the constructed SAM; PE fallback in pure Python.
- **Coupling:** orchestration script passing annual CSV/parquet between modules; version-controlled scenario configs.
- **Dashboard:** Streamlit / Power BI over the indicator layer, structured by 2.1–2.7.

---

## 12. Main recommendation

Build the model around **circular supply security, not mining alone.** The strongest NI policy case is the *combination*: responsible primary extraction where evidence supports it + critical-mineral recovery from end-of-life products + local supplier development + skills formation + high-ESG permitting + secondary-materials market creation.

The model should answer not "mining **vs** recycling" but **which mix** of mining, recycling, substitution, circular design, imports and public support delivers the best balance of resilience, GVA, employment, environmental protection and community acceptance — and it should do so with **honest uncertainty bands**, given the data gaps above.

**Single most important early action:** commission/secure the three gap datasets (updated NI I-O/SAM; NI critical-mineral waste & recycling flows; firm-level procurement & skills survey). Everything downstream depends on them.
```