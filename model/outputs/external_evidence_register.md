# External evidence register for Q2.1-Q2.7

Purpose: additional evidence collected to strengthen the seven consultation-question answers and identify model parameters that can be improved. This is an evidence register, not a forecast. Values should be wired into the model only after checking definitions, geography and units.

## Priority data points

| Question | Evidence found | Current model use | Suggested model action | Source |
|---|---:|---|---|---|
| Q2.1 circularity | UK Vision 2035 target: 20% of annual UK critical-mineral demand met through recycling by 2035. | Already used as recycling target. | Keep target; use it explicitly as the pass/fail threshold for intervention packages. | GOV.UK Vision 2035: https://www.gov.uk/government/publications/uk-critical-minerals-strategy/vision-2035-critical-minerals-strategy |
| Q2.1 circularity | EU CRMA benchmark: 25% of EU annual consumption from recycling by 2030. | Current model uses UK 20%. | Add as sensitivity target, especially for NI dual UK/EU market positioning. | European Commission CRMA: https://single-market-economy.ec.europa.eu/sectors/raw-materials/areas-specific-interest/critical-raw-materials/critical-raw-materials-act_en |
| Q2.1/Q2.3 | CLIMATES circular critical materials fund launched with GBP 15m; UK A2D facility has GBP 65.5m clean-energy innovation platform with critical-minerals pillar. | Public-cost assumptions use proxy NI-scale values. | Use these as upper/lower programme-cost anchors for innovation-grant sensitivity. | GOV.UK Critical Minerals Refresh: https://www.gov.uk/government/publications/critical-minerals-refresh/critical-minerals-refresh-delivering-resilience-in-a-changing-global-environment |
| Q2.2 opportunities | UK 2024 criticality assessment expanded assessed materials from 26 to 82 and identifies materials critical to UK prosperity, security and technology development using 2018-2022 data. | Implemented partly: Q2.2 now exports `mineral_class`, `critical`, and `growth_mineral` so copper can be reported separately. | Next: align the broader mineral inclusion/ranking with the full 2024 CMIC criticality list if the model scope expands beyond the current 10 minerals. | NERC/BGS NORA: https://nora.nerc.ac.uk/id/eprint/539735/ |
| Q2.2/Q2.4 | Vision 2035 technical annex lists copper as a growth mineral, even though not in the critical list, because it is fundamental for advanced manufacturing and clean energy. | Implemented: copper remains inside the supply-security basket for strategic NI relevance but is now flagged as a growth mineral and excluded from critical-only metrics. | Keep reporting both "critical & growth" and "critical-only" shares; avoid using the boolean `critical` for copper. | GOV.UK technical annex: https://www.gov.uk/government/publications/uk-critical-minerals-strategy/critical-minerals-technical-annex |
| Q2.3 business support | Vision 2035 names concrete support levers: National Wealth Fund, UKEF, BICS, EA priority tracked permitting, Skills England/DWP, demand aggregation, defence stockpiling/procurement, and up to GBP 50m DBT funding for UK critical mineral projects. | Already represented as policy levers. | Replace generic labels in memos with these instruments and map each lever to the named programme. | GOV.UK Vision 2035 |
| Q2.4 secure supply | UK 2035 targets: at least 10% domestic production, 20% recycling, and no more than 60% supplied by any one country in aggregate. | Already used; current NI scenarios often miss domestic and concentration targets. | Keep as dashboard thresholds; do not claim full compliance unless all three metrics pass. | GOV.UK Vision 2035 |
| Q2.4 secure supply | IEA 2025: top-three producer concentration for copper, lithium, nickel, cobalt, graphite and REEs rose to 86% in 2024; almost all supply growth came from the single top supplier except nickel. | Implemented: `crit_max_top3` is now reported beside single-country exposure and verified by the harness. | Continue to interpret top-three exposure with the supply gap; do not treat falling exposure under an export ban as security. | IEA 2025 press release/report: https://www.iea.org/news/diversification-is-the-cornerstone-of-energy-security-yet-critical-minerals-are-moving-in-the-opposite-direction |
| Q2.4 secure supply | IEA 2025: export controls affect 55% of energy-related strategic minerals; China is leading refiner for 19 of 20 strategic minerals analysed with around 70% average share. | Implemented: refining exposure and export-control exposure are reported and bounded by verification tests. | Use these metrics to keep the midstream processing/recovery capacity recommendation central. | IEA 2025 |
| Q2.4/Q2.6 demand | Vision 2035 technical annex 2035 cumulative demand estimates: aluminium 8,003,000 t; cobalt 163,000 t; copper 3,619,000 t; lithium 339,200 t LCE; nickel 867,200 t; REEs 37,940 t. | Implemented in the demand-supply strategy experiment. The seven Q2 scripts still use the shared `GREEN_DEMAND` path unless stated otherwise. | Keep the distinction explicit in reports: "annex-anchored demand study" vs "standard Q2 policy-growth path." | GOV.UK technical annex |
| Q2.5 employment/skills | NISRA ASHE latest results: NI full-time median weekly earnings were GBP 713 in April 2025, up from GBP 664 in 2024; median annual earnings GBP 37,100. | Implemented: `employment_module.NI_MEDIAN_ANNUAL_WAGE` now reads the 2025 register value. | Keep 2024 as a sensitivity if comparing with older outputs. | NISRA ASHE: https://www.nisra.gov.uk/statistics/work-pay-and-benefits/annual-survey-hours-and-earnings |
| Q2.6 benefits/trade | NISRA NI Economic Trade Statistics 2024: total NI business sales GBP 109.3bn; exports outside UK GBP 19.6bn; imports from outside UK GBP 11.2bn; trade surplus GBP 8.4bn. | Model export/import benefits are proxy. | Use NIETS sector/product tables to calibrate export intensity and avoided-import framing. | NISRA NIETS: https://www.nisra.gov.uk/statistics/business/ni-economic-trade |
| Q2.7 negative impacts | EU CRMA requires monitoring, waste recovery potential from extractive waste, permanent-magnet recyclability/recycled-content requirements, and environmental-footprint rules. | Model impact indices are relative proxies. | Add policy narrative and potential variables for extractive waste recovery, permanent-magnet recyclability and environmental footprint. | European Commission CRMA |

