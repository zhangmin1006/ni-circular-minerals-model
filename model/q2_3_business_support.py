"""
Q2.3 — "What support is needed for businesses to participate in the minerals
supply chain?"

The experiment has two lenses:
  1) UPSTREAM SUPPLY SHOCK — an import constraint on critical minerals (imports
     capped at 60% of demand) plus a price spike, reflecting the real supply
     concentration (China 74% REE, DRC 70% Co, Australia 44% Li). The shock
     creates an unmet-demand "supply gap" unless domestic + recycled supply fills
     it — the threat that hits downstream firms.
  2) FIRM CHALLENGES BY STAGE — firms sit at different stages (primary, midstream
     processing/collection, downstream manufacturing, enabling) and face different
     binding constraints, so they need different support.

We map the named firms to supply-chain stages, run the shock with no support and
with stage-targeted government support packages, and read off which support best
helps each stage participate and withstand the shock.

Run:  python q2_3_business_support.py
Outputs: outputs/q2_3_support_scenarios.csv, outputs/q2_3_stage_support.csv,
         outputs/q2_3_memo.md
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import seed_parameters as P
from coupling import CoupledModel
from company_data import (
    DOWNSTREAM_ROLES, MINING_ROLES, RECYCLING_ROLES, firm_capital_pipeline, parse_firms,
)

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

GREEN_DEMAND = {"REE_magnet": P.DEMAND_GROWTH_WIND, "Lithium": P.DEMAND_GROWTH_EV,
                "Cobalt": 0.06, "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}

# Upstream supply shock: cap critical-mineral imports at 60% of demand + price spike.
SHOCK_IMPORT_CAP = {m: 0.60 for m in P.CRITICAL_MINERALS}
SHOCK_PRICE = {"Lithium": 0.12, "REE_magnet": 0.11, "Cobalt": 0.10,
               "Nickel": 0.07, "Copper": 0.06}

# Stage-targeted government support packages (the "support needed" per stage).
SUPPORT = {
    "upstream": {   # primary / mining firms
        "finance_support": 0.8, "exploration_grant": 0.12, "permit_years": 2,
        "community_benefit": 0.4,
    },
    "midstream": {  # processing / recovery + collection (the binding capacity gap)
        "recycling_grant": 0.4, "innovation_grant": 0.6, "energy_cost_index": 0.90,
        "secondary_market_support": 0.6, "collection_infrastructure": 1.0,
        "product_passport": 0.6,
    },
    "downstream": {  # manufacturers using the material
        "recycled_content_procurement": 0.5, "secondary_market_support": 0.5,
        "local_supplier_support": 0.7, "design_standards": 0.6,
    },
    "enabling": {   # cross-cutting skills + supplier development
        "skills_support": 0.8, "local_supplier_support": 0.5,
    },
}


def _merge(*dicts):
    out = {}
    for d in dicts:
        for k, v in d.items():
            out[k] = max(out.get(k, 0.0), v) if k != "permit_years" else min(
                out.get(k, 99), v)
    return out


SCENARIOS = {
    "0_no_shock_no_support": {"shock": False, "policy": {},
                              "label": "No shock, no support (reference)"},
    "shock_no_support": {"shock": True, "policy": {},
                         "label": "Upstream shock, no support"},
    "shock_upstream_support": {"shock": True, "policy": SUPPORT["upstream"],
                               "label": "Shock + upstream (primary) support"},
    "shock_midstream_support": {"shock": True, "policy": SUPPORT["midstream"],
                                "label": "Shock + midstream (processing/collection) support"},
    "shock_downstream_support": {"shock": True, "policy": SUPPORT["downstream"],
                                 "label": "Shock + downstream (manufacturer) support"},
    "shock_enabling_support": {"shock": True, "policy": SUPPORT["enabling"],
                               "label": "Shock + enabling (skills/supplier) support"},
    "shock_full_support": {"shock": True,
                           "policy": _merge(*SUPPORT.values()),
                           "label": "Shock + full cross-chain support"},
}


def run_scenario(name, cfg):
    m = CoupledModel(
        name=name, policy=cfg["policy"], demand_growth=GREEN_DEMAND,
        price_path=SHOCK_PRICE if cfg["shock"] else {},
        import_constraint=SHOCK_IMPORT_CAP if cfg["shock"] else None,
        seed=42, use_ree_pilot=True, adaptive=True, use_cge=True)
    df = m.run()
    last = df.iloc[-1]
    return {
        "scenario": name, "label": cfg["label"],
        "crit_supply_gap_end": round(float(last["crit_supply_gap"]), 3),
        "crit_recycled_share_end": round(float(last["crit_recycled_share"]), 3),
        "crit_domestic_share_end": round(float(last["crit_domestic_share"]), 3),
        "crit_import_share_end": round(float(last["crit_import_share"]), 3),
        "single_country_exposure_end": round(float(last["crit_max_single_country"]), 3),
        "recycling_substitution_end": round(float(last["recycling_substitution"]), 3),
        "mining_jobs_end": round(float(last["mining_jobs"]), 1),
        "recycling_jobs_end": round(float(last["recycling_jobs"]), 1),
        "manufacturing_jobs_end": round(float(last["manufacturing_jobs"]), 1),
        "total_jobs_end": round(float(last["employment_total"]), 1),
        "cum_disc_gva_gbp_m": round(m.cumulative_discounted["gva"], 1),
    }


def stage_support_table():
    """Per-stage: firms, employees, binding challenge, shock exposure, the support
    instrument(s) needed, and the public-finance vehicle."""
    firms = parse_firms()

    def emp(roles):
        sel = [f for f in firms if f["role"] in roles]
        return len(sel), int(sum(f["employees"] for f in sel))

    n_up, e_up = emp(MINING_ROLES)
    n_mid, e_mid = emp(RECYCLING_ROLES)
    n_down, e_down = emp(DOWNSTREAM_ROLES)
    rows = [
        {"stage": "Upstream (primary/mining)", "firms": n_up, "employees": e_up,
         "binding_challenge": "Finance + social licence + permitting; ~20-yr lead time",
         "shock_exposure": "Opportunity (price signal) — if it can be financed/permitted",
         "support_needed": "NWF/UKEF co-investment, exploration grant, faster permitting, community-benefit scheme",
         "model_levers": "finance_support, exploration_grant, permit_years, community_benefit"},
        {"stage": "Midstream (processing/recovery + collection)", "firms": n_mid, "employees": e_mid,
         "binding_challenge": "Capacity gap (1 processor), feedstock collection, energy cost",
         "shock_exposure": "Opportunity (substitution) — but capacity-constrained",
         "support_needed": "Capital grants, BICS energy support, R&D, offtake guarantees, collection/DRS infrastructure",
         "model_levers": "recycling_grant, energy_cost_index, innovation_grant, secondary_market_support, collection_infrastructure"},
        {"stage": "Downstream (manufacturers)", "firms": n_down, "employees": e_down,
         "binding_challenge": "Input-cost/price volatility, supply insecurity, secondary-material access",
         "shock_exposure": "Threat (input-cost squeeze + supply gap)",
         "support_needed": "Recycled-content procurement, secondary-materials marketplace, supplier development, ecodesign",
         "model_levers": "recycled_content_procurement, secondary_market_support, local_supplier_support, design_standards"},
        {"stage": "Enabling (equipment + skills)", "firms": "—", "employees": "—",
         "binding_challenge": "Skills pipeline, market access for equipment makers",
         "shock_exposure": "Indirect — enables the other stages to respond",
         "support_needed": "Green-skills academy, cluster + supplier-development, export support",
         "model_levers": "skills_support, local_supplier_support"},
    ]
    return pd.DataFrame(rows).set_index("stage")


def main():
    rows = [run_scenario(n, c) for n, c in SCENARIOS.items()]
    sc = pd.DataFrame(rows).set_index("scenario")
    shock = sc.loc["shock_no_support"]
    # resilience deltas vs the unsupported shock
    sc["d_supply_gap_pp"] = ((sc["crit_supply_gap_end"] - shock["crit_supply_gap_end"]) * 100).round(2)
    sc["d_total_jobs"] = (sc["total_jobs_end"] - shock["total_jobs_end"]).round(1)
    sc["d_cum_gva_gbp_m"] = (sc["cum_disc_gva_gbp_m"] - shock["cum_disc_gva_gbp_m"]).round(1)
    sc.to_csv(os.path.join(OUT, "q2_3_support_scenarios.csv"))

    stages = stage_support_table()
    stages.to_csv(os.path.join(OUT, "q2_3_stage_support.csv"))

    print("=" * 115)
    print("Q2.3 — BUSINESS SUPPORT under an upstream supply shock (30-yr, STPR 3.5%)")
    print("=" * 115)
    show = ["label", "crit_supply_gap_end", "crit_recycled_share_end", "crit_domestic_share_end",
            "mining_jobs_end", "recycling_jobs_end", "manufacturing_jobs_end",
            "cum_disc_gva_gbp_m"]
    with pd.option_context("display.width", 240, "display.max_columns", None,
                           "display.max_colwidth", 42):
        print(sc[show].to_string())

    _write_memo(sc, stages)
    print("\nWritten: outputs/q2_3_support_scenarios.csv, q2_3_stage_support.csv, q2_3_memo.md")


def _md_table(df, cols, index_name):
    out = [f"| {index_name} | " + " | ".join(cols) + " |",
           "|" + "---|" * (len(cols) + 1)]
    for idx, r in df.iterrows():
        out.append(f"| {idx} | " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _write_memo(sc, stages):
    ref = sc.loc["0_no_shock_no_support"]
    shock = sc.loc["shock_no_support"]
    full = sc.loc["shock_full_support"]
    # best single-stage support by jobs protected
    singles = sc.loc[["shock_upstream_support", "shock_midstream_support",
                      "shock_downstream_support", "shock_enabling_support"]]
    best = singles.sort_values("d_total_jobs", ascending=False).index[0]

    lines = []
    lines.append("# Q2.3 — What support do businesses need to participate in the minerals supply chain?\n")
    lines.append("**Method:** an upstream supply shock (critical-mineral imports capped at 60% of "
                 "demand + price spike, reflecting China 74% REE / DRC 70% Co / Australia 44% Li "
                 "concentration) is run with no support and with stage-targeted government support, "
                 "over 30 years. Firms are mapped to supply-chain stages; outcomes are read by stage. "
                 "Figures are model behaviour, not forecasts.\n")

    lines.append("## The shock hits stages differently\n")
    lines.append(f"- Without support the shock opens a **critical-mineral supply gap of "
                 f"{shock['crit_supply_gap_end']:.0%}** (unmet demand) and pushes single-country "
                 f"exposure to {shock['single_country_exposure_end']:.0%} — the **downstream "
                 f"manufacturers** carry this as input-cost and supply insecurity.")
    lines.append(f"- The same shock is an **opportunity for upstream and midstream firms**: higher "
                 f"prices lift recovery and mining viability (recycled share "
                 f"{ref['crit_recycled_share_end']:.0%} → {shock['crit_recycled_share_end']:.0%}), "
                 f"but only if they have the finance/capacity to respond.\n")

    lines.append("## Support needed, by supply-chain stage\n")
    lines.append(_md_table(stages, ["firms", "employees", "binding_challenge",
                                    "shock_exposure", "support_needed", "model_levers"], "stage"))

    lines.append("\n## What the model says each support package does (under the shock)\n")
    lines.append(_md_table(sc, ["label", "crit_supply_gap_end", "crit_recycled_share_end",
                                "crit_domestic_share_end", "total_jobs_end", "cum_disc_gva_gbp_m",
                                "d_total_jobs"], "scenario"))
    lines.append(f"\n- **Most resilience per single package:** `{best}` "
                 f"({sc.loc[best, 'label']}) — +{sc.loc[best, 'd_total_jobs']:.0f} jobs vs the "
                 f"unsupported shock.")
    down = sc.loc["shock_downstream_support"]
    lines.append(f"- **Midstream support closes the supply gap** (builds the recovery capacity that "
                 f"converts the shock into domestic secondary supply: recycled share rises to "
                 f"{sc.loc['shock_midstream_support', 'crit_recycled_share_end']:.0%}); **upstream "
                 f"support** brings domestic primary forward where social licence allows "
                 f"(domestic share to {sc.loc['shock_upstream_support', 'crit_domestic_share_end']:.0%}).")
    lines.append(f"- **Crucial sequencing finding:** *downstream support alone barely moves the dial* "
                 f"under the shock (GVA £{down['cum_disc_gva_gbp_m']}m vs £{shock['cum_disc_gva_gbp_m']}m "
                 f"unsupported) — manufacturers cannot buy recycled content that does not yet exist. "
                 f"Recycled-content procurement and supplier development only pay off **once midstream "
                 f"capacity is built**, so downstream support must be sequenced with (or after) "
                 f"midstream investment.")
    lines.append(f"- **Full cross-chain support** cuts the supply gap to "
                 f"{full['crit_supply_gap_end']:.0%} and lifts total jobs to {full['total_jobs_end']:.0f} "
                 f"(+{full['d_total_jobs']:.0f} vs unsupported shock), £{full['cum_disc_gva_gbp_m']}m "
                 f"discounted GVA.\n")

    lines.append("## Recommendations (stage-differentiated business support)\n")
    lines.append("1. **Upstream firms** need *capital and confidence*: National Wealth Fund / UK "
                 "Export Finance co-investment and guarantees, faster/clearer permitting, and a "
                 "community-benefit scheme to convert price signals into actual domestic supply.")
    lines.append("2. **Midstream processors/recyclers** (the binding capacity gap) need *capex + "
                 "operating-cost relief + demand certainty*: capital grants, BICS-style energy "
                 "support, R&D co-funding, offtake guarantees, and collection/DRS infrastructure.")
    lines.append("3. **Downstream manufacturers** need *supply security and secondary-material "
                 "access*: recycled-content procurement, a secondary-materials marketplace, "
                 "supplier-development support, and ecodesign standards.")
    lines.append("4. **Cross-cutting:** a green-skills academy and a minerals/circular cluster "
                 "(anchored on CDE/Terex equipment makers and QUB) so every stage can deliver.\n")

    lines.append("*Behavioural thresholds and the shock magnitude are PROXY; calibrate with "
                 "firm-level survey, trade-exposure and licensing data.*")

    with open(os.path.join(OUT, "q2_3_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
