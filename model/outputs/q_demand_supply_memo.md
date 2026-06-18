# Demand-side opportunities & supply-side challenges for sustainable minerals development

Scenarios derive demand growth from the **UK Critical Minerals Strategy (Vision 2035)**, the **EU Critical Raw Materials Act**, and the **UK Industrial Strategy (2025)**, run under a sustainable enabling-policy stance (high-ESG + community benefit + finance/skills + circular mix). Demand grows to ~2035 then plateaus. Figures are model behaviour, not forecasts.

## Strategy demand signals used

- **Vision 2035:** UK copper demand ~2x and lithium ~+1,100% by 2035; growth minerals add copper & graphite; targets 10% domestic / 20% recycling / ≤60% single-country; NWF/UKEF finance, BICS energy support.
- **EU CRMA:** 2030 targets 10% extraction / 40% processing / 25% recycling / ≤65% single third country — a large processing-offtake pull and scarcity price premium for UK/NI midstream and recycling.
- **UK Industrial Strategy:** IS-8 growth sectors (Advanced Manufacturing £4.3bn, Clean Energy, Defence) drive EV/offshore-wind/battery demand; **Belfast named as a critical-minerals cluster**.

**Demand growth is derived from the Technical Annex (Annex 2), not hand-set.** The annex's cumulative UK demand at 2024/2027/2030/2035 is differenced to implied annual demand, and an annual-demand CAGR is taken over the ~7-yr gap between the first and last windows: Lithium 26%, Nickel 11%, Aluminium 9%, Cobalt 9%, REE_magnet 9%, Copper 4%. These cross-check against IEA net-zero (copper ~2x, lithium ~9x by 2040). The Industrial-Strategy run weights Cu/REE up 15% (clean-energy/defence emphasis); the CRMA run adds a 10% EU pull + scarcity price premium; demand plateaus after 2035.

**Annex 2035 cumulative-demand anchors (UK, tonnes)** — now in `data_register.csv` with provenance; these are the calibration target, not simple growth proxies:

| mineral | 2024 | 2027 | 2030 | 2035 (cumulative t) | derived annual CAGR |
|---|---|---|---|---|---|
| Copper | 178,400 | 922,200 | 1,953,000 | **3,619,000** | 4.3% |
| Lithium | 2,525 | 28,680 | 113,400 | **339,200** | 26.5% |
| Nickel | 50,430 | 182,700 | 416,100 | **867,200** | 10.8% |
| Cobalt | 6,089 | 34,010 | 76,610 | **163,000** | 9.2% |
| Aluminium | 578,300 | 1,875,000 | 3,966,000 | **8,003,000** | 9.3% |
| REE_magnet | 1,161 | 7,788 | 18,020 | **37,940** | 8.8% |

*Copper is a UK **growth** mineral (the largest-tonnage entry), not a current UK critical mineral — so the demand basket spans **critical & growth minerals**.*

## Part A — Demand-side opportunities for sustainable development

| scenario | label | mines_opened | projects_unlocked | crit_domestic_share_end | crit_recycled_share_end | crit_import_share_end | end_jobs | cum_disc_gva_gbp_m |
|---|---|---|---|---|---|---|---|---|
| 0_current | Current demand + current policy (reference) | 0 | — | 0.01 | 0.319 | 0.67 | 1008.5 | 770.6 |
| sustainable_baseline_demand | Current demand + sustainable enabling policy | 1 | Dalradian Gold | 0.077 | 0.453 | 0.47 | 1604.5 | 1171.6 |
| uk_vision_2035 | UK Vision 2035 demand (Cu x2, Li +1100%) | 1 | Dalradian Gold | 0.055 | 0.439 | 0.505 | 1889.5 | 1228.5 |
| eu_crma | EU CRMA pull + scarcity price premium | 1 | Dalradian Gold | 0.054 | 0.434 | 0.512 | 1973.3 | 1248.3 |
| uk_industrial_strategy | UK Industrial Strategy (clean energy/defence/AM) | 1 | Dalradian Gold | 0.057 | 0.435 | 0.507 | 1925.7 | 1239.2 |
| combined_high_demand | Combined high demand (all three aligned) | 1 | Dalradian Gold | 0.054 | 0.433 | 0.513 | 1985.4 | 1251.9 |

