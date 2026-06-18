"""
Q2.2 — "What are the key opportunities and challenges for sustainable minerals
development?"

Two parts, both grounded in the firm-level register and the MFA/ABM:

  PART A  Opportunity ranking — a mineral-by-mineral score combining demand pull,
          domestic geology, circular (recycling) potential, strategic supply-
          security value and economic value, plus the headline *challenge* (binding
          constraint) for each.

  PART B  Challenge diagnosis — constraint-relaxation scenarios. Starting from
          today's constraints, each scenario relaxes ONE barrier (permitting,
          finance/cost-of-capital, community acceptance/social licence, skills,
          energy) and an "enabling-environment" scenario relaxes them together.
          Whatever unlocks the most development is the binding constraint.

Run:  python q2_2_opportunities_challenges.py
Outputs: outputs/q2_2_opportunity_ranking.csv, outputs/q2_2_constraint_scenarios.csv,
         outputs/q2_2_memo.md
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import numpy as np
import pandas as pd
import seed_parameters as P
from coupling import CoupledModel
from abm_module import MiningFirm, PROXY_DEPOSITS
from mfa_module import MINERAL_PARAMS, MINERAL_PRICE_GBP_PER_T
from company_data import (
    MINING_ROLES, deposit_quality_by_mineral, parse_firms, recycler_targets,
)

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

GREEN_DEMAND = {"REE_magnet": P.DEMAND_GROWTH_WIND, "Lithium": P.DEMAND_GROWTH_EV,
                "Cobalt": 0.06, "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}


# ---------------------------------------------------------------------------
# PART A — opportunity ranking
# ---------------------------------------------------------------------------
def _proxy_quality(mineral):
    p = PROXY_DEPOSITS.get(mineral)
    if not p:
        return 0.0
    return round((0.65 * p["resource"] + 0.35 * p["capacity"]) * 0.85, 3)


def opportunity_ranking():
    firms = parse_firms()
    firm_quality = deposit_quality_by_mineral()           # named-firm derived
    all_targets = set()
    for f in firms:
        all_targets |= f["recycler_targets"]

    # max planning risk among named miners of each mineral (for challenge tag)
    risk_by_mineral = {}
    miners_by_mineral = {}
    for f in firms:
        if f["role"] not in MINING_ROLES:
            continue
        for m in f["minerals"]:
            risk_by_mineral.setdefault(m, []).append(f["scores"]["planning_risk"])
            miners_by_mineral.setdefault(m, []).append(f["name"])

    max_price = max(MINERAL_PRICE_GBP_PER_T.values())
    rows = []
    for m in P.MINERALS:
        demand0, lifetime, coll, rec, dom0, imp_conc = MINERAL_PARAMS[m]
        price = MINERAL_PRICE_GBP_PER_T[m]
        geology = firm_quality.get(m, _proxy_quality(m))
        is_recycler = m in all_targets
        recycled0 = coll * rec                            # rough steady-state share
        import_dep = max(0.0, 1.0 - dom0 - recycled0)
        strategic = import_dep * imp_conc                 # single-country exposure
        # 0-1 opportunity components
        demand_pull = min(1.0, GREEN_DEMAND.get(m, 0.0) / 0.12)
        circular = rec * (1.0 if is_recycler else 0.4)
        value = np.log1p(price) / np.log1p(max_price)
        score = (0.25 * demand_pull + 0.20 * geology + 0.25 * circular
                 + 0.20 * strategic + 0.10 * value)

        # pathway + headline challenge
        if geology >= 0.5 and circular >= 0.5:
            pathway = "Primary + recycling"
        elif geology >= 0.5:
            pathway = "Primary"
        elif circular >= 0.5 or is_recycler:
            pathway = "Recycling"
        else:
            pathway = "Import-dependent"

        max_risk = max(risk_by_mineral.get(m, [0.0]))
        if geology >= 0.5 and max_risk >= 0.7:
            challenge = "Social licence / permitting (contested deposit)"
        elif geology >= 0.5:
            challenge = "Finance & scale-up of primary project"
        elif is_recycler:
            challenge = "Feedstock collection (low end-of-life capture)"
        else:
            challenge = "No domestic source — import-dependent"

        rows.append({
            "mineral": m,
            "critical": m in P.CRITICAL_MINERALS,
            "opportunity_score": round(score, 3),
            "pathway": pathway,
            "key_challenge": challenge,
            "demand_growth_pa": GREEN_DEMAND.get(m, 0.0),
            "domestic_geology": round(geology, 3),
            "recovery_yield": rec,
            "import_dependence": round(import_dep, 3),
            "single_country_conc": imp_conc,
            "named_miners": "; ".join(miners_by_mineral.get(m, [])) or "—",
            "price_gbp_t": price,
        })
    df = pd.DataFrame(rows).sort_values("opportunity_score", ascending=False)
    return df.set_index("mineral")


# ---------------------------------------------------------------------------
# PART B — constraint-relaxation scenarios
# ---------------------------------------------------------------------------
SCENARIOS = {
    "0_current_constraints": {"policy": {}, "label": "Today's constraints (baseline)"},
    "permitting_reform": {"policy": {"permit_years": 2},
                          "label": "Faster, clearer permitting"},
    "finance_support": {"policy": {"finance_support": 0.8, "exploration_grant": 0.10},
                        "label": "Finance: National Wealth Fund / UKEF co-investment"},
    "community_benefit": {"policy": {"community_benefit": 0.4},
                          "label": "Community benefit + social licence"},
    "skills_availability": {"policy": {"skills_support": 0.8},
                            "label": "Skills & expertise availability"},
    "energy_competitiveness": {"policy": {"energy_cost_index": 0.90},
                               "label": "Competitive (green) energy cost"},
    "responsible_high_esg": {"policy": {"esg_cost": 0.18, "community_benefit": 0.4,
                                        "permit_years": 4},
                             "label": "High-ESG responsible development"},
    "enabling_environment": {"policy": {"permit_years": 2, "finance_support": 0.8,
                                        "community_benefit": 0.4, "skills_support": 0.8,
                                        "exploration_grant": 0.12, "energy_cost_index": 0.95},
                             "label": "All enablers together"},
}


def run_scenario(name, cfg):
    m = CoupledModel(name=name, policy=cfg["policy"], demand_growth=GREEN_DEMAND,
                     seed=42, use_ree_pilot=True, adaptive=True, use_cge=True)
    df = m.run()
    last = df.iloc[-1]
    opened = sorted(a.name for a in m.abm.agents
                    if isinstance(a, MiningFirm) and getattr(a, "newly_opened", False))
    domestic = sorted(k for k, v in m.abm.new_domestic.items() if v > 0)
    return {
        "scenario": name,
        "label": cfg["label"],
        "mines_opened": int(last["mines_opened"]),
        "projects_unlocked": "; ".join(opened) or "—",
        "domestic_minerals": "; ".join(domestic) or "—",
        "crit_domestic_share_end": round(float(last["crit_domestic_share"]), 3),
        "crit_recycled_share_end": round(float(last["crit_recycled_share"]), 3),
        "single_country_exposure_end": round(float(last["crit_max_single_country"]), 3),
        "end_jobs": round(float(last["employment_total"]), 1),
        "cum_disc_gva_gbp_m": round(m.cumulative_discounted["gva"], 1),
        "cum_disc_co2_kt": round(m.cumulative_discounted["co2"], 1),
    }


def main():
    opp = opportunity_ranking()
    opp.to_csv(os.path.join(OUT, "q2_2_opportunity_ranking.csv"))

    rows = [run_scenario(n, c) for n, c in SCENARIOS.items()]
    sc = pd.DataFrame(rows).set_index("scenario")
    base = sc.loc["0_current_constraints"]
    sc["d_mines"] = (sc["mines_opened"] - base["mines_opened"]).astype(int)
    sc["d_cum_gva_gbp_m"] = (sc["cum_disc_gva_gbp_m"] - base["cum_disc_gva_gbp_m"]).round(1)
    sc["d_cum_co2_kt"] = (sc["cum_disc_co2_kt"] - base["cum_disc_co2_kt"]).round(1)
    sc.to_csv(os.path.join(OUT, "q2_2_constraint_scenarios.csv"))

    single = sc.drop(index=["0_current_constraints", "responsible_high_esg",
                            "enabling_environment"], errors="ignore")
    binding = single.sort_values(["d_mines", "d_cum_gva_gbp_m"], ascending=False)

    print("=" * 100)
    print("Q2.2 — OPPORTUNITY RANKING (mineral-by-mineral)")
    print("=" * 100)
    cols = ["opportunity_score", "pathway", "key_challenge", "domestic_geology",
            "import_dependence", "named_miners"]
    with pd.option_context("display.width", 200, "display.max_columns", None,
                           "display.max_colwidth", 40):
        print(opp[cols].to_string())
    print("\n" + "=" * 100)
    print("Q2.2 — CONSTRAINT-RELAXATION SCENARIOS (what unlocks development?)")
    print("=" * 100)
    show = ["label", "mines_opened", "projects_unlocked", "crit_domestic_share_end",
            "end_jobs", "cum_disc_gva_gbp_m", "d_cum_gva_gbp_m", "d_cum_co2_kt"]
    with pd.option_context("display.width", 220, "display.max_columns", None,
                           "display.max_colwidth", 36):
        print(sc[show].to_string())

    _write_memo(opp, sc, binding)
    print("\nWritten: outputs/q2_2_opportunity_ranking.csv, q2_2_constraint_scenarios.csv, q2_2_memo.md")


def _md_table(df, cols, index_name="row"):
    header = f"| {index_name} | " + " | ".join(cols) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    out = [header, sep]
    for idx, r in df.iterrows():
        out.append(f"| {idx} | " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _write_memo(opp, sc, binding):
    top_opp = opp.head(5)
    binding_name = binding.index[0]
    binding_label = sc.loc[binding_name, "label"]
    lines = []
    lines.append("# Q2.2 — Key opportunities and challenges for sustainable minerals development\n")
    lines.append("**Question:** What are the key opportunities and challenges for "
                 "sustainable minerals development?\n")
    lines.append("**Method:** a mineral-by-mineral opportunity score (demand pull, domestic "
                 "geology, circular potential, strategic supply-security value, economic value) "
                 "from the firm-grounded register + MFA, and constraint-relaxation scenarios in "
                 "the ABM that relax one barrier at a time over 30 years (STPR 3.5%). Figures "
                 "are model behaviour, not forecasts.\n")

    lines.append("## Opportunities — top-ranked minerals/pathways\n")
    lines.append("> **Critical vs growth minerals.** Per the Vision 2035 Technical Annex, **copper is "
                 "a UK *growth* mineral** (fundamental to advanced manufacturing & clean energy), not a "
                 "current UK *critical* mineral — it is tagged *growth* below. The other tracked metals "
                 "(REE, Li, Co, Ni, Al, Sb) are critical. So the opportunity set is best read as "
                 "**'critical & growth minerals'**, and copper's strong ranking reflects industrial "
                 "resilience rather than critical-supply scarcity.\n")
    for m, r in top_opp.iterrows():
        tag = ("growth" if m in P.GROWTH_MINERALS
               else "critical" if r["critical"] else "bulk")
        lines.append(f"- **{m}** ({tag}, score {r['opportunity_score']}): {r['pathway']} — "
                     f"key challenge: *{r['key_challenge']}*.")
    lines.append("")
    lines.append(_md_table(opp, ["critical", "opportunity_score", "pathway", "key_challenge",
                                 "domestic_geology", "import_dependence", "named_miners"],
                           index_name="mineral"))

    lines.append("\n## Challenges — what is the binding constraint?\n")
    lines.append(f"Relaxing constraints one at a time, the single change that unlocks the most "
                 f"development is **`{binding_name}` ({binding_label})** "
                 f"(+{int(sc.loc[binding_name, 'd_mines'])} project(s), "
                 f"+£{sc.loc[binding_name, 'd_cum_gva_gbp_m']}m discounted GVA vs baseline).")
    lines.append("")
    lines.append("Ranked single-constraint unlocks:")
    for n, r in binding.iterrows():
        lines.append(f"- **{r['label']}** — mines +{int(r['d_mines'])}, GVA "
                     f"+£{r['d_cum_gva_gbp_m']}m, projects: {r['projects_unlocked']}")
    lines.append("")
    lines.append(_md_table(sc, ["label", "mines_opened", "projects_unlocked",
                                "crit_domestic_share_end", "end_jobs", "cum_disc_gva_gbp_m",
                                "d_cum_co2_kt"], index_name="scenario"))

    lines.append("\n## Key findings\n")
    lines.append("1. **The best critical-mineral deposits are constrained by social licence, "
                 "not economics.** NI's highest-quality antimony/gold prospect (Dalradian) clears "
                 "the NPV hurdle but is blocked by community opposition; a credible community-"
                 "benefit/social-licence package is what brings contested deposits forward.")
    lines.append("2. **Bulk/industrial minerals (baryte, salt, aggregates) are the low-friction "
                 "near-term opportunity** — they advance under modest finance/permitting support "
                 "with low social-licence risk.")
    lines.append("3. **Critical-mineral security is mainly a recycling/feedstock story, not a "
                 "primary-mining story** — there is little domestic REE/Li/Co/Ni geology, so the "
                 "opportunity is recovery from end-of-life products, constrained by collection.")
    lines.append("4. **The 'enabling-environment' bundle unlocks the most** but raising ambition "
                 "trades off against CO₂/impact — hence the *sustainable* framing: pair extraction "
                 "enablers with high-ESG conditions and community benefit.\n")

    lines.append("*Behavioural thresholds (dev hurdle, social-licence floor, risk→delay) are "
                 "PROXY; calibrate with planning/licensing records and community evidence.*")

    with open(os.path.join(OUT, "q2_2_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
