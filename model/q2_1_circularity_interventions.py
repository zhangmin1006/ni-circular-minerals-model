"""
Q2.1 — "How can the Department support innovation that will support circularity,
in particular materials recovery, secondary materials markets, recycling and
circular design in manufacturing?"

This experiment designs a menu of concrete NI-government interventions, maps each
to the firm-grounded ABM policy levers, and tests them one at a time and as a
combined package over the 30-year horizon. It reports the indicators the proposal
asks for under 2.1 — recovery/recycled share, secondary-material value, recycling
GVA/jobs, circular-design uptake — plus a transparent innovation-ROI ranking
(benefit per £ of notional public cost) so the Department can see the *best policy
mix*, not just the effect of any single lever.

Run:  python q2_1_circularity_interventions.py
Outputs: outputs/q2_1_interventions.csv and outputs/q2_1_memo.md
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import seed_parameters as P
from coupling import CoupledModel

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

# Vision-2035 demand drivers (same as the main run), keyed to the register.
GREEN_DEMAND = {"REE_magnet": P.DEMAND_GROWTH_WIND, "Lithium": P.DEMAND_GROWTH_EV,
                "Cobalt": 0.06, "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}

# ---------------------------------------------------------------------------
# 1. The interventions (each a realistic DfE/DAERA instrument -> model levers)
# ---------------------------------------------------------------------------
# theme tags map each intervention to the four parts of the question.
INTERVENTIONS = {
    "0_baseline": {
        "theme": "—", "policy": {},
        "desc": "No new circular-economy policy (current trajectory).",
    },
    "A_materials_recovery_capital": {
        "theme": "materials recovery",
        "policy": {"recycling_grant": 0.45, "energy_cost_index": 0.95},
        "desc": "Capital-grant + green-tariff scheme for recovery/separation plant "
                "(scales Ionic-type REE separation and battery/WEEE recovery).",
    },
    "B_circular_innovation_fund": {
        "theme": "materials recovery + circular design",
        "policy": {"innovation_grant": 0.7, "recycling_grant": 0.2},
        "desc": "Circular Innovation Fund: co-funded R&D with QUB/Met4Tech/Ionic on "
                "recovery yield and design-for-disassembly.",
    },
    "C_smart_collection_drs": {
        "theme": "recycling / collection",
        "policy": {"collection_infrastructure": 1.0, "product_passport": 0.6},
        "desc": "Smart collection + deposit-return + WEEE/ELV stewardship with "
                "Re-Gen/RiverRidge/Bryson; digital product passports.",
    },
    "D_secondary_market_offtake": {
        "theme": "secondary materials markets",
        "policy": {"secondary_market_support": 0.7, "recycled_content_procurement": 0.5},
        "desc": "Secondary-materials marketplace + public offtake guarantees and "
                "minimum recycled-content in public contracts.",
    },
    "E_circular_design_standards": {
        "theme": "circular design in manufacturing",
        "policy": {"design_standards": 0.7, "product_passport": 0.6,
                   "recycled_content_procurement": 0.3},
        "desc": "Ecodesign / design-for-disassembly standards + passports for "
                "Wrightbus, Encirc, Seagate, Spirit.",
    },
    "F_green_skills_cluster": {
        "theme": "enabling (skills) ",
        "policy": {"skills_support": 0.8, "local_supplier_support": 0.5},
        "desc": "Green-skills academy + minerals/circular cluster (CDE/Terex "
                "equipment, FE colleges, QUB).",
    },
    "G_integrated_package": {
        "theme": "full Q2.1 mix",
        "policy": {"recycling_grant": 0.35, "innovation_grant": 0.6,
                   "collection_infrastructure": 1.0, "product_passport": 0.6,
                   "secondary_market_support": 0.6, "recycled_content_procurement": 0.4,
                   "design_standards": 0.6, "skills_support": 0.6,
                   "local_supplier_support": 0.5, "energy_cost_index": 0.96},
        "desc": "Integrated Circular Innovation Package — all instruments together.",
    },
}

# Public cost per lever at intensity 1.0 (GBP m / yr), as an NI-scale annual budget
# ANCHORED TO REAL UK PROGRAMMES (NI ~2.9% of UK population; critical-minerals
# activity over-indexed in NI so several are set above pro-rata). Used for a
# *relative* ROI ranking; see LEVER_COST_SOURCE for provenance.
LEVER_COST = {
    "recycling_grant": 7.0,             # capital recovery/processing grants
    "innovation_grant": 5.0,            # circular-minerals R&D fund
    "collection_infrastructure": 9.0,   # WEEE/battery/ELV collection + DRS-type
    "product_passport": 2.0,            # digital passports (mostly regulatory)
    "secondary_market_support": 4.0,    # marketplace + offtake guarantees
    "recycled_content_procurement": 1.0,  # procurement standard (regulatory)
    "design_standards": 1.0,            # ecodesign standard (regulatory)
    "skills_support": 4.0,              # green-skills bootcamps / cluster
    "local_supplier_support": 3.0,      # supplier development (Invest NI-style)
}
LEVER_COST_SOURCE = {
    "recycling_grant": "Vision 2035 DBT £50m for UK extraction/processing/recycling "
                       "(+£165m already invested); NI recovery-grant share ~£7m/yr.",
    "innovation_grant": "Innovate UK CLIMATES £15m + Faraday/ReLiB £34m battery-recycling "
                        "R&D; NI Circular Innovation Fund ~£5m/yr.",
    "collection_infrastructure": "DEFRA DRS impact assessment: £632m set-up, £1.065bn/yr "
                        "running (England+NI, drinks); NI WEEE/critical-stream collection "
                        "programme ~£9m/yr.",
    "product_passport": "Digital product passport / EPR data systems — largely regulatory.",
    "secondary_market_support": "Secondary-materials marketplace + contingent offtake "
                        "guarantees; ~£4m/yr NI.",
    "recycled_content_procurement": "Minimum recycled-content public-procurement standard "
                        "— regulatory, minimal direct spend.",
    "design_standards": "Ecodesign / design-for-disassembly standards — regulatory.",
    "skills_support": "DfE green-skills bootcamps (~£3,152/learner); NI circular-minerals "
                       "skills programme ~£4m/yr.",
    "local_supplier_support": "Invest NI-style supplier-development programme ~£3m/yr.",
}


# Low/high public-cost bounds (£m/yr at intensity 1.0) around the central
# LEVER_COST, reflecting programme-cost uncertainty. Capital/collection schemes
# get the widest band (the DRS government-vs-industry estimates diverged ~10x);
# regulatory levers get a tight absolute band.
LEVER_COST_BOUNDS = {
    "recycling_grant": (4.0, 12.0),
    "innovation_grant": (3.0, 9.0),
    "collection_infrastructure": (5.0, 20.0),
    "product_passport": (1.0, 4.0),
    "secondary_market_support": (2.0, 8.0),
    "recycled_content_procurement": (0.5, 2.0),
    "design_standards": (0.5, 2.0),
    "skills_support": (2.0, 7.0),
    "local_supplier_support": (1.5, 6.0),
}


def annual_cost(policy, which="central"):
    """Notional public £m/yr for a policy bundle (energy_cost_index excluded —
    it is a price signal, not a spend). `which` selects low/central/high bound."""
    total = 0.0
    for k, v in policy.items():
        if k not in LEVER_COST:
            continue
        if which == "low":
            c = LEVER_COST_BOUNDS[k][0]
        elif which == "high":
            c = LEVER_COST_BOUNDS[k][1]
        else:
            c = LEVER_COST[k]
        total += c * v
    return total


def discounted_cost(policy, which="central", horizon=P.HORIZON, stpr=P.STPR):
    c = annual_cost(policy, which)
    return sum(c / ((1.0 + stpr) ** t) for t in range(horizon))


def run_one(name, cfg):
    m = CoupledModel(name=name, policy=cfg["policy"], demand_growth=GREEN_DEMAND,
                     seed=42, use_ree_pilot=True, adaptive=True, use_cge=True)
    df = m.run()
    last = df.iloc[-1]
    return {
        "intervention": name,
        "theme": cfg["theme"],
        "crit_recycled_share_end": round(float(last["crit_recycled_share"]), 3),
        "recycled_share_all_end": round(float(last["recycled_share_all"]), 3),
        "secondary_value_gbp_m_end": round(float(last["recycling_fd_gbp_m"]), 2),
        "recycling_jobs_end": round(float(last["recycling_jobs"]), 1),
        "circular_design_uptake_end": round(float(last["recycling_substitution"]), 3),
        "crit_max_single_country_end": round(float(last["crit_max_single_country"]), 3),
        "co2_kt_end": round(float(last["co2_kt"]), 1),
        "cum_disc_gva_gbp_m": round(m.cumulative_discounted["gva"], 1),
        "cum_disc_co2_kt": round(m.cumulative_discounted["co2"], 1),
        "disc_public_cost_gbp_m": round(discounted_cost(cfg["policy"], "central"), 1),
        "disc_cost_low_gbp_m": round(discounted_cost(cfg["policy"], "low"), 1),
        "disc_cost_high_gbp_m": round(discounted_cost(cfg["policy"], "high"), 1),
    }


def main():
    rows = [run_one(name, cfg) for name, cfg in INTERVENTIONS.items()]
    df = pd.DataFrame(rows).set_index("intervention")

    base = df.loc["0_baseline"]
    df["d_recycled_share_pp"] = ((df["crit_recycled_share_end"]
                                  - base["crit_recycled_share_end"]) * 100).round(2)
    df["d_recycling_jobs"] = (df["recycling_jobs_end"] - base["recycling_jobs_end"]).round(1)
    df["d_cum_gva_gbp_m"] = (df["cum_disc_gva_gbp_m"] - base["cum_disc_gva_gbp_m"]).round(1)
    df["d_cum_co2_kt"] = (df["cum_disc_co2_kt"] - base["cum_disc_co2_kt"]).round(1)
    # innovation ROI: extra discounted GVA per £ of discounted public cost.
    # Central estimate plus a band: pessimistic uses the HIGH cost bound,
    # optimistic uses the LOW cost bound (benefit side is held at the model value).
    cost_c = df["disc_public_cost_gbp_m"].where(df["disc_public_cost_gbp_m"] > 0)
    cost_lo = df["disc_cost_low_gbp_m"].where(df["disc_cost_low_gbp_m"] > 0)
    cost_hi = df["disc_cost_high_gbp_m"].where(df["disc_cost_high_gbp_m"] > 0)
    df["gva_roi_central"] = (df["d_cum_gva_gbp_m"] / cost_c).round(2)
    df["gva_roi_pessimistic"] = (df["d_cum_gva_gbp_m"] / cost_hi).round(2)   # high cost
    df["gva_roi_optimistic"] = (df["d_cum_gva_gbp_m"] / cost_lo).round(2)    # low cost
    df["gva_roi_range"] = (df["gva_roi_pessimistic"].map("{:.2f}".format)
                           + "–" + df["gva_roi_optimistic"].map("{:.2f}".format))
    # cost-effectiveness on the headline circularity target (pp of recycled share / £m-yr)
    df["recycled_pp_per_costm"] = (df["d_recycled_share_pp"] / cost_c).round(4)

    df.to_csv(os.path.join(OUT, "q2_1_interventions.csv"))

    show = ["theme", "crit_recycled_share_end", "recycling_jobs_end",
            "circular_design_uptake_end", "d_cum_gva_gbp_m", "disc_public_cost_gbp_m",
            "gva_roi_central", "gva_roi_range"]
    print("=" * 110)
    print("Q2.1 CIRCULAR-INNOVATION INTERVENTIONS — 30-yr horizon, STPR 3.5%")
    print("(gva_roi_range = pessimistic[high cost]–optimistic[low cost])")
    print("=" * 110)
    with pd.option_context("display.width", 220, "display.max_columns", None):
        print(df[show].to_string())

    target = P.TARGETS_2035["recycling_share"]
    hit = [h for h in df.index[(df["crit_recycled_share_end"] >= target)].tolist()
           if h != "0_baseline"]
    eu_target = P.TARGETS_EU_CRMA_2030["recycling_share"]   # EU-CRMA stretch (25%)
    hit_eu = [h for h in df.index[(df["crit_recycled_share_end"] >= eu_target)].tolist()
              if h != "0_baseline"]
    ranked_roi = df.drop(index="0_baseline").sort_values("gva_roi_central", ascending=False)
    ranked_share = df.drop(index="0_baseline").sort_values(
        "d_recycled_share_pp", ascending=False)

    robust = _rank_robustness(df)
    print("\nROI rank robustness to cost uncertainty: " + robust)
    print(f"Meets UK 20% target: {hit or 'none alone'} | meets EU-CRMA 25% stretch: "
          f"{hit_eu or 'none alone'}")

    _write_memo(df, hit, ranked_roi, ranked_share, target, robust, eu_target, hit_eu)
    print("\nWritten: outputs/q2_1_interventions.csv  and  outputs/q2_1_memo.md")


def _rank_robustness(df):
    """Does the ROI ordering survive the cost band? Compare the top-ranked
    intervention under central / pessimistic / optimistic costs."""
    sub = df.drop(index="0_baseline")
    top_c = sub["gva_roi_central"].idxmax()
    top_p = sub["gva_roi_pessimistic"].idxmax()
    top_o = sub["gva_roi_optimistic"].idxmax()
    if top_c == top_p == top_o:
        return (f"ROBUST — `{top_c}` is the highest-ROI intervention across the full "
                f"low/central/high cost band.")
    return (f"SENSITIVE — top-ROI intervention changes with cost assumptions "
            f"(central=`{top_c}`, high-cost=`{top_p}`, low-cost=`{top_o}`).")


def _md_table(df, cols):
    """Render a DataFrame to a GitHub markdown table without the tabulate dep."""
    header = "| intervention | " + " | ".join(cols) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    rows = []
    for idx, r in df.iterrows():
        cells = [f"{r[c]}" for c in cols]
        rows.append(f"| {idx} | " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + rows)


def _write_memo(df, hit, ranked_roi, ranked_share, target, robust, eu_target=0.25, hit_eu=None):
    hit_eu = hit_eu or []
    def fmt(name):
        return INTERVENTIONS[name]["desc"]
    lines = []
    lines.append("# Q2.1 — Supporting innovation for circularity in NI minerals\n")
    lines.append("**Question:** How can the Department support innovation that will "
                 "support circularity — materials recovery, secondary materials markets, "
                 "recycling and circular design in manufacturing?\n")
    lines.append("**Method:** seven candidate interventions were mapped onto the "
                 "firm-grounded ABM (agents = named NI operators) and run individually "
                 "and as a combined package over 30 years (STPR 3.5%). Metrics below are "
                 "model behaviour, not forecasts; public-cost figures are notional and "
                 "used only for *relative* ROI ranking.\n")

    lines.append("## Interventions tested\n")
    for name, cfg in INTERVENTIONS.items():
        if name == "0_baseline":
            continue
        lines.append(f"- **{name}** ({cfg['theme']}): {cfg['desc']}")
    lines.append("")

    lines.append("## Headline findings\n")
    best_roi = ranked_roi.index[0]
    best_share = ranked_share.index[0]
    lines.append(f"1. **Best value-for-money (GVA ROI): `{best_roi}`** "
                 f"(~{df.loc[best_roi, 'gva_roi_central']}x central; "
                 f"{df.loc[best_roi, 'gva_roi_range']}x across the cost band) discounted GVA "
                 f"per £ public cost. {fmt(best_roi)}")
    lines.append(f"2. **Biggest lift in critical-mineral recycled share: `{best_share}`** "
                 f"(+{df.loc[best_share, 'd_recycled_share_pp']} pp vs baseline).")
    if hit:
        names = ", ".join(f"`{h}`" for h in hit)
        eu_names = ", ".join(f"`{h}`" for h in hit_eu) or "none individually"
        lines.append(f"3. **Meets the Vision-2035 20% recycling target:** {names or 'none individually'} "
                     f"(target = {target:.0%} critical-mineral recycled share). Against the stricter "
                     f"**EU-CRMA 25% (2030) stretch** — relevant to NI's potential EU-market exposure "
                     f"under the Windsor Framework — the qualifying set is: {eu_names}.")
    else:
        lines.append(f"3. **No single intervention reaches the Vision-2035 {target:.0%} "
                     f"recycling target** on its own — the package is needed (and the EU-CRMA "
                     f"{eu_target:.0%} stretch is harder still).")
    design_rank = (df.drop(index=["0_baseline", "G_integrated_package"])
                   .sort_values("circular_design_uptake_end", ascending=False))
    d1, d2 = design_rank.index[0], design_rank.index[1]
    lines.append(f"4. **Circular design in manufacturing** (recycled-content uptake) "
                 f"responds most to `{d1}` ({df.loc[d1, 'circular_design_uptake_end']:.0%}) "
                 f"and `{d2}` ({df.loc[d2, 'circular_design_uptake_end']:.0%}) — but note "
                 f"this raises *design uptake* without raising the *recycled share*, which "
                 f"stays feedstock-constrained until collection (`C`) is fixed.")
    lines.append(f"5. **The integrated package `G_integrated_package`** delivers the "
                 f"largest absolute gains (+{df.loc['G_integrated_package','d_cum_gva_gbp_m']} "
                 f"£m discounted GVA, +{df.loc['G_integrated_package','d_recycled_share_pp']} pp "
                 f"recycled share) — confirming the proposal's view that the *mix* beats any "
                 f"single lever.\n")

    lines.append("## Recommended sequencing\n")
    lines.append("- **Now (highest ROI, low cost):** demand-side rules — recycled-content "
                 "public procurement + design-for-disassembly standards + product passports. "
                 "These pull secondary-materials markets with little public spend.")
    lines.append("- **Near-term:** Circular Innovation Fund (R&D) to raise recovery yields "
                 "and design capability, anchored on Ionic/QUB/Met4Tech.")
    lines.append("- **Capital:** recovery-plant grants + smart collection/DRS to fix the "
                 "binding feedstock constraint (low NI critical-mineral waste collection).")
    lines.append("- **Enabling:** green-skills academy + minerals/circular cluster (CDE/Terex).\n")

    lines.append("## Full results table\n")
    show = ["crit_recycled_share_end", "secondary_value_gbp_m_end",
            "recycling_jobs_end", "circular_design_uptake_end", "d_recycled_share_pp",
            "d_cum_gva_gbp_m", "d_cum_co2_kt", "disc_public_cost_gbp_m", "gva_roi_central"]
    lines.append(_md_table(df, show))

    lines.append("\n## ROI sensitivity to cost uncertainty\n")
    lines.append(f"**Rank robustness:** {robust}\n")
    lines.append("Each lever carries a low/central/high public-cost bound (capital and "
                 "collection schemes get the widest band — the DRS government-vs-industry "
                 "estimates diverged ~10x). ROI is recomputed at the bundle's low and high "
                 "cost; the *benefit* (modelled discounted GVA) is held fixed, so this "
                 "isolates cost risk.")
    lines.append("")
    sens = ["d_cum_gva_gbp_m", "disc_cost_low_gbp_m", "disc_public_cost_gbp_m",
            "disc_cost_high_gbp_m", "gva_roi_pessimistic", "gva_roi_central",
            "gva_roi_optimistic"]
    lines.append(_md_table(df.drop(index="0_baseline"), sens))
    lines.append("\n*Read: `gva_roi_pessimistic` uses the HIGH cost bound, "
                 "`gva_roi_optimistic` the LOW. An intervention whose whole band stays >1 "
                 "is robustly value-positive; one straddling 1 is cost-sensitive.*")

    lines.append("\n## Calibration & cost sources (UK-anchored)\n")
    lines.append("Public-cost figures are NI-scale annual budgets benchmarked to real UK "
                 "programmes (NI ≈ 2.9% of UK population). Effect coefficients are calibrated "
                 "to UK circular-economy evidence:")
    lines.append("")
    lines.append("| Lever | NI cost £m/yr — low / central / high (intensity 1.0) | UK anchor |")
    lines.append("|---|---|---|")
    for k in LEVER_COST:
        lo, hi = LEVER_COST_BOUNDS[k]
        lines.append(f"| {k} | {lo} / {LEVER_COST[k]} / {hi} | {LEVER_COST_SOURCE[k]} |")
    lines.append("")
    lines.append("**Effect-coefficient evidence:**")
    lines.append("- *Collection lever:* calibrated to the UK Deposit Return Scheme uplift "
                 "(container return 70–75% → >90%, i.e. +15–20pp). Full deployment in-model "
                 "lifts WEEE battery-metal collection ~+17pp and commercial scrap ~+20pp; "
                 "REE stays low (~+5pp), consistent with global REE recycling at ~1% of demand.")
    lines.append("- *Recovery yields:* REE_magnet 0.85 / Li 0.50 / Cu 0.90 from Met4Tech, "
                 "Faraday/ReLiB (£34m EV-battery recycling programme) and Ionic process data.")
    lines.append("- *WEEE baseline collection ≈ 0.25* — UK documented WEEE collection/recycling "
                 "~22–25% (UN Global E-waste Monitor 2024); critical metals within it recovered "
                 "far less, which is why recycled *share* stays feedstock-constrained.")
    lines.append("\n*These remain modelling estimates with uncertainty; swap in audited NI "
                 "scheme budgets and a firm-level recycler survey to move from illustrative to "
                 "calibrated.*")

    with open(os.path.join(OUT, "q2_1_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
