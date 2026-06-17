"""
Q2.5 — "How can the sector contribute to local employment, skills development
and regional growth?"

Produces the indicators the proposal asks for under 2.5 — jobs by council area,
by skill level and wage band, retained local employment, training/apprenticeship
need and supplier opportunities — across a few policy scenarios, and shows how a
*local-content + skills* focus changes who benefits.

Run:  python q2_5_employment_skills.py
Outputs: outputs/q2_5_scenarios.csv, outputs/q2_5_district_jobs.csv, outputs/q2_5_memo.md
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import seed_parameters as P
from coupling import CoupledModel
import employment_module as E

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

GREEN_DEMAND = {"REE_magnet": P.DEMAND_GROWTH_WIND, "Lithium": P.DEMAND_GROWTH_EV,
                "Cobalt": 0.06, "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}

SCENARIOS = {
    "1_baseline": {"policy": {}, "label": "Baseline"},
    "2_circular_innovation": {"policy": {
        "recycling_grant": 0.4, "collection_infrastructure": 1.0, "product_passport": 0.5,
        "design_standards": 0.6, "recycled_content_procurement": 0.4,
        "local_supplier_support": 0.5}, "label": "Circular innovation"},
    "4_integrated": {"policy": {
        "exploration_grant": 0.15, "permit_years": 3, "community_benefit": 0.4,
        "recycling_grant": 0.4, "collection_infrastructure": 1.0, "design_standards": 0.6,
        "recycled_content_procurement": 0.4, "local_supplier_support": 0.8,
        "finance_support": 0.5}, "label": "Integrated circular + primary"},
    "local_skills_focus": {"policy": {
        "recycling_grant": 0.3, "collection_infrastructure": 1.0, "design_standards": 0.5,
        "local_supplier_support": 0.9, "skills_support": 0.9,
        "innovation_grant": 0.5}, "label": "Local-content + skills focus"},
}


def run_scenario(name, cfg):
    pol = cfg["policy"]
    m = CoupledModel(name=name, policy=pol, demand_growth=GREEN_DEMAND, seed=42,
                     use_ree_pilot=True, adaptive=True, use_cge=True)
    df = m.run()
    last, first = df.iloc[-1], df.iloc[0]
    minerals_jobs = {
        "Mining_Quarrying": float(last["mining_jobs"]),
        "Recycling_Secondary": float(last["recycling_jobs"]),
        "Manufacturing": float(last["manufacturing_jobs"]),
    }
    total_jobs = float(last["employment_total"])
    sk = E.skill_breakdown(minerals_jobs)
    wm = E.wage_metrics(minerals_jobs)
    retained, retention = E.retained_local(
        total_jobs, pol.get("local_supplier_support", 0.0), pol.get("skills_support", 0.0))
    delta = total_jobs - float(first["employment_total"])
    train = E.training_need(delta / max(1, P.HORIZON) * P.HORIZON, minerals_jobs)
    # district jobs (end-year), from the firm-grounded spatial layer
    districts = {c[len("jobs_"):]: round(float(last[c]), 1)
                 for c in df.columns if c.startswith("jobs_")}
    return {
        "scenario": name, "label": cfg["label"],
        "total_jobs_end": round(total_jobs, 1),
        "minerals_sector_jobs": round(sum(minerals_jobs.values()), 1),
        "high_skill_jobs": round(sk["high"], 1),
        "mid_skill_jobs": round(sk["mid"], 1),
        "entry_skill_jobs": round(sk["entry"], 1),
        "avg_wage_gbp": wm["avg_wage_gbp"],
        "wage_premium_vs_ni": wm["wage_premium_vs_ni"],
        "wage_bill_gbp_m": wm["wage_bill_gbp_m"],
        "retained_local_jobs": retained,
        "local_retention_rate": retention,
        "skilled_training_need": train,
    }, districts


def main():
    rows, dist_rows = [], []
    for name, cfg in SCENARIOS.items():
        rec, districts = run_scenario(name, cfg)
        rows.append(rec)
        for d, j in districts.items():
            dist_rows.append({"scenario": name, "district": d, "end_jobs": j})
    sc = pd.DataFrame(rows).set_index("scenario")
    sc.to_csv(os.path.join(OUT, "q2_5_scenarios.csv"))
    dist = pd.DataFrame(dist_rows)
    dist.to_csv(os.path.join(OUT, "q2_5_district_jobs.csv"), index=False)

    print("=" * 110)
    print("Q2.5 — EMPLOYMENT, SKILLS & REGIONAL GROWTH (end-year, 30-yr horizon)")
    print("=" * 110)
    show = ["label", "total_jobs_end", "minerals_sector_jobs", "high_skill_jobs",
            "avg_wage_gbp", "wage_premium_vs_ni", "retained_local_jobs",
            "local_retention_rate", "skilled_training_need"]
    with pd.option_context("display.width", 220, "display.max_columns", None):
        print(sc[show].to_string())
    print("\nEnd-year jobs by council area (top 6), Local-content + skills focus:")
    top = (dist[dist["scenario"] == "local_skills_focus"]
           .sort_values("end_jobs", ascending=False).head(6))
    print(top.to_string(index=False))

    _write_memo(sc, dist)
    print("\nWritten: outputs/q2_5_scenarios.csv, q2_5_district_jobs.csv, q2_5_memo.md")


def _md_table(df, cols, index_name):
    out = [f"| {index_name} | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for idx, r in df.iterrows():
        out.append(f"| {idx} | " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _write_memo(sc, dist):
    base = sc.loc["1_baseline"]
    ls = sc.loc["local_skills_focus"]
    top = (dist[dist["scenario"] == "local_skills_focus"]
           .sort_values("end_jobs", ascending=False).head(5))
    lines = []
    lines.append("# Q2.5 — Local employment, skills development & regional growth\n")
    lines.append("**Method:** the firm-grounded jobs-by-council-area output is split by **skill "
                 "level** and **wage band** (ONS SOC / ASHE-by-industry structure on a real NISRA "
                 f"ASHE anchor — NI median FT wage £{E.NI_MEDIAN_ANNUAL_WAGE:,.0f}/yr, 2024), with "
                 "**retained local employment** (the Minviro leakage fix — rises with local-supplier "
                 "and skills support) and a **skilled training/apprenticeship need**. Run across four "
                 "policy scenarios. Figures are model behaviour, not forecasts.\n")

    lines.append("## How the sector contributes\n")
    lines.append(f"- **Quality jobs, above the NI average.** The minerals sectors pay a wage premium "
                 f"of ~**{ls['wage_premium_vs_ni']:.0%}** of the NI median (mining & advanced "
                 f"manufacturing are skill-intensive: ~{ls['high_skill_jobs']:.0f} higher-skill roles "
                 f"in the local-content + skills scenario). Mining/quarrying is among the highest-paid "
                 f"UK industries (ONS ASHE).")
    lines.append(f"- **Regional growth is rural-weighted.** End-year jobs concentrate in the council "
                 f"areas where the named firms sit — e.g. " +
                 ", ".join(f"{r['district']} ({r['end_jobs']:.0f})" for _, r in top.iterrows()) +
                 " — spreading growth beyond Belfast to the rural west and Mid Ulster.")
    lines.append(f"- **Local retention is a policy choice.** Retained local employment rises from "
                 f"~{base['local_retention_rate']:.0%} (baseline) to "
                 f"~{ls['local_retention_rate']:.0%} under a local-content + skills focus — i.e. "
                 f"{ls['retained_local_jobs']:.0f} of {ls['total_jobs_end']:.0f} jobs kept in NI — "
                 f"directly addressing Minviro's warning that benefits leak out when specialist "
                 f"labour and equipment are imported.")
    lines.append(f"- **Skills are the binding enabler.** The sector needs ~{ls['skilled_training_need']:.0f} "
                 f"skilled roles trained over the horizon, against an NI backdrop of ~7,500 skill-"
                 f"shortage vacancies and 5,000+ new roles needed annually. A green-skills/critical-"
                 f"minerals pipeline (Skills England/DWP, FE colleges, QUB, Camborne-style provision) "
                 f"and apprenticeships are prerequisites, not add-ons.\n")

    lines.append("## Scenario comparison\n")
    lines.append(_md_table(sc, ["label", "total_jobs_end", "minerals_sector_jobs",
                                "high_skill_jobs", "wage_premium_vs_ni", "retained_local_jobs",
                                "local_retention_rate", "skilled_training_need"], "scenario"))

    lines.append("\n## Recommendations\n")
    lines.append("1. **Tie support to local content & skills.** Local-supplier development and a "
                 "skills pipeline convert headline jobs into *retained* NI jobs and apprenticeships — "
                 "the local-content + skills scenario delivers the highest retention and skilled-job "
                 "share.")
    lines.append("2. **Target the rural west / Mid Ulster** (where mining/quarry and equipment firms "
                 "sit) for regional-growth balance, and Belfast/Mid & East Antrim for "
                 "recycling/advanced-manufacturing clusters.")
    lines.append("3. **Build the green-skills pipeline now** (FE/apprenticeships + QUB + Skills "
                 "England/DWP) — skills shortages are the binding constraint on capturing the jobs.\n")

    lines.append("## Sources\n")
    for s in (
        "NISRA ASHE 2024: NI median FT gross weekly £666 (~£34,632/yr); UK £728/£37,430",
        "ONS ASHE by industry: mining & quarrying among the highest-paid industries; "
        "manufacturing a modest premium",
        "NI skills: ~7,500 skill-shortage vacancies (2024), 5,000+ new roles needed annually, "
        "STEM/engineering/apprenticeship gaps (NI Executive / DfE Skills Strategy)",
        "Vision 2035: skills via Skills England + DWP; Camborne School of Mines; BGS human capital",
        "Minviro Final Report: benefits leak from the region if specialist labour/equipment imported",
    ):
        lines.append(f"- {s}")
    lines.append("\n*Skill splits and sector wage indices are PROXY (ONS structure on a real NISRA "
                 "anchor); replace with NISRA BRES-by-district and ASHE-by-industry-by-region.*")

    with open(os.path.join(OUT, "q2_5_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
