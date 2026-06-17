# Q2.6 — Economic benefits of the NI minerals sector

**Method:** the coupled model's GVA / output / jobs (Type-II, discounted at STPR 3.5% over 30 years; multiplier basis as Minviro — NI 2016 + Scotland 2016 I-O) are extended with the proposal's full benefit suite — a **tax proxy** (~25% effective take on GVA), **exports**, the named-firm **investment pipeline**, **productivity** (GVA per worker), **manufacturing resilience** and **avoided import costs** (the discounted value of demand met by domestic + recycled supply, i.e. the import bill NI does not pay). Value-for-money is a GVA benefit-cost ratio (BCR) vs notional public cost. Figures are model behaviour, not forecasts.

This maps onto Minviro's own taxonomy of *positive socio-economic impacts* — job creation, economic multiplier effects, **payment of taxes and royalties**, new infrastructure, **investment in training and skills**, **employment of nationals/locals**, and **procurement of goods and services in-country** — so the benefit set below is the document's, quantified.

## Benefit suite by scenario

| scenario | label | cum_disc_gva_gbp_m | avoided_import_cost_gbp_m | tax_proxy_gbp_m | exports_gbp_m | gva_per_worker_gbp | disc_public_cost_gbp_m | gva_bcr | econ_resilience_bcr |
|---|---|---|---|---|---|---|---|---|---|
| 1_baseline | Baseline | 788.3 | 1215.2 | 197.1 | 630.7 | 45678.0 | 0.0 | nan | nan |
| 2_circular_innovation | Circular innovation | 1019.1 | 1567.2 | 254.8 | 841.9 | 46494.0 | 291.2 | 0.79 | 2.0 |
| 3_primary_extraction | Primary extraction | 790.0 | 1217.9 | 197.5 | 631.5 | 45659.0 | 113.1 | 0.02 | 0.04 |
| 4_integrated | Integrated circular + primary | 1152.6 | 1789.1 | 288.1 | 873.5 | 43625.0 | 425.4 | 0.86 | 2.21 |

## Findings

1. **The benefits are substantial and rise with ambition.** The integrated circular + primary scenario delivers ~£1,153m discounted GVA (+£364m vs baseline), ~£288m tax take and ~£874m exports over 30 years, alongside the £1,164m named-firm investment pipeline.
2. **Avoided import costs are a major, often-missed benefit.** Domestic + recycled supply avoids ~£1,789m of discounted import spending (+£574m vs baseline) — a direct trade-balance and resilience gain for NI manufacturers that buy secure, local inputs rather than volatile imports.
3. **Quality, productive jobs.** GVA per worker is ~£43,625 and the sectors pay above the NI average (see Q2.5); manufacturing resilience improves as secure secondary inputs displace import risk.
4. **Value for money:** on **incremental GVA alone** the return is below 1 for the capital-heavy scenarios (e.g. integrated ~0.86 extra GVA per £ public cost) — but once the **avoided-import / resilience benefit** is added the return rises to ~2.21× and the wider tax, export and jobs benefits push it higher still. Pure extraction support is the weakest value (little opens without social licence — cf. Q2.2).
5. **Benefits compound across questions:** the same spend that secures supply (Q2.4) and supports firms (Q2.3) also produces the GVA, exports and avoided imports here — so the economic case should be read as a portfolio, not lever-by-lever.

## Retained benefit & caveats (Minviro)

- **Benefits only count if they stay in NI.** Minviro devotes a section to *retained employment*, warning that mining benefits can be *"economically detached from the regions"* — it cites the recently closed Irish mines **Galmoy and Lisheen**, where national and international specialist firms during construction *limited the extent of local employment*. So the headline GVA/jobs here are an upper bound; the *retained* share depends on local-content and skills measures (quantified in Q2.5, where retention rises from ~70% to ~97%).
- **A skilled-labour shortage is a binding limitation.** Minviro notes all scenarios *"rely on access to a pool of skilled labour"* (even the US flags too few qualified domestic workers) — so the skills pipeline (Q2.5) gates how much of this benefit materialises.
- **Fiscal benefit is conservative.** The ~25% tax proxy captures income tax/NICs + corporation tax but **excludes royalties** (gold and silver are Crown-vested in NI) — Minviro lists *taxes and royalties* together, so the true fiscal return is somewhat higher.

## Sources & assumptions

- Minviro Final Report §2: 30-yr dynamic I-O (NI 2016 + Scotland 2016 multipliers), GVA/output/jobs scenario anchors (basic-exploration ~3 jobs/yr; one-mine 3a ~73 jobs/£7.3m/£1.6m; two-mine 4b ~430 jobs/£43m/£9m p.a.), WACC 11.26%
- Minviro positive socio-economic taxonomy: jobs, multiplier effects, taxes & royalties, infrastructure, training/skills, employment of nationals/locals, in-country procurement
- Minviro retained-employment analysis + Galmoy/Lisheen leakage comparison; skilled-labour-shortage limitation
- Tax proxy ~25% of GVA (PROXY, excludes royalties); export intensities & avoided-import valuation PROXY (replace with HMRC Regional Trade Statistics + firm offtake data)
- Investment pipeline from company_register.csv (named-firm investment_gbp_m)

*BCR uses discounted GVA vs notional public cost; avoided imports, tax and exports are reported separately to avoid double-counting value-added.*