# Data Audit — NI Circular Minerals model

Programmatic audit of the data inputs behind the model and the Q2.1-2.7 experiments: provenance/status, register-vs-code consumption, firm-register completeness, consistency checks and in-code parameter coverage. Regenerate with `python audit_data.py`.

## 1. Data register (`data_register.csv`)

- **80 parameters.** Status: real 47, proxy 19, desk_verified 11, web_verified 2, gap 1.
- **Placeholder-source (7)** — biggest provenance gaps: `io_technical_coefficients`, `io_employment_coefficients`, `io_co2_coefficients`, `local_procurement_share_mining`, `in_use_stock_ree_tonnes`, `ni_demand_growth_ev`, `ni_demand_growth_wind`.
- **Declared gaps (1):** `in_use_stock_ree_tonnes`.

## 2. Are registered parameters actually used?

| seed_parameters attribute | consumed in | verdict |
|---|---|---|
| `COLLECTION_RATE_WEEE` | — (only seed_parameters.py) | **DEFINED-BUT-UNUSED** |
| `DEMAND_GROWTH_EV` | `q2_1_circularity_interventions.py`, `q2_2_opportunities_challenges.py`, `q2_3_business_support.py`, `q2_4_secure_supply.py`, `q2_5_employment_skills.py`, `q2_6_economic_benefits.py`, `q2_7_negative_impacts.py`, `q_demand_supply_strategy.py`, `run_mvm.py` | consumed |
| `DEMAND_GROWTH_WIND` | `q2_1_circularity_interventions.py`, `q2_2_opportunities_challenges.py`, `q2_3_business_support.py`, `q2_4_secure_supply.py`, `q2_5_employment_skills.py`, `q2_6_economic_benefits.py`, `q2_7_negative_impacts.py`, `q_demand_supply_strategy.py`, `run_mvm.py` | consumed |
| `LOCAL_PROCUREMENT_SHARE_MINING` | — (only seed_parameters.py) | **DEFINED-BUT-UNUSED** |
| `RECOVERY_YIELDS` | `mfa_module.py` | consumed |

*Finding: parameters flagged DEFINED-BUT-UNUSED are loaded from the register but drive no output — their register `WIRED:` note overstates their effect.*

## 3. Firm register (`company_register.csv`)

- **21 firms**, all with a source URL. Evidence: web_verified 13, desk_verified 8.
- `investment_gbp_m`: only **6/21** firms carry a non-zero value.
- `annual_capacity_tonnes`: only **2/21** firms carry a non-zero value.
- The eight `*_score` columns (resource/capacity/feedstock/demand/local-procurement/planning-risk/skills/circularity) are **desk heuristics (0-1)**, not measured — the single largest proxy block on the firm side.

## 4. Consistency checks

- **REE single-country concentration is inconsistent across sources:** `MINERAL_PARAMS` = 0.74 (BGS mine supply) and register = 0.74, but the REE pilot overrides it to **0.87** (refined/magnet, China) — and every experiment runs `use_ree_pilot=True`, so the model actually uses 0.87. Both are defensible (mine vs refined) but the run value 0.87 is not in the register.
- **Two demand bases coexist:** `run_mvm` and Q2.5-2.7 use the register-wired GREEN_DEMAND (EV 0.12 / wind 0.08); the demand-supply study uses annex-derived CAGRs (Li ~26.5% ...). Same model, different scenario inputs — intended, but document so they are not conflated.

## 5. In-code parameters (calibration coefficients) outside the register

The register curates headline/sourced data + key proxies. The bulk of structural & behavioural calibration lives in code as `PROXY`-commented constants, **not** itemised in the register. Module-level constants found:

