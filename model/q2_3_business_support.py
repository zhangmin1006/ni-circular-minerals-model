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

# ---------------------------------------------------------------------------
# SHOCK — grounded in the strategy documents. Vision 2035 warns supply chains are
# "vulnerable to shocks such as natural disasters, war or geopolitical fallout",
# driven by concentration. We model a DOMINANT-SUPPLIER LOSS: per-mineral import
# caps = 1 - (single-country share) using the cited 2023 concentration
# (China 74% REE, DRC 70% Co, Australia 44% Li, ...; BGS/Idoine 2025 via GSNI
# OR25042), plus a price spike. The most concentrated minerals are hit hardest.
CONCENTRATION = {   # dominant single-country share of supply, 2023
    "REE_magnet": 0.74, "Cobalt": 0.70, "Antimony": 0.70, "Aluminium": 0.35,
    "Lithium": 0.44, "Nickel": 0.40, "Copper": 0.30,
}


def shock_caps(loss_factor=1.0):
    """Import cap per critical mineral if `loss_factor` x the dominant supplier is
    cut off (1.0 = lose the dominant single country entirely)."""
    return {m: max(0.0, 1.0 - min(1.0, loss_factor * CONCENTRATION.get(m, 0.3)))
            for m in P.CRITICAL_MINERALS}


SHOCK_IMPORT_CAP = shock_caps(1.0)          # central: lose the dominant supplier
SHOCK_PRICE = {"Lithium": 0.12, "REE_magnet": 0.11, "Cobalt": 0.10,
               "Nickel": 0.07, "Copper": 0.06}

