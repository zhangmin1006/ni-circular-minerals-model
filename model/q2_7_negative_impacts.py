"""
Q2.7 — "What are the potential ECONOMIC negative impacts of mineral development?"

This experiment answers the consultation question as literally posed: it focuses
ONLY on the *economic* downsides of mineral development (primarily primary mining),
NOT the environmental pressures (those remain tracked by the I-O CO2/PM satellites
and are out of scope here).

It quantifies five economic negatives — each grounded in the Minviro report —
across policy scenarios, and shows how circular activity avoids most of them and
how responsible, *managed* development mitigates the rest:

  1. Benefit leakage (enclave economy)        — Minviro 2.2.5 / Galmoy-Lisheen
  2. Closure cliff + remediation liability     — Minviro 1.4.6.8 (Fig 1.33)
  3. Agriculture & tourism displacement        — Minviro 3.4.2.4 / 3.4.2.5
  4. Boom-bust / price-volatility exposure     — Minviro / Appendix A
  5. Stranded / sunk capital on contested projects — Dalradian Curraghinalt

Figures are model behaviour under PROXY assumptions, not forecasts; the credible
content is the relative contrast (primary high; circular low; managed mitigated).

Run:  python q2_7_negative_impacts.py
Outputs: outputs/q2_7_impacts.csv, outputs/q2_7_memo.md
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import seed_parameters as P
from coupling import CoupledModel
import econ_impact_module as EI

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

GREEN_DEMAND = {"REE_magnet": P.DEMAND_GROWTH_WIND, "Lithium": P.DEMAND_GROWTH_EV,
                "Cobalt": 0.06, "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}

SCENARIOS = {
    "1_baseline": {"policy": {}, "label": "Baseline (current trajectory)"},
    "2_circular_innovation": {"policy": {
        "recycling_grant": 0.4, "collection_infrastructure": 1.0, "innovation_grant": 0.5,
        "design_standards": 0.6, "recycled_content_procurement": 0.4},
        "label": "Circular innovation (no new mine)"},
    "3_primary_unmanaged": {"policy": {
        "exploration_grant": 0.18, "permit_years": 3, "esg_cost": 0.04,
        "finance_support": 0.6, "community_benefit": 0.4},
        "label": "Primary extraction (lightly managed, no local content)"},
    "4_integrated": {"policy": {
        "exploration_grant": 0.15, "permit_years": 3, "community_benefit": 0.4,
        "esg_cost": 0.10, "finance_support": 0.5, "recycling_grant": 0.4,
        "collection_infrastructure": 1.0, "innovation_grant": 0.4,
        "design_standards": 0.6, "local_supplier_support": 0.6},
        "label": "Integrated circular + primary"},
    "5_responsible_managed": {"policy": {
        "exploration_grant": 0.15, "permit_years": 5, "esg_cost": 0.18,
        "community_benefit": 0.4, "finance_support": 0.5, "local_supplier_support": 0.8,
        "skills_support": 0.6, "recycling_grant": 0.4, "collection_infrastructure": 1.0,
        "innovation_grant": 0.5},
        "label": "Responsible, managed primary (bonded + local content + hedge)"},
}


def disc_sum(series, stpr=P.STPR):
    return float(sum(v / (1 + stpr) ** t for t, v in enumerate(series)))


def run_scenario(name, cfg):
    pol = cfg["policy"]
    m = CoupledModel(name=name, policy=pol, demand_growth=GREEN_DEMAND, seed=42,
                     use_ree_pilot=True, adaptive=True, use_cge=True)
    df = m.run().reset_index(drop=True)
    cum = m.cumulative_discounted
    gva_mine = float(P.GVA_COEFF[P.S["Mining_Quarrying"]])
    gva_rec = float(P.GVA_COEFF[P.S["Recycling_Secondary"]])
    mining_gva_pa = (df["mining_fd_gbp_m"] * gva_mine).tolist()
    rec_gva_pa = (df["recycling_fd_gbp_m"] * gva_rec).tolist()
    minerals_gva = disc_sum([a + b for a, b in zip(mining_gva_pa, rec_gva_pa)])
    last = df.iloc[-1]
    end_mining_gva = float(last["mining_fd_gbp_m"]) * gva_mine
    end_mining_jobs = float(last["mining_jobs"])
    mines_opened = int(last["mines_opened"])
    disc_active_mine_years = disc_sum(df["mines_opened"].tolist())

    retention = EI.local_retention(pol)
    mgmt = EI.management_intensity(pol)
    hedge = EI.circular_hedge(pol)

    leaked = EI.benefit_leakage_gbp_m(minerals_gva, retention)
    closure = EI.closure_liability_gbp_m(mines_opened, mgmt)
    displaced = EI.displacement_gbp_m(disc_active_mine_years, mgmt)
    boom = EI.boom_bust_var_gbp_m(end_mining_gva)
    stranded = EI.stranded_capital_gbp_m(mines_opened, hedge)

    neg_total = leaked + closure + displaced            # deterministic GVA-equiv losses
    gross_gva = cum["gva"]
    net_local = gross_gva - neg_total
    return {
        "scenario": name, "label": cfg["label"],
        "cum_disc_gva_gbp_m": round(gross_gva, 1),
        "minerals_direct_gva_gbp_m": round(minerals_gva, 1),
        "benefit_leakage_gbp_m": round(leaked, 1),
        "closure_liability_gbp_m": round(closure, 1),
        "agri_tourism_displacement_gbp_m": round(displaced, 1),
        "econ_negative_total_gbp_m": round(neg_total, 1),
        "econ_negative_per_gva": round(neg_total / gross_gva, 3) if gross_gva else 0.0,
        "net_local_gva_gbp_m": round(net_local, 1),
        "boom_bust_var_gbp_m_pa": round(boom, 2),
        "stranded_capital_at_risk_gbp_m": round(stranded, 1),
        "closure_cliff_gva_gbp_m_pa": round(end_mining_gva, 2),
        "closure_cliff_jobs": round(end_mining_jobs, 1),
        "local_retention": round(retention, 3),
        "mgmt_intensity": round(mgmt, 3),
        "mines_opened": mines_opened,
    }


def main():
    rows = [run_scenario(n, c) for n, c in SCENARIOS.items()]
    df = pd.DataFrame(rows).set_index("scenario")
    df.to_csv(os.path.join(OUT, "q2_7_impacts.csv"))

    print("=" * 122)
    print("Q2.7 — ECONOMIC NEGATIVE IMPACTS of mineral development (30-yr horizon, STPR 3.5%)")
    print("=" * 122)
    show = ["label", "benefit_leakage_gbp_m", "closure_liability_gbp_m",
            "agri_tourism_displacement_gbp_m", "econ_negative_total_gbp_m",
            "econ_negative_per_gva", "boom_bust_var_gbp_m_pa", "stranded_capital_at_risk_gbp_m",
            "net_local_gva_gbp_m"]
    with pd.option_context("display.width", 240, "display.max_columns", None):
        print(df[show].to_string())

    _write_memo(df)
    print("\nWritten: outputs/q2_7_impacts.csv, q2_7_memo.md")


def _md_table(df, cols, index_name):
    out = [f"| {index_name} | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for idx, r in df.iterrows():
        out.append(f"| {idx} | " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _write_memo(df):
    base = df.loc["1_baseline"]
    circ = df.loc["2_circular_innovation"]
    prim = df.loc["3_primary_unmanaged"]
    integ = df.loc["4_integrated"]
    mng = df.loc["5_responsible_managed"]
    lines = []
    lines.append("# Q2.7 — Potential economic negative impacts of mineral development\n")
    lines.append("**Question (as posed):** *What are the potential economic negative impacts of "
                 "mineral development?* This answer focuses **only on the economic downsides** of "
                 "(primarily) primary extraction — the environmental impacts (carbon, air, land, "
                 "water, biodiversity, tailings) are a separate question and remain tracked by the "
                 "model's I-O CO₂/PM satellites; they are **out of scope here**.\n")
    lines.append("**Method (grounded in the Minviro report):** five economic negatives are quantified "
                 "from the coupled model across policy scenarios, discounted at STPR 3.5% over 30 "
                 "years. Magnitudes are PROXY (data_register); the credible content is the **relative "
                 "contrast** — primary extraction carries high economic-negative risk, circular "
                 "activity carries little, and responsible *managed* development mitigates it.\n")

    lines.append("## The five economic negative impacts\n")
    lines.append("1. **Benefit leakage (the enclave-economy risk).** GVA and jobs leak *out* of NI "
                 "when specialist labour and equipment are imported rather than sourced locally — "
                 "Minviro's central caveat (it warns benefits can be *\"economically detached from the "
                 "regions\"* and cites the closed Irish mines **Galmoy and Lisheen**, where specialist "
                 "construction firms limited local employment). In the model, leakage = (1 − local "
                 "retention) × minerals GVA, and retention rises with local-supplier development + a "
                 "skills pipeline.")
    lines.append("2. **Closure cliff + remediation liability.** A mine's direct GVA and jobs **end at "
                 "closure** (life-of-mine ≈ 18 yrs), a local boom-bust cliff within the horizon; and "
                 "**closure/remediation is a public liability if it is not bonded** (Minviro's "
                 "mine-closure cost analysis). A responsible stance bonds closure, moving the liability "
                 "off the public purse.")
    lines.append("3. **Agriculture & tourism displacement.** A mine's land take and amenity loss "
                 "displace host-area farming and tourism output (Minviro devotes sections to both) — "
                 "acute for a rural/AONB setting like the Sperrins. Progressive rehabilitation shortens "
                 "the displaced period.")
    lines.append("4. **Boom-bust / price-volatility exposure.** Commodity prices are volatile, so a "
                 "large share of mining revenue/GVA is *at risk* year to year (Minviro notes price "
                 "volatility and volatile inflows). This is reported as annual revenue-at-risk on the "
                 "mining GVA.")
    lines.append("5. **Stranded / sunk capital on contested, long-lead projects.** A contested project "
                 "(Dalradian's Curraghinalt — ~£250m proposed, a ~21-year planning inquiry) risks "
                 "capital that is **sunk without ever operating**, or **stranded mid-life** by "
                 "recycling/substitution or a price collapse. A circular (recovery-capacity) hedge "
                 "lowers reliance on the single mine and the exposure.\n")

    lines.append("## Economic-negative profile by scenario (£m, discounted)\n")
    lines.append(_md_table(df, ["label", "benefit_leakage_gbp_m", "closure_liability_gbp_m",
                                "agri_tourism_displacement_gbp_m", "econ_negative_total_gbp_m",
                                "boom_bust_var_gbp_m_pa", "stranded_capital_at_risk_gbp_m",
                                "net_local_gva_gbp_m"], "scenario"))
    lines.append(f"\n*`econ_negative_total` = leakage + closure liability + agri/tourism displacement "
                 f"(the deterministic GVA-equivalent losses). `boom_bust_var` (annual revenue-at-risk) "
                 f"and `stranded_capital_at_risk` are risk exposures, reported separately. "
                 f"`net_local_gva` = discounted GVA minus the deterministic negatives.*")

    lines.append("\n## Findings\n")
    lines.append(f"1. **Primary extraction carries the heavy economic-negative load.** Lightly "
                 f"managed, it runs **£{prim['econ_negative_total_gbp_m']:,.0f}m** of deterministic "
                 f"economic negatives (leakage £{prim['benefit_leakage_gbp_m']:,.0f}m + closure "
                 f"liability £{prim['closure_liability_gbp_m']:,.0f}m + displacement "
                 f"£{prim['agri_tourism_displacement_gbp_m']:,.0f}m), i.e. "
                 f"{prim['econ_negative_per_gva']:.0%} of its discounted GVA, **plus** "
                 f"£{prim['stranded_capital_at_risk_gbp_m']:,.0f}m of contested capital at risk and "
                 f"~£{prim['boom_bust_var_gbp_m_pa']:,.1f}m/yr of price-volatility exposure — and a "
                 f"closure cliff of ~£{prim['closure_cliff_gva_gbp_m_pa']:,.1f}m GVA / "
                 f"{prim['closure_cliff_jobs']:,.0f} jobs that vanish when the mine closes.")
    lines.append(f"2. **Circular activity avoids almost all of it.** With no new mine the circular "
                 f"scenario has **no** closure liability, displacement, boom-bust or stranded-capital "
                 f"risk — its only economic negative is residual leakage "
                 f"(£{circ['benefit_leakage_gbp_m']:,.0f}m), so its economic-negative intensity "
                 f"({circ['econ_negative_per_gva']:.0%}) is far below primary "
                 f"({prim['econ_negative_per_gva']:.0%}). Recycling is the low-economic-risk route to "
                 f"the same supply security.")
    lines.append(f"3. **Responsible, managed development materially mitigates the negatives.** Bonded "
                 f"closure + progressive rehabilitation + local-content/skills + a circular hedge cut "
                 f"the managed scenario's economic negatives to **£{mng['econ_negative_total_gbp_m']:,.0f}m** "
                 f"(vs £{prim['econ_negative_total_gbp_m']:,.0f}m unmanaged) and its stranded-capital "
                 f"risk to £{mng['stranded_capital_at_risk_gbp_m']:,.0f}m — chiefly by lifting local "
                 f"retention to {mng['local_retention']:.0%} (leakage "
                 f"£{prim['benefit_leakage_gbp_m']:,.0f}m → £{mng['benefit_leakage_gbp_m']:,.0f}m) and "
                 f"bonding closure (liability £{prim['closure_liability_gbp_m']:,.0f}m → "
                 f"£{mng['closure_liability_gbp_m']:,.0f}m).")
    lines.append(f"4. **So the net local benefit depends on *how* minerals are developed.** Net local "
                 f"GVA after the economic negatives is £{prim['net_local_gva_gbp_m']:,.0f}m (unmanaged "
                 f"primary) vs £{mng['net_local_gva_gbp_m']:,.0f}m (responsible managed) vs "
                 f"£{integ['net_local_gva_gbp_m']:,.0f}m (integrated) — the same headline activity "
                 f"yields very different *retained* value once leakage, closure and displacement are "
                 f"counted. This is the economic mirror of the Q2.5/Q2.6 retained-benefit point.")
    lines.append("5. **Read with Q2.6.** Q2.6 reports the gross economic *benefits*; this question "
                 "nets off the economic *costs/risks*. The honest figure for a contested primary mine "
                 "is the **net** — and it is most negative when the project is lightly managed, "
                 "import-dependent and unhedged.\n")

    lines.append("## How to minimise the economic negatives\n")
    lines.append("- **Cut leakage:** local-supplier development + a skills pipeline (Q2.5) keep GVA/"
                 "jobs in NI (retention ~70% → ~92% in the managed scenario).")
    lines.append("- **De-risk closure:** mandate **bonded** mine-closure and progressive "
                 "rehabilitation so remediation is not a public liability and land returns to "
                 "productive (agri/tourism) use sooner.")
    lines.append("- **Protect agriculture & tourism:** site selection, buffer zones and rehabilitation "
                 "to limit displaced rural output; weigh it explicitly against mining GVA.")
    lines.append("- **Damp boom-bust:** offtake + price-floor contracts (cf. Q2.3) and economic "
                 "diversification reduce revenue-at-risk and the closure-cliff shock.")
    lines.append("- **Avoid stranded capital:** pair any contested primary project with circular "
                 "(recovery) capacity as a hedge, and stage capital against permitting milestones.\n")

    lines.append("## Sources & assumptions\n")
    for s in ("Minviro Final Report sec 2.2.5 (retained employment) + Galmoy/Lisheen leakage "
              "comparison — benefits can be 'economically detached from the regions'",
              "Minviro Final Report sec 1.4.6.8 'Mine Closure' (Fig 1.33 closure-cost estimates) — "
              "closure/remediation cost and the bonded-vs-public-liability distinction",
              "Minviro Final Report sec 3.4.2.4 (Agriculture) / 3.4.2.5 (Tourism) — host-area "
              "displacement of farming and tourism output",
              "Minviro Final Report / Appendix A — commodity price volatility and volatile inflows "
              "(boom-bust revenue-at-risk)",
              "Dalradian Curraghinalt (company_register.csv; Guardian 2026) — ~£250m proposed capital, "
              "~21-yr planning inquiry: sunk/stranded-capital risk on a contested long-lead project",
              "Parameters (life-of-mine 18 yr, closure cost £35m/mine, agri+tourism displacement "
              "£3m/mine-yr, price volatility 0.30, base retention 0.70) are PROXY/desk values in "
              "data_register.csv — replace with NISRA agri/tourism GVA-by-district, site closure-cost "
              "estimates and a firm-level local-content survey to calibrate"):
        lines.append(f"- {s}")
    lines.append("\n*Economic-negative magnitudes are illustrative under stated proxy assumptions, "
                 "not forecasts; the robust message is the ranking (primary > integrated > managed; "
                 "circular lowest) and that local content, bonded closure and a circular hedge are the "
                 "levers that minimise the economic downside.*")

    with open(os.path.join(OUT, "q2_7_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