## Highest-value data upgrades

1. Replace the proxy I-O/SAM structure with regionalised NISRA Supply-Use / ABI / NIETS data. This would improve Q2.5 and Q2.6 most.
2. Add a "critical + growth minerals" reporting layer. Copper is a UK growth mineral, not a current UK critical mineral; this matters for Q2.2 and Q2.4 interpretation.
3. Maintain the new processing/refining concentration metrics in the shock module. IEA evidence shows the security problem is often midstream/refining, not mine production alone.
4. Keep the NISRA ASHE 2025 wage anchor as the default, with 2024 retained only for comparison with older runs.
5. Keep Vision 2035 annex cumulative demand estimates as the main calibration source for the separate 2035 demand scenarios; do not imply every Q2 experiment uses those CAGRs.

## Notes by question

### Q2.1 circularity and innovation

The current answer is directionally strong. External evidence reinforces the model's emphasis on collection, secondary markets and circular design. The UK 20% recycling target and EU 25% recycling benchmark make it worth reporting both a UK-compliance and an EU-stretch result.

### Q2.2 opportunities and challenges

The most important refinement is mineral classification. Copper is now framed as a growth mineral in the UK taxonomy, not simply as critical. That does not weaken the case for copper in NI, but it changes the answer from "critical-mineral domestic supply" to "critical and growth-mineral industrial resilience."

### Q2.3 business support

Vision 2035 gives a strong official policy map for the model levers: finance, energy costs, permitting, skills, demand aggregation, defence stockpiling and DBT project funding. The model should continue to use stage-specific support, but the answer should name these official instruments.

### Q2.4 secure supply

The current model now captures single-country shock exposure, top-three concentration, processing/refining dependence and export-control exposure. The key interpretive rule is that lower single-country exposure during an export ban is not security by itself; it must be read alongside the unmet-demand supply gap.

### Q2.5 employment and skills

The wage anchor has been updated to GBP 37,100 median annual full-time earnings in 2025. This lifts wage-bill estimates without changing job counts.

### Q2.6 economic benefits

The avoided-import and export assumptions need stronger calibration. NISRA NIETS gives a current NI-wide trade frame; the next step is pulling NIETS sector tables for manufacturing/mining/recycling-like sectors and replacing generic export shares.

### Q2.7 negative impacts

Q2.7 is now focused on the economic negative impacts of mineral development: benefit leakage, closure/remediation liability, agriculture/tourism displacement, boom-bust exposure and stranded capital. Environmental CO2/PM remain tracked as satellites, but the old water/land/biodiversity/waste pressure-index framing should not be described as the Q2.7 answer.
