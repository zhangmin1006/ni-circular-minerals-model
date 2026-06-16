# Q2.3 — What support do businesses need to participate in the minerals supply chain?

**Method (grounded in the strategy documents):** Vision 2035 warns supply chains are *vulnerable to shocks such as natural disasters, war or geopolitical fallout* driven by concentration. We model a **dominant-supplier loss** — per-mineral import caps = 1 − (single-country share) using the cited 2023 concentration (China 74% REE, DRC 70% Co, Australia 44% Li; BGS/Idoine 2025) — plus a price spike. Support levers map to **named UK instruments** (NWF/UKEF, BICS, EA priority permitting, Skills England, CLIMATES/Faraday R&D, UKEF offtake, defence stockpiling). Firms are mapped to supply-chain stages; outcomes are read by stage. Figures are model behaviour, not forecasts.

## The shock hits stages differently

- Without support the shock opens a **critical-mineral supply gap of 20%** (unmet demand) and pushes single-country exposure to 25% — the **downstream manufacturers** carry this as input-cost and supply insecurity.
- The same shock is an **opportunity for upstream and midstream firms**: higher prices lift recovery and mining viability (recycled share 15% → 14%), but only if they have the finance/capacity to respond.
- **The aggregate gap masks acute, mineral-specific exposure.** Per mineral the unmet-demand gap is: REE_magnet 73%, Antimony 70%, Cobalt 69%, Lithium 43%, Nickel 27%, Aluminium 19%, Copper 12%. The most single-source-concentrated minerals (REE, antimony, cobalt) lose almost their entire supply, while bulk metals (copper, aluminium) are barely affected — so support should be *targeted by mineral and by the firms that depend on it*, not spread evenly.

## Support needed, by supply-chain stage

| stage | firms | employees | binding_challenge | shock_exposure | support_needed | model_levers |
|---|---|---|---|---|---|---|
| Upstream (primary/mining) | 8 | 2840 | Finance + social licence + permitting; ~20-yr lead time | Opportunity (price signal) — if it can be financed/permitted | NWF/UKEF co-investment, exploration grant, faster permitting, community-benefit scheme | finance_support, exploration_grant, permit_years, community_benefit |
| Midstream (processing/recovery + collection) | 6 | 894 | Capacity gap (1 processor), feedstock collection, energy cost | Opportunity (substitution) — but capacity-constrained | Capital grants, BICS energy support, R&D, offtake guarantees, collection/DRS infrastructure | recycling_grant, energy_cost_index, innovation_grant, secondary_market_support, collection_infrastructure |
| Downstream (manufacturers) | 7 | 9970 | Input-cost/price volatility, supply insecurity, secondary-material access, data/traceability | Threat (input-cost squeeze + supply gap) | Recycled-content procurement, secondary-materials marketplace, supplier development, ecodesign, product-passport data | recycled_content_procurement, secondary_market_support, local_supplier_support, design_standards |
| Enabling (equipment + skills + reserves) | — | — | Skills pipeline, equipment market access, export finance, residual supply risk | Cross-cutting — lets the chain respond and buffers the residual | Green-skills academy (Skills England/DWP), cluster + supplier development, UKEF export support, strategic stockpile/procurement reserve | skills_support, local_supplier_support, strategic_stockpile |

## What the model says each support package does (under the shock)

| scenario | label | crit_supply_gap_end | crit_recycled_share_end | crit_domestic_share_end | total_jobs_end | cum_disc_gva_gbp_m | d_total_jobs |
|---|---|---|---|---|---|---|---|
| 0_no_shock_no_support | No shock, no support (reference) | 0.0 | 0.147 | 0.011 | 1147.7 | 788.3 | 78.5 |
| shock_no_support | Upstream shock, no support | 0.204 | 0.135 | 0.011 | 1069.2 | 771.5 | 0.0 |
| shock_upstream_support | Shock + upstream (primary) support | 0.155 | 0.135 | 0.076 | 1687.4 | 989.6 | 618.2 |
| shock_midstream_support | Shock + midstream (processing/collection) support | 0.136 | 0.204 | 0.011 | 1421.2 | 1008.8 | 352.0 |
| shock_downstream_support | Shock + downstream (manufacturer) support | 0.204 | 0.135 | 0.011 | 1068.8 | 771.6 | -0.4 |
| shock_enabling_support | Shock + enabling (skills/supplier) support | 0.043 | 0.145 | 0.011 | 1115.2 | 781.0 | 46.0 |
| shock_full_support | Shock + full cross-chain support | 0.037 | 0.208 | 0.076 | 2097.1 | 1247.7 | 1027.9 |

