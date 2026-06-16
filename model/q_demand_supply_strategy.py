"""
Strategy-driven demand scenarios + circular supply-chain capacity analysis.

PART A — DEMAND-SIDE OPPORTUNITY SCENARIOS
  Demand-growth paths derived from three strategy documents:
    * UK Critical Minerals Strategy (Vision 2035): UK copper demand ~2x and
      lithium ~+1,100% by 2035; growth minerals incl. copper, graphite.
    * EU Critical Raw Materials Act: 2030 targets 10% extraction / 40% processing
      / 25% recycling / <=65% single third country -> large processing-offtake pull
      and a critical-mineral scarcity price premium for UK/NI midstream + recycling.
    * UK Industrial Strategy (2025): IS-8 growth sectors (Advanced Manufacturing,
      Clean Energy, Defence...) with EV/offshore-wind/battery demand; Belfast named
      as a critical-minerals cluster.
  Growth runs to 2035 (t=9) then plateaus. Each demand path is run under a
  sustainable enabling-policy stance (high-ESG + community benefit + circular +
  finance/skills) to read off the opportunity for *sustainable* development.

PART B — SUPPLY & CAPACITY CHALLENGE
  Maps the current NI circular supply chain by stage from the firm register and
  computes, per critical mineral, projected 2035 demand vs installed NI processing
  capacity and the primary/collection capability that exists today -> the gaps.

Run:  python q_demand_supply_strategy.py
Outputs: outputs/q_demand_scenarios.csv, outputs/q_supply_capacity_gap.csv,
         outputs/q_demand_supply_memo.md
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import seed_parameters as P
from coupling import CoupledModel
from abm_module import MiningFirm
from mfa_module import MINERAL_PARAMS, MINERAL_PRICE_GBP_PER_T
from company_data import (
    DOWNSTREAM_ROLES, MINING_ROLES, RECYCLING_ROLES,
    companies_by_role, firm_capital_pipeline, parse_firms,
    recycler_installed_capacity_t,
)

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

PLATEAU = 9   # demand grows to ~2035 then holds

# Baseline (current) demand, as in the main run.
BASE_DEMAND = {"REE_magnet": P.DEMAND_GROWTH_WIND, "Lithium": P.DEMAND_GROWTH_EV,
               "Cobalt": 0.06, "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}

# Document-anchored demand-growth paths (CAGR to 2035).
VISION = {"Copper": 0.08, "Lithium": 0.30, "REE_magnet": 0.12, "Cobalt": 0.09,
          "Nickel": 0.07, "Aluminium": 0.04}                  # Vision 2035
INDUSTRIAL = {"Copper": 0.09, "Lithium": 0.25, "REE_magnet": 0.12, "Cobalt": 0.08,
              "Nickel": 0.07, "Aluminium": 0.05}              # clean energy/defence/AM
CRMA = {m: round(v * 1.10, 3) for m, v in VISION.items()}     # EU-wide pull on top
CRMA_PRICE = {m: 0.04 for m in ("Lithium", "REE_magnet", "Cobalt", "Nickel", "Copper")}
COMBINED = {m: max(VISION.get(m, 0), INDUSTRIAL.get(m, 0), CRMA.get(m, 0))
            for m in set(VISION) | set(INDUSTRIAL) | set(CRMA)}
COMBINED_PRICE = {m: 0.05 for m in CRMA_PRICE}

# Sustainable enabling-policy stance (Vision 2035 / IS instruments): high-ESG +
# community benefit + finance + skills + the circular-innovation mix.
SUSTAINABLE = {
    "esg_cost": 0.16, "community_benefit": 0.4, "finance_support": 0.6,
    "skills_support": 0.6, "permit_years": 3, "exploration_grant": 0.10,
    "recycling_grant": 0.3, "innovation_grant": 0.5, "collection_infrastructure": 1.0,
    "product_passport": 0.6, "recycled_content_procurement": 0.4,
    "design_standards": 0.5, "secondary_market_support": 0.5,
}

SCENARIOS = {
    "0_current": {"demand": BASE_DEMAND, "policy": {}, "price": {},
                  "label": "Current demand + current policy (reference)"},
    "sustainable_baseline_demand": {"demand": BASE_DEMAND, "policy": SUSTAINABLE, "price": {},
                  "label": "Current demand + sustainable enabling policy"},
    "uk_vision_2035": {"demand": VISION, "policy": SUSTAINABLE, "price": {},
                  "label": "UK Vision 2035 demand (Cu x2, Li +1100%)"},
    "eu_crma": {"demand": CRMA, "policy": SUSTAINABLE, "price": CRMA_PRICE,
                  "label": "EU CRMA pull + scarcity price premium"},
    "uk_industrial_strategy": {"demand": INDUSTRIAL, "policy": SUSTAINABLE, "price": {},
                  "label": "UK Industrial Strategy (clean energy/defence/AM)"},
    "combined_high_demand": {"demand": COMBINED, "policy": SUSTAINABLE, "price": COMBINED_PRICE,
                  "label": "Combined high demand (all three aligned)"},
}

TARGETS = P.TARGETS_2035   # domestic 0.10, recycling 0.20, max_single_country 0.60


def run_scenario(name, cfg):
    m = CoupledModel(name=name, policy=cfg["policy"], demand_growth=cfg["demand"],
                     price_path=cfg["price"], seed=42, use_ree_pilot=True,
                     adaptive=True, use_cge=True, demand_plateau_years=PLATEAU)
    df = m.run()
    last = df.iloc[-1]
    opened = sorted(a.name for a in m.abm.agents
                    if isinstance(a, MiningFirm) and getattr(a, "newly_opened", False))
    return {
        "scenario": name,
        "label": cfg["label"],
        "mines_opened": int(last["mines_opened"]),
        "projects_unlocked": "; ".join(opened) or "—",
        "crit_domestic_share_end": round(float(last["crit_domestic_share"]), 3),
        "crit_recycled_share_end": round(float(last["crit_recycled_share"]), 3),
        "crit_import_share_end": round(float(last["crit_import_share"]), 3),
        "single_country_exposure_end": round(float(last["crit_max_single_country"]), 3),
        "recycling_value_gbp_m_end": round(float(last["recycling_fd_gbp_m"]), 1),
        "end_jobs": round(float(last["employment_total"]), 1),
        "cum_disc_gva_gbp_m": round(m.cumulative_discounted["gva"], 1),
        "cum_disc_co2_kt": round(m.cumulative_discounted["co2"], 1),
        "meets_domestic_10pct": bool(last["crit_domestic_share"] >= TARGETS["domestic_share"]),
        "meets_recycling_20pct": bool(last["crit_recycled_share"] >= TARGETS["recycling_share"]),
        "meets_single_country_60pct": bool(
            last["crit_max_single_country"] <= TARGETS["max_single_country"]),
    }


def supply_capacity_gap():
    """Map the current NI circular supply chain and the per-mineral capacity gap."""
    firms = parse_firms()
    installed = recycler_installed_capacity_t()          # NI processing capacity (tpa)
    # which minerals have any NI primary capability / collection capability today
    primary_minerals, collection_minerals = set(), set()
    for f in firms:
        if f["role"] in MINING_ROLES:
            primary_minerals |= f["minerals"]
        if f["role"] in RECYCLING_ROLES:
            collection_minerals |= f["recycler_targets"]

    rows = []
    for m in P.CRITICAL_MINERALS:
        demand0, lifetime, coll, rec, dom0, imp_conc = MINERAL_PARAMS[m]
        proj = demand0 * (1.0 + VISION.get(m, 0.0)) ** PLATEAU      # 2035 demand (t/yr)
        cap = installed.get(m, 0.0)
        coverage = cap / proj if proj else 0.0
        if cap > 0:
            gap = "Processing capacity exists (Ionic) but feedstock-limited"
        elif m in collection_minerals:
            gap = "No NI processing capacity — collection exists, recovery absent"
        elif m in primary_minerals:
            gap = "Primary prospect only — no processing/recovery capacity"
        else:
            gap = "No NI supply-chain stage — fully import-dependent"
        rows.append({
            "mineral": m,
            "proj_2035_demand_t": round(proj, 0),
            "ni_processing_capacity_tpa": round(cap, 0),
            "capacity_coverage": round(coverage, 3),
            "has_primary_prospect": m in primary_minerals,
            "has_collection_route": m in collection_minerals,
            "key_gap": gap,
        })
    return pd.DataFrame(rows).set_index("mineral")


def stage_summary():
    firms = parse_firms()
    capex = firm_capital_pipeline()
    stages = [
        ("Primary / mining", MINING_ROLES),
        ("Collection / feedstock", {"waste_recycler"}),
        ("Processing / recovery", {"critical_mineral_recycler"}),
        ("Downstream demand", {"downstream_manufacturer"}),
        ("Equipment / enabling", {"supply_chain_manufacturer"}),
    ]
    rows = []
    for label, roles in stages:
        sel = [f for f in firms if f["role"] in roles]
        rows.append({
            "stage": label,
            "firms": len(sel),
            "employees": int(sum(f["employees"] for f in sel)),
            "named": "; ".join(f["name"] for f in sel) or "—",
        })
    return pd.DataFrame(rows).set_index("stage"), capex


def main():
    rows = [run_scenario(n, c) for n, c in SCENARIOS.items()]
    dem = pd.DataFrame(rows).set_index("scenario")
    ref = dem.loc["sustainable_baseline_demand"]
    dem["d_domestic_pp"] = ((dem["crit_domestic_share_end"]
                             - ref["crit_domestic_share_end"]) * 100).round(2)
    dem["d_recycled_pp"] = ((dem["crit_recycled_share_end"]
                             - ref["crit_recycled_share_end"]) * 100).round(2)
    dem["d_import_pp"] = ((dem["crit_import_share_end"]
                          - ref["crit_import_share_end"]) * 100).round(2)
    dem.to_csv(os.path.join(OUT, "q_demand_scenarios.csv"))

    gap = supply_capacity_gap()
    gap.to_csv(os.path.join(OUT, "q_supply_capacity_gap.csv"))
    stages, capex = stage_summary()

    print("=" * 110)
    print("PART A — DEMAND-SIDE OPPORTUNITY SCENARIOS (sustainable policy stance; demand to ~2035)")
    print("=" * 110)
    show = ["label", "mines_opened", "projects_unlocked", "crit_domestic_share_end",
            "crit_recycled_share_end", "crit_import_share_end", "end_jobs",
            "cum_disc_gva_gbp_m"]
    with pd.option_context("display.width", 230, "display.max_columns", None,
                           "display.max_colwidth", 40):
        print(dem[show].to_string())
    print("\n" + "=" * 110)
    print("PART B — CURRENT CIRCULAR SUPPLY CHAIN: capacity gap by critical mineral")
    print("=" * 110)
    with pd.option_context("display.width", 230, "display.max_columns", None,
                           "display.max_colwidth", 55):
        print(gap.to_string())
    print("\nSupply-chain stage map:")
    print(stages[["firms", "employees"]].to_string())

    _write_memo(dem, gap, stages, capex)
    print("\nWritten: outputs/q_demand_scenarios.csv, q_supply_capacity_gap.csv, q_demand_supply_memo.md")


def _md_table(df, cols, index_name):
    out = [f"| {index_name} | " + " | ".join(cols) + " |",
           "|" + "---|" * (len(cols) + 1)]
    for idx, r in df.iterrows():
        out.append(f"| {idx} | " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _write_memo(dem, gap, stages, capex):
    lines = []
    lines.append("# Demand-side opportunities & supply-side challenges for sustainable "
                 "minerals development\n")
    lines.append("Scenarios derive demand growth from the **UK Critical Minerals Strategy "
                 "(Vision 2035)**, the **EU Critical Raw Materials Act**, and the **UK "
                 "Industrial Strategy (2025)**, run under a sustainable enabling-policy stance "
                 "(high-ESG + community benefit + finance/skills + circular mix). Demand grows "
                 "to ~2035 then plateaus. Figures are model behaviour, not forecasts.\n")

    lines.append("## Strategy demand signals used\n")
    lines.append("- **Vision 2035:** UK copper demand ~2x and lithium ~+1,100% by 2035; growth "
                 "minerals add copper & graphite; targets 10% domestic / 20% recycling / "
                 "≤60% single-country; NWF/UKEF finance, BICS energy support.")
    lines.append("- **EU CRMA:** 2030 targets 10% extraction / 40% processing / 25% recycling / "
                 "≤65% single third country — a large processing-offtake pull and scarcity price "
                 "premium for UK/NI midstream and recycling.")
    lines.append("- **UK Industrial Strategy:** IS-8 growth sectors (Advanced Manufacturing "
                 "£4.3bn, Clean Energy, Defence) drive EV/offshore-wind/battery demand; **Belfast "
                 "named as a critical-minerals cluster**.\n")

    lines.append("## Part A — Demand-side opportunities for sustainable development\n")
    lines.append(_md_table(dem, ["label", "mines_opened", "projects_unlocked",
                                 "crit_domestic_share_end", "crit_recycled_share_end",
                                 "crit_import_share_end", "end_jobs", "cum_disc_gva_gbp_m"],
                           "scenario"))
    best = dem.drop(index=["0_current", "sustainable_baseline_demand"]).sort_values(
        "cum_disc_gva_gbp_m", ascending=False)
    top = best.index[0]
    base = dem.loc["sustainable_baseline_demand"]
    lines.append(f"\n**Opportunity finding:** rising strategy-driven demand makes the circular + "
                 f"primary opportunity materially larger — the strongest case `{top}` "
                 f"({dem.loc[top, 'label']}) reaches {dem.loc[top, 'end_jobs']:.0f} end-year jobs and "
                 f"£{dem.loc[top, 'cum_disc_gva_gbp_m']}m discounted GVA (vs "
                 f"{base['end_jobs']:.0f} jobs / £{base['cum_disc_gva_gbp_m']}m at today's demand). "
                 f"The EU CRMA scarcity premium improves recovery economics, and a community-benefit "
                 f"+ high-ESG stance brings the contested primary deposit (Dalradian) forward.")
    lines.append(f"\n**The catch (links to Part B):** higher demand *erodes the supply-security "
                 f"ratios* unless capacity scales with it — recycled share falls from "
                 f"{base['crit_recycled_share_end']:.0%} (today's demand) to "
                 f"{dem.loc[top, 'crit_recycled_share_end']:.0%}, and import share rises from "
                 f"{base['crit_import_share_end']:.0%} to {dem.loc[top, 'crit_import_share_end']:.0%}, "
                 f"because demand outruns NI's thin processing/recovery capacity. Demand-side "
                 f"opportunity is real but only captured if the supply-side capacity gap is closed.\n")

    lines.append("## Part B — Supply & capacity challenges (current circular supply chain)\n")
    lines.append(f"NI capital pipeline across the chain: £{capex['total_gbp_m']}m "
                 f"(operating £{capex['operating_gbp_m']}m + proposed £{capex['proposed_gbp_m']}m).\n")
    lines.append(_md_table(stages, ["firms", "employees", "named"], "stage"))
    lines.append("")
    lines.append(_md_table(gap, ["proj_2035_demand_t", "ni_processing_capacity_tpa",
                                 "capacity_coverage", "has_primary_prospect",
                                 "has_collection_route", "key_gap"], "mineral"))

    lines.append("\n## Key challenges (supply & capacity side)\n")
    lines.append("1. **A single midstream processing asset.** NI has named recovery capacity for "
                 "REE only (Ionic, 400 tpa) — and even that is dwarfed by projected 2035 demand. "
                 "There is **no NI processing/recovery capacity for lithium, cobalt or nickel**, the "
                 "fastest-growing battery metals.")
    lines.append("2. **Feedstock collection is the binding circular constraint.** Collection routes "
                 "exist (Re-Gen, RiverRidge, Bryson) but critical-metal capture from end-of-life is "
                 "low, so processing capacity would be feedstock-starved.")
    lines.append("3. **Almost no domestic primary critical-mineral geology.** The opportunity is "
                 "midstream + recycling, not primary mining — except contested antimony/copper "
                 "(Dalradian), which is a social-licence not a resource question.")
    lines.append("4. **The chain is demand-rich but capacity-poor.** Strong downstream demand "
                 "(Wrightbus, Seagate, Encirc, Spirit) and equipment capability (CDE, Terex) are "
                 "present, but the processing/recovery middle is thin — the priority gap to fund.\n")

    lines.append("\n## NI-specific evidence base (opportunities)\n")
    lines.append("- **Geology:** NI is the *most prospective area of the UK/Ireland for precious "
                 "metals* (BGS). Curraghinalt (Sperrins, Tyrone) is NI's one known polymetallic "
                 "deposit — 3.79 Moz Au measured+indicated plus ~15 kt copper over life and minor "
                 "**antimony, tellurium, bismuth, cobalt**; the Mourne granites show **REE/critical-"
                 "metal enrichment** potential; Pt/Pd anomalies in the Sperrins (GSNI Tellus).")
    lines.append("- **Innovation ecosystem:** a genuine REE-recycling cluster — **Ionic "
                 "Technologies** (QUB/Seren spin-out, 400 tpa REO target), **Plaswire** (turbine "
                 "magnet+blade recycling), and **QUILL** (Queen's Ionic Liquids Lab). NI's named "
                 "role in Vision 2035 is permanent-magnet recycling.")
    lines.append("- **Logistics & feedstock:** Belfast Harbour (24.1 Mt cargo, 2024) is an offshore-"
                 "wind **decommissioning hub** — an end-of-life turbine-magnet feedstock pipeline for "
                 "Ionic/Plaswire.")
    lines.append("- **Dual-market access:** under **Windsor Framework Art. 13(4)**, EU CRMA "
                 "provisions could apply in NI (DBT, Apr 2025) — NI midstream/recycling could serve "
                 "both the UK Vision 2035 and the EU CRMA 40%-processing / 25%-recycling pulls.\n")

    lines.append("## NI-specific evidence base (challenges)\n")
    lines.append("- **Midstream gap is the headline constraint:** ~**80% of UK-shredded automotive/"
                 "electronic metals are exported for processing** for lack of UK midstream investment "
                 "(BGS) — NI has one REE processor and none for Li/Co/Ni.")
    lines.append("- **Supply concentration to displace:** 2023 mine supply was **74% China (REE), "
                 "70% DRC (Co), 44% Australia (Li)** (BGS/Idoine 2025) — the strategic prize, but also "
                 "why import prices/volumes are volatile.")
    lines.append("- **Circular performance has stalled:** NI municipal recycling **~50.4% (2024/25), "
                 "flat since 2019**, with energy-from-waste rising to 34.3% — competing with recycling "
                 "for material and locking critical metals out of recovery.")
    lines.append("- **Long, contested primary lead times:** ~20 years from discovery to mine globally, "
                 "with declining grades; NI's best deposit (Curraghinalt) is constrained by social "
                 "licence, and the **Mineral Development Act (NI) 1969 is under review** (gold/silver "
                 "vested in the Crown, other minerals in DfE).\n")

    lines.append("## Sources\n")
    for s in (
        "UK Critical Minerals Strategy — Vision 2035 (DBT, Jan 2026)",
        "UK Critical Minerals Technical Annex — Annex 2 demand signals (DBT, 2026)",
        "UK Modern Industrial Strategy (HMG, Jul 2025)",
        "EU Critical Raw Materials Act (2024)",
        "GSNI/BGS — Critical Minerals and the Circular Economy in Northern Ireland (OR25042, 2025)",
        "BGS/Idoine et al. (2025) — global mine-supply concentration; IEA net-zero demand (2024)",
        "Dalradian — Curraghinalt 2021 feasibility study; DAERA LAC municipal waste 2024/25",
    ):
        lines.append(f"- {s}")

    lines.append("\n*Capacities are register-derived desk estimates; demand CAGRs are document-"
                 "anchored (headline annual multiples, not the cumulative Annex-2 totals). Replace "
                 "with audited plant data and CMIC mineral-by-mineral demand forecasts to calibrate.*")

    with open(os.path.join(OUT, "q_demand_supply_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