**Opportunity finding:** rising strategy-driven demand makes the circular + primary opportunity materially larger — the strongest case `combined_high_demand` (Combined high demand (all three aligned)) reaches 1985 end-year jobs and £1251.9m discounted GVA (vs 1604 jobs / £1171.6m at today's demand). The EU CRMA scarcity premium improves recovery economics, and a community-benefit + high-ESG stance brings the contested primary deposit (Dalradian) forward.

**The catch (links to Part B):** higher demand *erodes the supply-security ratios* unless capacity scales with it — recycled share falls from 45% (today's demand) to 43%, and import share rises from 47% to 51%, because demand outruns NI's thin processing/recovery capacity. Demand-side opportunity is real but only captured if the supply-side capacity gap is closed.

## Demand sensitivity (how much does the demand assumption matter?)

Varying the annex-derived demand ±50% moves end-year jobs across **1539–2398** (central 1890) and discounted GVA across **£1146–1349m** (central £1228m). Varying *only lithium* (the steepest, most uncertain CAGR) ±50% moves GVA only £1211–1268m — small, because lithium's NI tonnage base is tiny vs copper/aluminium. **The opportunity scales with overall demand, but the headline qualitative findings — Dalradian unlocked by community benefit, recycled share eroding as demand outruns capacity — are robust across the band.**

| demand case | crit_recycled_share_end | crit_import_share_end | end_jobs | cum_disc_gva_gbp_m |
|---|---|---|---|---|
| all_demand_-50% | 0.468 | 0.468 | 1539.3 | 1146.4 |
| lithium_-50% | 0.45 | 0.492 | 1841.3 | 1210.8 |
| central_annex | 0.439 | 0.505 | 1889.5 | 1228.5 |
| lithium_+50% | 0.416 | 0.533 | 2001.2 | 1267.6 |
| all_demand_+50% | 0.413 | 0.54 | 2398.4 | 1348.8 |

## Part B — Supply & capacity challenges (current circular supply chain)

NI capital pipeline across the chain: £1164.0m (operating £914.0m + proposed £250.0m).

| stage | firms | employees | named |
|---|---|---|---|
| Primary / mining | 8 | 2840 | Dalradian Gold; Galantas Gold; Conroy Gold and Natural Resources; Irish Salt Mining and Exploration; Kilwaughter Minerals; Breedon / Whitemountain; FP McCann; Mannok |
| Collection / feedstock | 5 | 824 | Re-Gen Waste; RiverRidge; Bryson Recycling; Envirogreen Recycling; Plaswire |
| Processing / recovery | 1 | 70 | Ionic Technologies |
| Downstream demand | 5 | 8470 | Encirc; Wrightbus; Seagate Technology; Spirit AeroSystems Belfast / Airbus-Boeing transition; Harland & Wolff / Navantia UK |
| Equipment / enabling | 2 | 1500 | CDE Group; Terex Materials Processing / Powerscreen / Finlay |

| mineral | proj_2035_demand_t | ni_processing_capacity_tpa | capacity_coverage | has_primary_prospect | has_collection_route | key_gap |
|---|---|---|---|---|---|---|
| REE_magnet | 203.0 | 400.0 | 1.971 | False | True | Processing capacity exists (Ionic) but feedstock-limited |
| Lithium | 2488.0 | 0.0 | 0.0 | False | True | No NI processing capacity — collection exists, recovery absent |
| Cobalt | 199.0 | 0.0 | 0.0 | False | True | No NI processing capacity — collection exists, recovery absent |
| Nickel | 2013.0 | 0.0 | 0.0 | False | True | No NI processing capacity — collection exists, recovery absent |
| Copper | 13146.0 | 0.0 | 0.0 | True | True | No NI processing capacity — collection exists, recovery absent |
| Aluminium | 26715.0 | 0.0 | 0.0 | False | True | No NI processing capacity — collection exists, recovery absent |
| Antimony | 40.0 | 0.0 | 0.0 | True | False | Primary prospect only — no processing/recovery capacity |

## Key challenges (supply & capacity side)

1. **A single midstream processing asset.** NI has named recovery capacity for REE only (Ionic, 400 tpa) — and even that is dwarfed by projected 2035 demand. There is **no NI processing/recovery capacity for lithium, cobalt or nickel**, the fastest-growing battery metals.
2. **Feedstock collection is the binding circular constraint.** Collection routes exist (Re-Gen, RiverRidge, Bryson) but critical-metal capture from end-of-life is low, so processing capacity would be feedstock-starved.
3. **Almost no domestic primary critical-mineral geology.** The opportunity is midstream + recycling, not primary mining — except contested antimony/copper (Dalradian), which is a social-licence not a resource question.
4. **The chain is demand-rich but capacity-poor.** Strong downstream demand (Wrightbus, Seagate, Encirc, Spirit) and equipment capability (CDE, Terex) are present, but the processing/recovery middle is thin — the priority gap to fund.


## NI-specific evidence base (opportunities)

- **Geology:** NI is the *most prospective area of the UK/Ireland for precious metals* (BGS). Curraghinalt (Sperrins, Tyrone) is NI's one known polymetallic deposit — 3.79 Moz Au measured+indicated plus ~15 kt copper over life and minor **antimony, tellurium, bismuth, cobalt**; the Mourne granites show **REE/critical-metal enrichment** potential; Pt/Pd anomalies in the Sperrins (GSNI Tellus).
- **Innovation ecosystem:** a genuine REE-recycling cluster — **Ionic Technologies** (QUB/Seren spin-out, 400 tpa REO target), **Plaswire** (turbine magnet+blade recycling), and **QUILL** (Queen's Ionic Liquids Lab). NI's named role in Vision 2035 is permanent-magnet recycling.
- **Logistics & feedstock:** Belfast Harbour (24.1 Mt cargo, 2024) is an offshore-wind **decommissioning hub** — an end-of-life turbine-magnet feedstock pipeline for Ionic/Plaswire.
- **Dual-market access:** under **Windsor Framework Art. 13(4)**, EU CRMA provisions could apply in NI (DBT, Apr 2025) — NI midstream/recycling could serve both the UK Vision 2035 and the EU CRMA 40%-processing / 25%-recycling pulls.

## NI-specific evidence base (challenges)

- **Midstream gap is the headline constraint:** ~**80% of UK-shredded automotive/electronic metals are exported for processing** for lack of UK midstream investment (BGS) — NI has one REE processor and none for Li/Co/Ni.
- **Supply concentration to displace:** 2023 mine supply was **74% China (REE), 70% DRC (Co), 44% Australia (Li)** (BGS/Idoine 2025) — the strategic prize, but also why import prices/volumes are volatile.
- **Circular performance has stalled:** NI municipal recycling **~50.4% (2024/25), flat since 2019**, with energy-from-waste rising to 34.3% — competing with recycling for material and locking critical metals out of recovery.
- **Long, contested primary lead times:** ~20 years from discovery to mine globally, with declining grades; NI's best deposit (Curraghinalt) is constrained by social licence, and the **Mineral Development Act (NI) 1969 is under review** (gold/silver vested in the Crown, other minerals in DfE).

## Sources

- UK Critical Minerals Strategy — Vision 2035 (DBT, Jan 2026)
- UK Critical Minerals Technical Annex — Annex 2 demand signals (DBT, 2026)
- UK Modern Industrial Strategy (HMG, Jul 2025)
- EU Critical Raw Materials Act (2024)
- GSNI/BGS — Critical Minerals and the Circular Economy in Northern Ireland (OR25042, 2025)
- BGS/Idoine et al. (2025) — global mine-supply concentration; IEA net-zero demand (2024)
- Dalradian — Curraghinalt 2021 feasibility study; DAERA LAC municipal waste 2024/25

*Capacities are register-derived desk estimates; demand CAGRs are document-anchored (headline annual multiples, not the cumulative Annex-2 totals). Replace with audited plant data and CMIC mineral-by-mineral demand forecasts to calibrate.*