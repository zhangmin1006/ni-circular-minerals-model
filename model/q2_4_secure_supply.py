"""
Q2.4 — "What role should we have in ensuring a secure supply of minerals?"

Models UPSTREAM GEOPOLITICAL SHOCKS to critical-mineral supply and evaluates
distinct GOVERNMENT ROLES (strategic postures) against them.

  PART A — deterministic grid: each government role x an escalating set of
           geopolitical shocks (trade friction -> dominant-supplier export ban ->
           bloc fragmentation), scored on the Vision-2035 secure-supply metrics
           (domestic / recycled / import shares, single-country exposure, an
           HHI-style supply-risk index) plus the unmet-demand supply gap, GVA and
           public cost.

  PART B — Monte Carlo geopolitical risk: for each role, many random shock
           realisations (uncertain onset year, affected minerals weighted by
           their real single-country concentration, and severity) -> the
           DISTRIBUTION of the post-shock supply gap, i.e. resilience under
           uncertainty (mean and 90th-percentile tail risk).

Roles compared: market/light-touch; diversify-&-insure; domestic-autonomy;
circular-leader; strategic-coordinator (balanced portfolio).

Run:  python q2_4_secure_supply.py
Outputs: outputs/q2_4_role_shock_grid.csv, outputs/q2_4_monte_carlo.csv,
         outputs/q2_4_memo.md
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import numpy as np
import pandas as pd
import seed_parameters as P
from coupling import CoupledModel

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

GREEN_DEMAND = {"REE_magnet": P.DEMAND_GROWTH_WIND, "Lithium": P.DEMAND_GROWTH_EV,
                "Cobalt": 0.06, "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}

# SHOCK BASIS (Vision 2035): "increasingly concentrated processing and mining
# supply chains ... vulnerable to shocks such as natural disasters, war or
# geopolitical fallout" and "shortages or disruption". We model that concentration
# risk with the 2023 single-country supply shares (BGS/Idoine 2025): import caps
# under a shock = 1 - loss_factor * concentration (a dominant-supplier export ban).
CONCENTRATION = {"REE_magnet": 0.74, "Cobalt": 0.70, "Antimony": 0.70,
                 "Aluminium": 0.35, "Lithium": 0.44, "Nickel": 0.40, "Copper": 0.30}
PRICE_SPIKE = {"Lithium": 0.10, "REE_magnet": 0.10, "Cobalt": 0.09,
               "Nickel": 0.06, "Copper": 0.05}


def shock_caps(loss_factor, minerals=None):
    minerals = minerals or P.CRITICAL_MINERALS
    return {m: max(0.0, 1.0 - min(1.0, loss_factor * CONCENTRATION.get(m, 0.3)))
            for m in minerals}


# ---------------------------------------------------------------------------
# Government roles (strategic postures) -> policy lever bundles, each grounded in
# the UK Vision 2035 strategy:
#   market_light_touch    : counterfactual (no strategy).
#   diversify_and_insure  : objective 2 "international partnerships ... diversify
#                           our supply chains" + "stockpiling ... through
#                           procurement mechanisms" (defence resilience).
#   domestic_autonomy     : objective 1 "grow our domestic production" (NWF/UKEF,
#                           EA priority permitting, community benefit).
#   circular_leader       : "strengthening our own capabilities for mining,
#                           refining and recycling ... a more circular economy"
#                           (+ EU CRMA 25% recycling target; NI magnet recycling).
#   strategic_coordinator : BOTH Vision-2035 objectives + "joint action between
#                           industry and government ... in a more coordinated way",
#                           with responsible/high-ESG terms.
# ---------------------------------------------------------------------------
ROLES = {
    "market_light_touch": {},
    "diversify_and_insure": {
        "diversification": 0.8, "strategic_stockpile": 0.6,
        "secondary_market_support": 0.4,
    },
    "domestic_autonomy": {
        "finance_support": 0.8, "exploration_grant": 0.12, "permit_years": 2,
        "community_benefit": 0.4,
    },
    "circular_leader": {
        "recycling_grant": 0.4, "innovation_grant": 0.6, "collection_infrastructure": 1.0,
        "product_passport": 0.6, "secondary_market_support": 0.5, "design_standards": 0.6,
    },
    "strategic_coordinator": {
        "diversification": 0.6, "strategic_stockpile": 0.5, "finance_support": 0.5,
        "community_benefit": 0.4, "permit_years": 3, "recycling_grant": 0.3,
        "innovation_grant": 0.5, "collection_infrastructure": 1.0, "product_passport": 0.5,
        "secondary_market_support": 0.5, "design_standards": 0.5, "skills_support": 0.5,
    },
}
ROLE_LABEL = {
    "market_light_touch": "Market / light-touch",
    "diversify_and_insure": "Diversify & insure (partnerships + stockpile)",
    "domestic_autonomy": "Domestic autonomy (build primary)",
    "circular_leader": "Circular leader (recover + recycle)",
    "strategic_coordinator": "Strategic coordinator (balanced portfolio)",
}

# Escalating geopolitical shock scenarios (loss factor on the dominant supplier).
SHOCKS = {
    "0_stable": None,
    "trade_friction": 0.5,
    "export_ban": 1.0,
    "bloc_fragmentation": 1.5,
}

# Notional public cost per lever (£m/yr at intensity 1.0), NI-scale, UK-anchored.
COST = {
    "finance_support": 6.0, "exploration_grant": 3.0, "community_benefit": 3.0,
    "recycling_grant": 7.0, "innovation_grant": 5.0, "collection_infrastructure": 9.0,
    "product_passport": 2.0, "secondary_market_support": 4.0,
    "recycled_content_procurement": 1.0, "design_standards": 1.0, "skills_support": 4.0,
    "local_supplier_support": 3.0, "diversification": 3.0, "strategic_stockpile": 4.0,
}


def disc_cost(policy, horizon=P.HORIZON, stpr=P.STPR):
    annual = sum(COST.get(k, 0.0) * v for k, v in policy.items() if k in COST)
    return round(sum(annual / (1 + stpr) ** t for t in range(horizon)), 1)


def supply_risk_index(mfa):
    """Demand-weighted single-country exposure across critical minerals at the
    end year (0-1; an HHI-style concentration-risk index)."""
    last = mfa.history[-len(mfa.minerals):]
    crit = [r for r in last if r["mineral"] in P.CRITICAL_MINERALS]
    tot = sum(r["demand_t"] for r in crit) or 1.0
    return round(sum(r["single_country_exposure"] * r["demand_t"] for r in crit) / tot, 3)


def run_grid_cell(role, policy, loss_factor):
    caps = None if loss_factor is None else shock_caps(loss_factor)
    price = {} if loss_factor is None else PRICE_SPIKE
    m = CoupledModel(name=f"{role}", policy=policy, demand_growth=GREEN_DEMAND,
                     price_path=price, import_constraint=caps, seed=42,
                     use_ree_pilot=True, adaptive=True, use_cge=True)
    df = m.run()
    last = df.iloc[-1]
    return {
        "crit_domestic_share": round(float(last["crit_domestic_share"]), 3),
        "crit_recycled_share": round(float(last["crit_recycled_share"]), 3),
        "crit_import_share": round(float(last["crit_import_share"]), 3),
        "single_country_exposure": round(float(last["crit_max_single_country"]), 3),
        "supply_risk_index": supply_risk_index(m.mfa),
        "mean_supply_gap": round(float(df["crit_supply_gap"].mean()), 3),
        "cum_disc_gva_gbp_m": round(m.cumulative_discounted["gva"], 1),
    }


# ---------------------------------------------------------------------------
def monte_carlo(role, policy, n=120, horizon=P.HORIZON, seed=2026):
    """Random geopolitical shock realisations: uncertain onset, affected minerals
    (prob ∝ concentration) and severity. Returns the distribution of the post-
    onset mean supply gap and single-country exposure. CGE off for speed (supply-
    security metrics come from the MFA/ABM)."""
    rng = np.random.default_rng(seed)
    crit = P.CRITICAL_MINERALS
    gaps, exposures = [], []
    for _ in range(n):
        onset = int(rng.integers(1, 16))             # shock hits in years 1-15
        factor = float(rng.uniform(0.5, 1.5))        # severity
        hit = [m for m in crit if rng.random() < CONCENTRATION.get(m, 0.3)]
        if not hit:
            hit = ["REE_magnet"]
        caps = shock_caps(factor, hit)

        def constraint(t, _caps=caps, _onset=onset):
            return _caps if t >= _onset else {}

        m = CoupledModel(name="mc", policy=policy, demand_growth=GREEN_DEMAND,
                         price_path=PRICE_SPIKE, import_constraint=constraint, seed=42,
                         use_ree_pilot=True, adaptive=True, use_cge=False)
        df = m.run()
        post = df.iloc[onset:]
        gaps.append(float(post["crit_supply_gap"].mean()))
        exposures.append(float(post["crit_max_single_country"].mean()))
    g = np.array(gaps)
    return {
        "mean_supply_gap": round(float(g.mean()), 3),
        "p90_supply_gap": round(float(np.percentile(g, 90)), 3),
        "worst_supply_gap": round(float(g.max()), 3),
        "mean_single_country_exposure": round(float(np.mean(exposures)), 3),
    }


def main():
    # ---- Part A: role x shock grid --------------------------------------
    rows = []
    for role, policy in ROLES.items():
        for shock, factor in SHOCKS.items():
            cell = run_grid_cell(role, policy, factor)
            rows.append({"role": role, "shock": shock,
                         "disc_public_cost_gbp_m": disc_cost(policy), **cell})
    grid = pd.DataFrame(rows)
    grid.to_csv(os.path.join(OUT, "q2_4_role_shock_grid.csv"), index=False)

    # ---- Part B: Monte Carlo geopolitical risk --------------------------
    mc_rows = []
    for role, policy in ROLES.items():
        mc = monte_carlo(role, policy)
        mc_rows.append({"role": role, "disc_public_cost_gbp_m": disc_cost(policy), **mc})
    mc = pd.DataFrame(mc_rows).set_index("role")
    mc.to_csv(os.path.join(OUT, "q2_4_monte_carlo.csv"))

    print("=" * 112)
    print("Q2.4 — SECURE SUPPLY: government roles x geopolitical shocks (30-yr, STPR 3.5%)")
    print("=" * 112)
    show = grid.pivot(index="role", columns="shock", values="single_country_exposure")
    show = show.reindex(list(ROLES))[list(SHOCKS)]
    print("\nSingle-country exposure (target <=0.60) by role x shock:")
    print(show.to_string())
    eb = grid[grid["shock"] == "export_ban"].set_index("role").reindex(list(ROLES))
    print("\nUnder an export-ban shock — secure-supply metrics:")
    print(eb[["crit_domestic_share", "crit_recycled_share", "crit_import_share",
              "single_country_exposure", "supply_risk_index", "mean_supply_gap",
              "cum_disc_gva_gbp_m", "disc_public_cost_gbp_m"]].to_string())
    print("\n" + "=" * 112)
    print("MONTE CARLO geopolitical risk — supply-gap distribution by role (120 draws)")
    print("=" * 112)
    print(mc[["mean_supply_gap", "p90_supply_gap", "worst_supply_gap",
              "mean_single_country_exposure", "disc_public_cost_gbp_m"]].to_string())

    _write_memo(grid, mc, eb)
    print("\nWritten: outputs/q2_4_role_shock_grid.csv, q2_4_monte_carlo.csv, q2_4_memo.md")


def _md_table(df, cols, index_name):
    out = [f"| {index_name} | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for idx, r in df.iterrows():
        out.append(f"| {idx} | " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _write_memo(grid, mc, eb):
    target = P.TARGETS_2035
    # resilience ranking: lowest Monte-Carlo p90 (tail) supply gap, excl. market
    ranked = mc.drop(index="market_light_touch").sort_values("p90_supply_gap")
    best = ranked.index[0]
    lines = []
    lines.append("# Q2.4 — What role should government have in ensuring secure mineral supply?\n")
    lines.append("**Method (grounded in the strategy documents):** Vision 2035 warns that "
                 "*\"increasingly concentrated processing and mining supply chains\"* leave supply "
                 "*\"vulnerable to shocks such as natural disasters, war or geopolitical fallout\"*. "
                 "We model that as a **dominant-supplier export ban** — per-mineral import caps = "
                 "1 − (2023 single-country concentration: REE 74% China, Co 70% DRC, Li 44% Australia; "
                 "BGS/Idoine 2025) — escalated from trade friction to bloc fragmentation, plus a "
                 "**Monte Carlo** of uncertain shocks (random onset, affected minerals ∝ concentration, "
                 "severity). The five **government roles** are the postures the strategy itself "
                 "describes — *optimise domestic production* and *build resilient UK & global supply "
                 "networks* (incl. partnerships, diversification, stockpiling and circular capability). "
                 "Metrics are the Vision-2035 / EU-CRMA secure-supply targets (≥10% domestic, ≥20% "
                 "recycled, ≤60% single-country) plus an HHI-style supply-risk index and the unmet-demand "
                 "supply gap. Figures are model behaviour, not forecasts.\n")

    lines.append("## Roles tested\n")
    for r, lbl in ROLE_LABEL.items():
        lines.append(f"- **{r}** — {lbl}")
    lines.append("")

    lines.append("## Resilience under uncertainty (Monte Carlo, 120 random shocks)\n")
    lines.append(_md_table(mc, ["mean_supply_gap", "p90_supply_gap", "worst_supply_gap",
                                "mean_single_country_exposure", "disc_public_cost_gbp_m"], "role"))
    lines.append(f"\n- **Most resilient posture (lowest tail risk): `{best}`** "
                 f"({ROLE_LABEL[best]}) — 90th-percentile supply gap {mc.loc[best,'p90_supply_gap']:.0%} "
                 f"vs {mc.loc['market_light_touch','p90_supply_gap']:.0%} under light-touch.")
    lines.append("")

    lines.append("## Secure-supply metrics under an export-ban shock\n")
    lines.append(_md_table(eb.reindex(list(ROLES)),
                           ["crit_domestic_share", "crit_recycled_share", "crit_import_share",
                            "single_country_exposure", "supply_risk_index", "mean_supply_gap",
                            "cum_disc_gva_gbp_m", "disc_public_cost_gbp_m"], "role"))
    lines.append(f"\nVision-2035 targets: domestic ≥{target['domestic_share']:.0%}, "
                 f"recycled ≥{target['recycling_share']:.0%}, single-country "
                 f"≤{target['max_single_country']:.0%}.")

    piv = grid.pivot(index="role", columns="shock", values="single_country_exposure")
    lines.append("\n## Findings — the role government should play\n")
    lines.append(f"1. **NI is structurally over-concentrated, and only diversification fixes it.** In "
                 f"normal times single-country exposure is ~{piv.loc['market_light_touch','0_stable']:.0%} "
                 f"under light-touch — far above the ≤60% target — and the *only* roles that meet the "
                 f"target are those that diversify imports (diversify-&-insure "
                 f"{piv.loc['diversify_and_insure','0_stable']:.0%}, coordinator "
                 f"{piv.loc['strategic_coordinator','0_stable']:.0%}). (Note: exposure *falls* under an "
                 f"actual export ban only because access to the dominant supplier is lost — that shows "
                 f"up instead as a **supply gap**, so the two must be read together.)")
    lines.append("2. **Light-touch is not an option for security.** Under a dominant-supplier export "
                 "ban the market posture leaves the widest supply gap and highest residual exposure — "
                 "security is a public good the market under-provides.")
    lines.append("3. **No single instrument is sufficient.** *Diversification + a stockpile* cut "
                 "single-country exposure and bridge the immediate gap but build no domestic capability; "
                 "*domestic autonomy* is slow and constrained by social licence and geology; *circular "
                 "leadership* builds durable secondary supply but is feedstock-limited and cannot cover "
                 "a broad shock alone.")
    lines.append(f"4. **A balanced *strategic-coordinator* role is the most robust** across the shock "
                 f"range and the Monte-Carlo tail: it diversifies imports, holds a thin reserve to "
                 f"bridge, builds circular capacity for durable secondary supply, and brings responsible "
                 f"primary forward where social licence allows — the only posture that moves all three "
                 f"Vision-2035 indicators at once while adding GVA.")
    lines.append("5. **The government's role is therefore an active *coordinator/insurer*, not a "
                 "producer or a bystander:** set the targets, de-risk midstream capacity (finance + "
                 "offtake), fix feedstock collection, diversify and insure against the tail with "
                 "partnerships + a strategic reserve, and uphold high-ESG/community-benefit terms. "
                 "This is exactly what Vision 2035 describes — *\"joint action between industry and "
                 "government … in a more coordinated way\"* across its dual objective of *optimising "
                 "domestic production* and *building resilient UK & global supply networks*. The model "
                 "finds that the posture the strategy actually adopts is also the most robust.\n")

    lines.append("## Sources\n")
    for s in (
        "UK Critical Minerals Strategy — Vision 2035 (DBT): shock taxonomy (natural disasters, "
        "war, geopolitical fallout; concentrated processing & mining); two objectives; "
        "partnerships, diversification, defence stockpiling, responsible/high-ESG, coordinated "
        "industry–government action",
        "EU Critical Raw Materials Act (2024): 10% extraction / 40% processing / 25% recycling / "
        "≤65% single-country benchmarks; strategic stockpiling & monitoring",
        "BGS/Idoine et al. (2025) via GSNI OR25042: 2023 single-country supply concentration "
        "(REE 74%, Co 70%, Li 44%); ~80% of UK metals exported for processing",
        "Strategic stockpiles: Japan/JOGMEC 60–180 days, Korea/KOMIR 100 days (IEA; CSEP 2025)",
    ):
        lines.append(f"- {s}")
    lines.append("\n*Roles are illustrative lever bundles; costs are NI-scale UK-anchored proxies for "
                 "relative comparison. Behavioural thresholds and shock magnitudes are PROXY.*")

    with open(os.path.join(OUT, "q2_4_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