# ---------------------------------------------------------------------------
# SUPPORT — each lever mapped to a NAMED instrument in the UK strategy documents.
#   finance_support  -> National Wealth Fund + UK Export Finance (Vision 2035)
#   energy_cost_index-> British Industrial Competitiveness Scheme (BICS)
#   permit_years     -> Environment Agency priority-tracked service
#   skills_support   -> Skills England + DWP
#   innovation_grant -> Innovate UK CLIMATES + Faraday/ReLiB R&D
#   secondary_market_support -> UKEF offtake + secondary-materials marketplace
#   collection_infrastructure/product_passport -> WEEE/DRS + EPR
#   local_supplier_support -> supplier development (fixes Minviro leakage)
#   community_benefit -> ESG/community-benefit (social licence; Curraghinalt)
#   strategic_stockpile -> Vision 2035 defence stockpiling / procurement reserve
SUPPORT = {
    "upstream": {   # primary / mining firms: finance, permits, social licence
        "finance_support": 0.8, "exploration_grant": 0.12, "permit_years": 2,
        "community_benefit": 0.4,
    },
    "midstream": {  # processing/recovery + collection: the binding capacity gap
        "recycling_grant": 0.4, "innovation_grant": 0.6, "energy_cost_index": 0.90,
        "secondary_market_support": 0.6, "collection_infrastructure": 1.0,
        "product_passport": 0.6,
    },
    "downstream": {  # manufacturers: supply security + secondary-material access
        "recycled_content_procurement": 0.5, "secondary_market_support": 0.5,
        "local_supplier_support": 0.7, "design_standards": 0.6,
    },
    "enabling": {   # cross-cutting: skills + supplier development + stockpile
        "skills_support": 0.8, "local_supplier_support": 0.5,
        "strategic_stockpile": 0.6,
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
        "supply_gap_early7": round(float(df.iloc[:7]["crit_supply_gap"].mean()), 3),
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


def run_with_shock(caps, policy):
    """Run one (shock severity x support) cell; return resilience metrics."""
    m = CoupledModel(
        name="sev", policy=policy, demand_growth=GREEN_DEMAND, price_path=SHOCK_PRICE,
        import_constraint=caps, seed=42, use_ree_pilot=True, adaptive=True, use_cge=True)
    df = m.run()
    last = df.iloc[-1]
    return {
        "supply_gap_early7": round(float(df.iloc[:7]["crit_supply_gap"].mean()), 3),
        "supply_gap_end": round(float(last["crit_supply_gap"]), 3),
        "recycled_share_end": round(float(last["crit_recycled_share"]), 3),
        "domestic_share_end": round(float(last["crit_domestic_share"]), 3),
        "total_jobs_end": round(float(last["employment_total"]), 1),
        "cum_disc_gva_gbp_m": round(m.cumulative_discounted["gva"], 1),
    }


# Shock severity = how much of the dominant single supplier is lost (loss factor).
SEVERITIES = {"mild_half_supplier": 0.5, "moderate_supplier_lost": 1.0,
              "severe_+25pct": 1.25, "extreme_+50pct": 1.5}
SWEEP_PACKAGES = {
    "no_support": {},
    "upstream": SUPPORT["upstream"],
    "midstream": SUPPORT["midstream"],
    "full": _merge(*SUPPORT.values()),
}


def per_mineral_gap(caps=None):
    """Per-mineral end-year supply gap under the (no-support) dominant-supplier
    shock — shows how the aggregate masks concentrated-mineral exposure."""
    caps = caps or SHOCK_IMPORT_CAP
    m = CoupledModel(name="permineral", policy={}, demand_growth=GREEN_DEMAND,
                     price_path=SHOCK_PRICE, import_constraint=caps, seed=42,
                     use_ree_pilot=True, adaptive=True, use_cge=True)
    m.run()
    last = m.mfa.history[-len(m.mfa.minerals):]
    return {r["mineral"]: round(r["supply_gap_share"], 3) for r in last
            if r["mineral"] in P.CRITICAL_MINERALS and r["supply_gap_share"] > 0.001}


def shock_severity_sweep():
    rows = []
    for sev, factor in SEVERITIES.items():
        caps = shock_caps(factor)
        for pkg, pol in SWEEP_PACKAGES.items():
            r = run_with_shock(caps, pol)
            rows.append({"severity": sev, "supplier_loss_factor": factor,
                         "support": pkg, **r})
    return pd.DataFrame(rows)


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
         "binding_challenge": "Input-cost/price volatility, supply insecurity, secondary-material access, data/traceability",
         "shock_exposure": "Threat (input-cost squeeze + supply gap)",
         "support_needed": "Recycled-content procurement, secondary-materials marketplace, supplier development, ecodesign, product-passport data",
         "model_levers": "recycled_content_procurement, secondary_market_support, local_supplier_support, design_standards"},
        {"stage": "Enabling (equipment + skills + reserves)", "firms": "—", "employees": "—",
         "binding_challenge": "Skills pipeline, equipment market access, export finance, residual supply risk",
         "shock_exposure": "Cross-cutting — lets the chain respond and buffers the residual",
         "support_needed": "Green-skills academy (Skills England/DWP), cluster + supplier development, UKEF export support, strategic stockpile/procurement reserve",
         "model_levers": "skills_support, local_supplier_support, strategic_stockpile"},
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

    pmg = per_mineral_gap()
    sweep = shock_severity_sweep()
    sweep.to_csv(os.path.join(OUT, "q2_3_shock_severity.csv"), index=False)
    gap_pivot = sweep.pivot(index="severity", columns="support", values="supply_gap_end")
    gap_pivot = gap_pivot.reindex(list(SEVERITIES))[list(SWEEP_PACKAGES)]

    print("=" * 115)
    print("Q2.3 — BUSINESS SUPPORT under an upstream supply shock (30-yr, STPR 3.5%)")
    print("=" * 115)
    show = ["label", "supply_gap_early7", "crit_supply_gap_end", "crit_recycled_share_end",
            "crit_domestic_share_end", "mining_jobs_end", "recycling_jobs_end",
            "manufacturing_jobs_end", "cum_disc_gva_gbp_m"]
    with pd.option_context("display.width", 240, "display.max_columns", None,
                           "display.max_colwidth", 42):
        print(sc[show].to_string())

    print("\n" + "=" * 115)
    print("SHOCK-SEVERITY SWEEP — critical-mineral supply gap by severity x support package")
    print("=" * 115)
    print(gap_pivot.to_string())

    print("\nPer-mineral supply gap under the dominant-supplier shock (no support):")
    print("  " + ", ".join(f"{k} {v:.0%}" for k, v in
                           sorted(pmg.items(), key=lambda x: -x[1])))

    _write_memo(sc, stages, sweep, gap_pivot, pmg)
    print("\nWritten: q2_3_support_scenarios.csv, q2_3_stage_support.csv, "
          "q2_3_shock_severity.csv, q2_3_memo.md")


def _md_table(df, cols, index_name):
    out = [f"| {index_name} | " + " | ".join(cols) + " |",
           "|" + "---|" * (len(cols) + 1)]
    for idx, r in df.iterrows():
        out.append(f"| {idx} | " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _write_memo(sc, stages, sweep, gap_pivot, pmg):
    ref = sc.loc["0_no_shock_no_support"]
    shock = sc.loc["shock_no_support"]
    full = sc.loc["shock_full_support"]
    # best single-stage support by jobs protected
    singles = sc.loc[["shock_upstream_support", "shock_midstream_support",
                      "shock_downstream_support", "shock_enabling_support"]]
    best = singles.sort_values("d_total_jobs", ascending=False).index[0]

    lines = []
    lines.append("# Q2.3 — What support do businesses need to participate in the minerals supply chain?\n")
    lines.append("**Method (grounded in the strategy documents):** Vision 2035 warns supply chains "
                 "are *vulnerable to shocks such as natural disasters, war or geopolitical fallout* "
                 "driven by concentration. We model a **dominant-supplier loss** — per-mineral import "
                 "caps = 1 − (single-country share) using the cited 2023 concentration (China 74% REE, "
                 "DRC 70% Co, Australia 44% Li; BGS/Idoine 2025) — plus a price spike. Support levers "
                 "map to **named UK instruments** (NWF/UKEF, BICS, EA priority permitting, Skills "
                 "England, CLIMATES/Faraday R&D, UKEF offtake, defence stockpiling). Firms are mapped "
                 "to supply-chain stages; outcomes are read by stage. Figures are model behaviour, "
                 "not forecasts.\n")

    lines.append("## The shock hits stages differently\n")
    lines.append(f"- Without support the shock opens a **critical-mineral supply gap of "
                 f"{shock['crit_supply_gap_end']:.0%}** (unmet demand) and pushes single-country "
                 f"exposure to {shock['single_country_exposure_end']:.0%} — the **downstream "
                 f"manufacturers** carry this as input-cost and supply insecurity.")
    lines.append(f"- The same shock is an **opportunity for upstream and midstream firms**: higher "
                 f"prices lift recovery and mining viability (recycled share "
                 f"{ref['crit_recycled_share_end']:.0%} → {shock['crit_recycled_share_end']:.0%}), "
                 f"but only if they have the finance/capacity to respond.")
    pmg_str = ", ".join(f"{k} {v:.0%}" for k, v in sorted(pmg.items(), key=lambda x: -x[1]))
    lines.append(f"- **The aggregate gap masks acute, mineral-specific exposure.** Per mineral the "
                 f"unmet-demand gap is: {pmg_str}. The most single-source-concentrated minerals "
                 f"(REE, antimony, cobalt) lose almost their entire supply, while bulk metals "
                 f"(copper, aluminium) are barely affected — so support should be *targeted by "
                 f"mineral and by the firms that depend on it*, not spread evenly.\n")

    lines.append("## Support needed, by supply-chain stage\n")
    lines.append(_md_table(stages, ["firms", "employees", "binding_challenge",
                                    "shock_exposure", "support_needed", "model_levers"], "stage"))

    lines.append("\n## What the model says each support package does (under the shock)\n")
    lines.append(_md_table(sc, ["label", "supply_gap_early7", "crit_supply_gap_end",
                                "crit_recycled_share_end", "crit_domestic_share_end",
                                "total_jobs_end", "cum_disc_gva_gbp_m", "d_total_jobs"], "scenario"))
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
    enab = sc.loc["shock_enabling_support"]
    mids = sc.loc["shock_midstream_support"]
    ups = sc.loc["shock_upstream_support"]
    lines.append(f"- **Stockpile = a bridge, not a fix (finite, depleting reserve).** The enabling "
                 f"package's Vision-2035 *strategic stockpile* slashes the **early-shock** gap "
                 f"(first 7 yrs) from {shock['supply_gap_early7']:.0%} to {enab['supply_gap_early7']:.0%}, "
                 f"but once the reserve depletes the **end-state** gap is back to "
                 f"{enab['crit_supply_gap_end']:.0%} (= unsupported) and it builds no industry "
                 f"(GVA £{enab['cum_disc_gva_gbp_m']}m). By contrast, midstream support gives durable "
                 f"protection (end gap {mids['crit_supply_gap_end']:.0%}, recycled share "
                 f"{mids['crit_recycled_share_end']:.0%}, GVA £{mids['cum_disc_gva_gbp_m']}m) but little "
                 f"*immediate* relief (early gap {mids['supply_gap_early7']:.0%}); upstream mining gives "
                 f"**no early relief at all** (early gap {ups['supply_gap_early7']:.0%} — mines take "
                 f"years to permit/build).")
    lines.append(f"- **So the sequencing is: stockpile to bridge the first years while midstream + "
                 f"upstream capacity is built.** Full support uses the stockpile early (gap "
                 f"{full['supply_gap_early7']:.0%}) and the new capacity later (end gap "
                 f"{full['crit_supply_gap_end']:.0%}).")
    lines.append(f"- **Full cross-chain support** cuts the supply gap to "
                 f"{full['crit_supply_gap_end']:.0%} and lifts total jobs to {full['total_jobs_end']:.0f} "
                 f"(+{full['d_total_jobs']:.0f} vs unsupported shock), £{full['cum_disc_gva_gbp_m']}m "
                 f"discounted GVA.\n")

    lines.append("## Resilience across shock severity (½ → 1.5× of the dominant supplier lost)\n")
    lines.append("Critical-mineral **supply gap** (unmet demand) by shock severity (how much of the "
                 "dominant single supplier is cut off) and support package — lower is more resilient. "
                 "The `full` package includes the Vision-2035 strategic-stockpile/procurement reserve:")
    lines.append("")
    lines.append(_md_table(gap_pivot.round(3), list(gap_pivot.columns), "severity"))
    g = gap_pivot
    mild_none = g.loc["mild_half_supplier", "no_support"]
    ext_none = g.loc["extreme_+50pct", "no_support"]
    ext_mid, ext_full = g.loc["extreme_+50pct", "midstream"], g.loc["extreme_+50pct", "full"]
    lines.append(f"\n- **The gap scales with severity:** unsupported, it rises from "
                 f"{mild_none:.0%} (mild) to {ext_none:.0%} (extreme).")
    lines.append(f"- **Support is more valuable the more severe the shock** — but no single stage "
                 f"is enough under an extreme shock: midstream support alone leaves a "
                 f"{ext_mid:.0%} gap, whereas **full cross-chain support holds it to "
                 f"{ext_full:.0%}**. Mild shocks can be absorbed by midstream capacity alone; "
                 f"severe shocks need upstream + midstream + downstream together.")
    lines.append(f"- **Implication:** the depth of support should scale with assessed supply risk. "
                 f"For low-risk minerals, fund the midstream (recovery) capacity; for high-risk, "
                 f"single-source-dependent minerals (REE/Co/Li), the full cross-chain package is "
                 f"justified.\n")

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

    lines.append("## Sources\n")
    for s in (
        "UK Critical Minerals Strategy — Vision 2035 (DBT, Jan 2026): NWF/UKEF, BICS, EA "
        "priority permitting, Skills England/DWP, defence stockpiling, offtake, partnerships",
        "Model proposal Q2.3 taxonomy: finance, skills, data, permits, offtake, export, "
        "recycling infrastructure, supplier-development support",
        "GSNI/BGS — Critical Minerals and the Circular Economy in NI (OR25042, 2025): ~80% UK "
        "metals exported for processing; supply concentration; ~20-yr lead times; declining grades",
        "BGS/Idoine et al. (2025): 2023 single-country supply concentration (REE 74%, Co 70%, Li 44%)",
        "Minviro Final Report: local-procurement leakage and skills constraints",
        "Innovate UK CLIMATES (£15m) + Faraday/ReLiB (£34m); DEFRA DRS impact assessment",
    ):
        lines.append(f"- {s}")
    lines.append("\n*Behavioural thresholds and the shock magnitude are PROXY; calibrate with "
                 "firm-level survey, trade-exposure and licensing data.*")

    with open(os.path.join(OUT, "q2_3_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