- **Most resilience per single package:** `shock_upstream_support` (Shock + upstream (primary) support) — +618 jobs vs the unsupported shock.
- **Midstream support closes the supply gap** (builds the recovery capacity that converts the shock into domestic secondary supply: recycled share rises to 20%); **upstream support** brings domestic primary forward where social licence allows (domestic share to 8%).
- **Crucial sequencing finding:** *downstream support alone barely moves the dial* under the shock (GVA £771.6m vs £771.5m unsupported) — manufacturers cannot buy recycled content that does not yet exist. Recycled-content procurement and supplier development only pay off **once midstream capacity is built**, so downstream support must be sequenced with (or after) midstream investment.
- **Stockpile vs capability — two kinds of support do different jobs.** The enabling package (which carries the Vision-2035 *strategic stockpile*) cuts the aggregate gap cheaply to 4% but builds no industry (GVA £781.0m, recycled share flat). Midstream support builds lasting capability (GVA £1008.8m, recycled share to 20%) but takes time. **A stockpile is fast, cheap insurance; midstream/upstream investment is the durable fix — the Department needs both.**
- **Full cross-chain support** cuts the supply gap to 4% and lifts total jobs to 2097 (+1028 vs unsupported shock), £1247.7m discounted GVA.

## Resilience across shock severity (½ → 1.5× of the dominant supplier lost)

Critical-mineral **supply gap** (unmet demand) by shock severity (how much of the dominant single supplier is cut off) and support package — lower is more resilient. The `full` package includes the Vision-2035 strategic-stockpile/procurement reserve:

| severity | no_support | upstream | midstream | full |
|---|---|---|---|---|
| mild_half_supplier | 0.033 | 0.033 | 0.027 | 0.003 |
| moderate_supplier_lost | 0.204 | 0.155 | 0.136 | 0.037 |
| severe_+25pct | 0.3 | 0.234 | 0.234 | 0.06 |
| extreme_+50pct | 0.398 | 0.327 | 0.331 | 0.117 |

- **The gap scales with severity:** unsupported, it rises from 3% (mild) to 40% (extreme).
- **Support is more valuable the more severe the shock** — but no single stage is enough under an extreme shock: midstream support alone leaves a 33% gap, whereas **full cross-chain support holds it to 12%**. Mild shocks can be absorbed by midstream capacity alone; severe shocks need upstream + midstream + downstream together.
- **Implication:** the depth of support should scale with assessed supply risk. For low-risk minerals, fund the midstream (recovery) capacity; for high-risk, single-source-dependent minerals (REE/Co/Li), the full cross-chain package is justified.

## Recommendations (stage-differentiated business support)

1. **Upstream firms** need *capital and confidence*: National Wealth Fund / UK Export Finance co-investment and guarantees, faster/clearer permitting, and a community-benefit scheme to convert price signals into actual domestic supply.
2. **Midstream processors/recyclers** (the binding capacity gap) need *capex + operating-cost relief + demand certainty*: capital grants, BICS-style energy support, R&D co-funding, offtake guarantees, and collection/DRS infrastructure.
3. **Downstream manufacturers** need *supply security and secondary-material access*: recycled-content procurement, a secondary-materials marketplace, supplier-development support, and ecodesign standards.
4. **Cross-cutting:** a green-skills academy and a minerals/circular cluster (anchored on CDE/Terex equipment makers and QUB) so every stage can deliver.

## Sources

- UK Critical Minerals Strategy — Vision 2035 (DBT, Jan 2026): NWF/UKEF, BICS, EA priority permitting, Skills England/DWP, defence stockpiling, offtake, partnerships
- Model proposal Q2.3 taxonomy: finance, skills, data, permits, offtake, export, recycling infrastructure, supplier-development support
- GSNI/BGS — Critical Minerals and the Circular Economy in NI (OR25042, 2025): ~80% UK metals exported for processing; supply concentration; ~20-yr lead times; declining grades
- BGS/Idoine et al. (2025): 2023 single-country supply concentration (REE 74%, Co 70%, Li 44%)
- Minviro Final Report: local-procurement leakage and skills constraints
- Innovate UK CLIMATES (£15m) + Faraday/ReLiB (£34m); DEFRA DRS impact assessment

*Behavioural thresholds and the shock magnitude are PROXY; calibrate with firm-level survey, trade-exposure and licensing data.*