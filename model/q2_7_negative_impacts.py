"""
Q2.7 — "What are the negative impacts, and how can they be minimised?"

Reports the Minviro Appendix A impact set across policy scenarios — CO2 and PM
(validated I-O satellites) plus relative pressure indices for water, land
transformation, biodiversity and mine waste/tailings — together with
**eco-efficiency** (impact per £m GVA) and the **recycling-vs-primary** contrast,
and shows how a **high-ESG / low-impact** stance mitigates the local burden.

Impacts are site-specific (Minviro): the land/water/biodiversity burden of any
primary mine concentrates on its host council area and receptors.

Run:  python q2_7_negative_impacts.py
Outputs: outputs/q2_7_impacts.csv, outputs/q2_7_memo.md
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import seed_parameters as P
from coupling import CoupledModel
import impact_module as I

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

GREEN_DEMAND = {"REE_magnet": P.DEMAND_GROWTH_WIND, "Lithium": P.DEMAND_GROWTH_EV,
                "Cobalt": 0.06, "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}

SCENARIOS = {
    "1_baseline": {"policy": {}, "label": "Baseline"},
    "2_circular_innovation": {"policy": {
        "recycling_grant": 0.4, "collection_infrastructure": 1.0, "product_passport": 0.5,
        "design_standards": 0.6, "recycled_content_procurement": 0.4}, "label": "Circular innovation"},
    "3_primary_extraction": {"policy": {
        "exploration_grant": 0.18, "permit_years": 3, "esg_cost": 0.08,
        "finance_support": 0.6, "community_benefit": 0.4}, "label": "Primary extraction"},
    "4_integrated": {"policy": {
        "exploration_grant": 0.15, "community_benefit": 0.4, "recycling_grant": 0.4,
        "collection_infrastructure": 1.0, "design_standards": 0.6,
        "recycled_content_procurement": 0.4, "finance_support": 0.5}, "label": "Integrated"},
    "6_high_esg_low_impact": {"policy": {
        "exploration_grant": 0.15, "permit_years": 5, "esg_cost": 0.18, "community_benefit": 0.4,
        "recycling_grant": 0.4, "collection_infrastructure": 1.0, "design_standards": 0.6},
        "label": "High-ESG / low-impact"},
}


def disc_sum(series, stpr=P.STPR):
    return float(sum(v / (1 + stpr) ** t for t, v in enumerate(series)))


def run_scenario(name, cfg):
    pol = cfg["policy"]
    m = CoupledModel(name=name, policy=pol, demand_growth=GREEN_DEMAND, seed=42,
                     use_ree_pilot=True, adaptive=True, use_cge=True)
    df = m.run().reset_index(drop=True)
    cum = m.cumulative_discounted
    esg = pol.get("esg_cost", 0.0)
    # relative pressures per year -> discounted cumulative
    press = {c: [] for c in I.CATEGORIES}
    for _, r in df.iterrows():
        ap = I.annual_pressures(r["mining_fd_gbp_m"], r["recycling_fd_gbp_m"], esg_cost=esg)
        for c in I.CATEGORIES:
            press[c].append(ap[c])
    cum_press = {c: disc_sum(press[c]) for c in I.CATEGORIES}
    cum_pm = disc_sum(df["pm_t"].tolist())
    gva = cum["gva"] or 1.0
    return {
        "scenario": name, "label": cfg["label"],
        "cum_disc_co2_kt": round(cum["co2"], 1),
        "cum_disc_pm_t": round(cum_pm, 1),
        "water_pressure": round(cum_press["water"], 0),
        "land_pressure": round(cum_press["land"], 0),
        "biodiversity_pressure": round(cum_press["biodiversity"], 0),
        "waste_pressure": round(cum_press["waste"], 0),
        "co2_per_gva": round(cum["co2"] / gva, 3),
        "land_per_gva": round(cum_press["land"] / gva, 3),
        "cum_disc_gva_gbp_m": round(cum["gva"], 1),
        "mines_opened": int(df.iloc[-1]["mines_opened"]),
    }


def main():
    rows = [run_scenario(n, c) for n, c in SCENARIOS.items()]
    df = pd.DataFrame(rows).set_index("scenario")
    df.to_csv(os.path.join(OUT, "q2_7_impacts.csv"))

    print("=" * 116)
    print("Q2.7 — NEGATIVE IMPACTS (30-yr horizon, STPR 3.5%; pressures = relative indices)")
    print("=" * 116)
    show = ["label", "cum_disc_co2_kt", "cum_disc_pm_t", "water_pressure", "land_pressure",
            "biodiversity_pressure", "waste_pressure", "co2_per_gva", "land_per_gva"]
    with pd.option_context("display.width", 230, "display.max_columns", None):
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
    prim = df.loc["3_primary_extraction"]
    circ = df.loc["2_circular_innovation"]
    esg = df.loc["6_high_esg_low_impact"]
    lines = []
    lines.append("# Q2.7 — Negative impacts and how to minimise them\n")
    lines.append("**Method (grounded in Minviro Appendix A):** the model's validated CO2 (ktCO2e) "
                 "and PM (t) satellites are reported with relative pressure indices for the other "
                 "Appendix-A impact groups — **water** (availability & quality), **land "
                 "transformation** (take, habitat loss, landscape), **biodiversity**, and **mine "
                 "waste/tailings** — plus **eco-efficiency** (impact per £m GVA). Per Appendix A the "
                 "ultimate receptors are *people and biodiversity*, and impacts are **site-specific** "
                 "(receptors, design, operation and **closure**). Pressure indices are dimensionless "
                 "PROXIES; the credible content is the relative contrast and per-£GVA efficiency.\n")

    lines.append("## Impact profile by scenario\n")
    lines.append(_md_table(df, ["label", "cum_disc_co2_kt", "cum_disc_pm_t", "water_pressure",
                                "land_pressure", "biodiversity_pressure", "waste_pressure",
                                "co2_per_gva", "land_per_gva"], "scenario"))

    lines.append("\n## Findings\n")
    lines.append(f"1. **Primary mining carries the heavy local burden.** It is land-, water-, "
                 f"biodiversity- and tailings-intensive: the primary-extraction scenario's land "
                 f"pressure ({prim['land_pressure']:.0f}) and waste/tailings pressure "
                 f"({prim['waste_pressure']:.0f}) far exceed the circular scenario's "
                 f"({circ['land_pressure']:.0f} / {circ['waste_pressure']:.0f}). These are the "
                 f"impacts Minviro Appendix A treats as site-specific — land take, habitat loss, "
                 f"water draw-down, tailings, dust, noise and closure liabilities.")
    lines.append(f"2. **Recycling is far lower-impact per unit benefit.** Secondary supply avoids "
                 f"the land/water/biodiversity/tailings burden almost entirely and its carbon "
                 f"footprint is ~{I.RECYCLING_CO2_VS_PRIMARY:.0%} of primary — so the circular "
                 f"scenario has much lower land-per-£GVA ({circ['land_per_gva']:.2f}) than primary "
                 f"extraction ({prim['land_per_gva']:.2f}). Circularity is the impact-minimising "
                 f"route to the same supply security.")
    lines.append(f"3. **High-ESG design materially mitigates the local burden.** Applying high-ESG "
                 f"conditions (water recycling, progressive rehabilitation, biodiversity net gain, "
                 f"dust/noise controls, closure planning) cuts primary pressures by up to "
                 f"~{I.ESG_MAX_MITIGATION:.0%}: the high-ESG scenario's land pressure "
                 f"({esg['land_pressure']:.0f}) sits well below unmitigated primary extraction "
                 f"({prim['land_pressure']:.0f}) for comparable development.")
    lines.append(f"4. **Carbon rises with activity but is efficient.** Cumulative discounted CO2 "
                 f"grows from {base['cum_disc_co2_kt']:.0f} kt (baseline) as recycling/processing "
                 f"expands, but CO2-per-£GVA stays low — and recycling displaces higher-carbon "
                 f"primary + import routes. Q2.7 should be read with Q2.6: the impacts buy real GVA, "
                 f"jobs and avoided imports.")
    lines.append("5. **Impacts are site-specific and concentrated.** Any primary mine's land/"
                 "biodiversity/water burden falls on its host council area (e.g. Curraghinalt in "
                 "Fermanagh & Omagh) and named receptors — so impact assessment, community benefit "
                 "and closure bonds must be project- and place-specific, not modelled generically.\n")

    lines.append("## Minimisation hierarchy (Minviro Appendix A)\n")
    lines.append("- **Avoid** — prioritise recycling/secondary supply and design-for-disassembly "
                 "(lowest land/water/biodiversity footprint).")
    lines.append("- **Mitigate** — where primary extraction proceeds, require high-ESG design: water "
                 "stewardship, progressive rehabilitation, biodiversity net gain, dust/noise/traffic "
                 "controls.")
    lines.append("- **Manage closure** — bonded mine-closure and post-closure monitoring (a distinct "
                 "Appendix-A impact group); and manage socio-economic risks (boom-bust, wage "
                 "inflation, public-service costs, agriculture/tourism displacement) locally.\n")

    lines.append("## Sources & assumptions\n")
    for s in ("Minviro Appendix A: impact groups (land transformation, water availability/quality, "
              "air quality & noise, GHG, biodiversity, mine closure, tailings/waste rock); site-"
              "specific receptors; avoid > mitigate > closure hierarchy",
              "Minviro CLCA + ree_pilot: recycling carbon footprint ~30% of primary",
              "CO2/PM are the model's I-O satellites (NAEI/DAERA-class, PROXY); water/land/"
              "biodiversity/waste are dimensionless relative pressure indices (PROXY) — replace with "
              "site EIA + ecoinvent/EXIOBASE characterisation factors"):
        lines.append(f"- {s}")

    with open(os.path.join(OUT, "q2_7_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
