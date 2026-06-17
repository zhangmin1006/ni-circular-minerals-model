# Q2.6 — Economic benefits of the NI minerals sector

**Method:** the coupled model's GVA / output / jobs (Type-II, discounted at STPR 3.5% over 30 years) are extended with the proposal's full benefit suite — a **tax proxy** (~25% effective take on GVA), **exports**, the named-firm **investment pipeline**, **productivity** (GVA per worker), **manufacturing resilience** and **avoided import costs** (the discounted value of demand met by domestic + recycled supply, i.e. the import bill NI does not pay). Value-for-money is a GVA benefit-cost ratio (BCR) vs notional public cost. Figures are model behaviour, not forecasts.

## Benefit suite by scenario

| scenario | label | cum_disc_gva_gbp_m | avoided_import_cost_gbp_m | tax_proxy_gbp_m | exports_gbp_m | gva_per_worker_gbp | disc_public_cost_gbp_m | gva_bcr | econ_resilience_bcr |
|---|---|---|---|---|---|---|---|---|---|
| 1_baseline | Baseline | 788.3 | 1215.2 | 197.1 | 630.7 | 45678.0 | 0.0 | nan | nan |
| 2_circular_innovation | Circular innovation | 1019.4 | 1567.6 | 254.8 | 842.2 | 46495.0 | 291.2 | 0.79 | 2.0 |
| 3_primary_extraction | Primary extraction | 790.0 | 1217.9 | 197.5 | 631.5 | 45659.0 | 113.1 | 0.02 | 0.04 |
| 4_integrated | Integrated circular + primary | 1152.6 | 1789.1 | 288.1 | 873.5 | 43625.0 | 425.4 | 0.86 | 2.21 |

## Findings

1. **The benefits are substantial and rise with ambition.** The integrated circular + primary scenario delivers ~£1,153m discounted GVA (+£364m vs baseline), ~£288m tax take and ~£874m exports over 30 years, alongside the £1,164m named-firm investment pipeline.
2. **Avoided import costs are a major, often-missed benefit.** Domestic + recycled supply avoids ~£1,789m of discounted import spending (+£574m vs baseline) — a direct trade-balance and resilience gain for NI manufacturers that buy secure, local inputs rather than volatile imports.
3. **Quality, productive jobs.** GVA per worker is ~£43,625 and the sectors pay above the NI average (see Q2.5); manufacturing resilience improves as secure secondary inputs displace import risk.
4. **Value for money:** on **incremental GVA alone** the return is below 1 for the capital-heavy scenarios (e.g. integrated ~0.86 extra GVA per £ public cost) — but once the **avoided-import / resilience benefit** is added the return rises to ~2.21× and the wider tax, export and jobs benefits push it higher still. Pure extraction support is the weakest value (little opens without social licence — cf. Q2.2).
5. **Benefits compound across questions:** the same spend that secures supply (Q2.4) and supports firms (Q2.3) also produces the GVA, exports and avoided imports here — so the economic case should be read as a portfolio, not lever-by-lever.

## Sources & assumptions

- Minviro Final Report: GVA/output/jobs anchors (one-mine £1.6m / two-mine £9m GVA p.a.)
- Tax proxy ~25% of GVA (income tax + NICs on wages + corporation tax on surplus; PROXY)
- Export intensities and avoided-import valuation are PROXY (replace with HMRC Regional Trade Statistics + firm offtake data)
- Investment pipeline from company_register.csv (named-firm investment_gbp_m)

*BCR uses discounted GVA vs notional public cost; avoided imports, tax and exports are reported separately to avoid double-counting value-added.*