- **`abm_module.py`**: `PROXY_DEPOSITS`, `SOCIAL_LICENCE_FLOOR`
- **`cge_module.py`**: `SIGMA_ARM`, `SIGMA_E`, `SIGMA_VA`
- **`company_data.py`**: `CONFIDENCE`, `LIFECYCLE_WEIGHT`
- **`coupling.py`**: `STOCKPILE_DEPTH`, `STOCKPILE_RATE`
- **`employment_module.py`**: `NI_MEDIAN_ANNUAL_WAGE`, `SECTOR_WAGE_INDEX`, `SKILL_SPLIT`
- **`impact_module.py`**: `ESG_MAX_MITIGATION`, `ESG_REF`, `PRESSURE`, `RECYCLING_CO2_VS_PRIMARY`
- **`mfa_module.py`**: `MINERAL_PARAMS`, `MINERAL_PRICE_GBP_PER_T`
- **`q2_1_circularity_interventions.py`**: `GREEN_DEMAND`, `INTERVENTIONS`, `LEVER_COST`, `LEVER_COST_BOUNDS`, `LEVER_COST_SOURCE`
- **`q2_2_opportunities_challenges.py`**: `GREEN_DEMAND`, `SCENARIOS`
- **`q2_3_business_support.py`**: `CONCENTRATION`, `GREEN_DEMAND`, `SCENARIOS`, `SEVERITIES`, `SHOCK_IMPORT_CAP`, `SHOCK_PRICE`, `SUPPORT`, `SWEEP_PACKAGES`
- **`q2_4_secure_supply.py`**: `CONCENTRATION`, `COST`, `GREEN_DEMAND`, `PRICE_SPIKE`, `ROLES`, `SHOCKS`
- **`q2_5_employment_skills.py`**: `GREEN_DEMAND`, `SCENARIOS`
- **`q2_6_economic_benefits.py`**: `COST`, `EXPORT_SHARE_MINING`, `EXPORT_SHARE_RECYCLING`, `GREEN_DEMAND`, `SCENARIOS`, `TAX_RATE_ON_GVA`
- **`q2_7_negative_impacts.py`**: `GREEN_DEMAND`, `SCENARIOS`
- **`q_demand_supply_strategy.py`**: `ANNEX_CAGR`, `ANNEX_DEMAND_T`, `BASE_DEMAND`, `COMBINED`, `COMBINED_PRICE`, `CRMA`, `CRMA_PRICE`, `INDUSTRIAL`, `PLATEAU`, `SCENARIOS`, `SUSTAINABLE`, `TARGETS`, `VISION`
- **`run_mvm.py`**: `GREEN_DEMAND`, `SCENARIOS`
- **`sam_module.py`**: `EXPORT_INTENSITY`, `GOV_DEMAND_SHARE`, `GVA_SHARE`, `HH_SAVINGS_RATE`, `LABOUR_SHARE_OF_VA`, `NI_TOTAL_GVA_GBP_M`
- **`seed_parameters.py`**: `ANCHORS`, `CO2_COEFF`, `COLLECTION_RATE_WEEE`, `DEMAND_GROWTH_EV`, `DEMAND_GROWTH_WIND`, `DOMESTIC_INTENSITY`, `EMP_COEFF`, `GVA_COEFF`, `HH_CONSUMPTION`, `HORIZON`, `IMPORT_SHARE`, `LOCAL_CONSUMPTION_PROPENSITY`, `LOCAL_PROCUREMENT_SHARE_MINING`, `MINING_COST_OF_EQUITY`, `PM_COEFF`, `RECOVERY_YIELDS`, `STPR`, `TARGETS_2035`, `WAGE_SHARE_OF_GVA`
- **`spatial_module.py`**: `DISTRICTS`, `FIRM_BLEND_WEIGHT`, `SHARES`

*Plus non-constant proxies: the 8x8 I-O `A` matrix and the GVA/EMP/CO2/PM satellite vectors (seed_parameters), the ABM decision thresholds (dev hurdle 0.45, social-licence floor 0.4, risk/price coefficients), and per-scenario policy bundles. These are the model's biggest aggregate proxy dependency.*

## 6. Findings & recommendations (severity-ranked)

1. **[High] The I-O/SAM core is proxy.** `io_technical_coefficients`, `io_employment_coefficients`, `io_co2_coefficients` are placeholders; the A-matrix is a tuned proxy. *Action:* commission a regionalised NISRA Supply-Use + Scottish I-O (FLQ+RAS) and NI SAM — the single highest-value data investment.
2. **[Medium] Firm scores are desk heuristics.** The 0-1 capacity/feedstock/risk/procurement/skills scores drive ABM behaviour. *Action:* a firm-level survey (capacity tonnage, employment, local-procurement, planning status).
3. **[Medium] NI critical-mineral waste/recycling flows are a gap** (`collection_rate_weee` and the MFA collection/recovery seeds are UK-scaled). *Action:* DAERA/NIEA + recycler survey to build the NI MFA.
4. **[Low] Tidy defined-but-unused registered params** (`COLLECTION_RATE_WEEE`, `LOCAL_PROCUREMENT_SHARE_MINING`): either wire them into the MFA/coupling or relabel their register note from `WIRED` to `documented (not yet consumed)`.
5. **[Low] Reconcile the REE concentration** (0.74 mine vs 0.87 refined) and add the 0.87 run value to the register; de-duplicate the `CONCENTRATION` and lever-`COST` maps that are repeated across q2_3/q2_4/q2_6.

*Overall: validation anchors and headline policy figures are sourced and CI-checked; the economic-structure and behavioural calibration remain proxy (flagged), so outputs are directional, not forecasts. The three gap datasets above convert it to a calibrated tool.*