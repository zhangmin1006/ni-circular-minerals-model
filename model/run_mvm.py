"""
NI Circular Minerals MVM (Tier 1) — scenario runner.

Runs the six scenario families over a 30-year horizon, validates the I-O core
against the Minviro anchors, writes results to ../outputs/, and prints a
question-by-question (2.1-2.7) summary.

Run:  python run_mvm.py
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import seed_parameters as P
from coupling import CoupledModel
from indicators import validate_against_minviro, map_to_questions

OUT = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT, exist_ok=True)

# --- demand growth paths (Vision 2035 drivers) -----------------------------
GREEN_DEMAND = {"REE_magnet": 0.08, "Lithium": 0.12, "Cobalt": 0.06,
                "Nickel": 0.05, "Copper": 0.04, "Aluminium": 0.03}

# --- six scenario families (proposal section 7) ----------------------------
SCENARIOS = {
    "1_baseline": dict(policy={}, demand_growth=GREEN_DEMAND),
    "2_circular_innovation": dict(
        policy={"recycling_grant": 0.4, "collection_infrastructure": 1.0,
                "product_passport": 0.5, "design_standards": 0.6,
                "recycled_content_procurement": 0.4, "local_supplier_support": 0.5},
        demand_growth=GREEN_DEMAND),
    "3_primary_extraction": dict(
        policy={"exploration_grant": 0.18, "permit_years": 3, "esg_cost": 0.08,
                "local_supplier_support": 0.6},
        demand_growth=GREEN_DEMAND),
    "4_integrated_circular_primary": dict(
        policy={"exploration_grant": 0.15, "permit_years": 3, "esg_cost": 0.10,
                "recycling_grant": 0.4, "collection_infrastructure": 1.0,
                "design_standards": 0.6, "recycled_content_procurement": 0.4,
                "local_supplier_support": 0.8},
        demand_growth=GREEN_DEMAND),
    "5_supply_shock": dict(
        policy={"recycling_grant": 0.3, "collection_infrastructure": 0.8},
        demand_growth=GREEN_DEMAND,
        price_path={"Lithium": 0.10, "REE_magnet": 0.09, "Cobalt": 0.08,
                    "Nickel": 0.06, "Copper": 0.05}),
    "6_high_esg_low_impact": dict(
        policy={"exploration_grant": 0.15, "permit_years": 5, "esg_cost": 0.18,
                "recycling_grant": 0.4, "collection_infrastructure": 1.0,
                "design_standards": 0.6, "local_supplier_support": 0.7},
        demand_growth=GREEN_DEMAND),
}


def main():
    print("=" * 70)
    print("VALIDATION against Minviro scenario anchors (I-O core)")
    print("=" * 70)
    val = validate_against_minviro()
    for label, r in val.items():
        print(f"\n {label}:")
        print(f"   output £m       : model {r['model_output']:6.1f}  | anchor {r['anchor_output']:6.1f}")
        print(f"   jobs (total)    : model {r['model_jobs']:6.1f}  | anchor {r['anchor_jobs']:6.1f}")
        print(f"   direct mining GVA: model {r['model_direct_mining_gva']:6.2f}  | anchor {r['anchor_gva']:6.2f}")
    with open(os.path.join(OUT, "validation.json"), "w") as f:
        json.dump(val, f, indent=2)

    print("\n" + "=" * 70)
    print("SCENARIO RUNS (30-year horizon, STPR 3.5%)")
    print("=" * 70)
    all_runs = []
    summary = {}
    spatial_rows = []
    for name, cfg in SCENARIOS.items():
        # Tier-3: real REE pilot data, adaptive agents, CGE economy-wide feedback
        m = CoupledModel(name=name, seed=42, use_ree_pilot=True,
                         adaptive=True, use_cge=True, **cfg)
        df = m.run()
        all_runs.append(df)
        q = map_to_questions(df, m.cumulative_discounted)
        summary[name] = q
        print(f"\n--- {name} ---")
        print(f"  Cum. discounted GVA £m : {q['2.6_economic_benefits']['cumulative_discounted_gva_gbp_m']}")
        print(f"  End-year total jobs    : {q['2.5_employment_regional_growth']['total_jobs_end']}")
        print(f"  Crit. recycled share   : {q['2.4_secure_supply']['crit_recycled_share_end']} (target 0.20)")
        print(f"  Crit. domestic share   : {q['2.4_secure_supply']['crit_domestic_share_end']} (target 0.10)")
        print(f"  Crit. max single-country: {q['2.4_secure_supply']['crit_max_single_country_end']} (target <=0.60)")
        print(f"  Cum. discounted CO2 kt : {q['2.7_negative_impacts']['cumulative_discounted_co2_kt']}")

        # end-year spatial job allocation (Q2.5 regional growth)
        end = df.iloc[-1]
        for col in df.columns:
            if col.startswith("jobs_"):
                spatial_rows.append({"scenario": name,
                                     "district": col[len("jobs_"):],
                                     "end_jobs": round(float(end[col]), 1)})
        cge_w = end.get("cge_wage_index")
        if pd.notna(cge_w):
            print(f"  CGE end wage index     : {cge_w:.4f}")

    pd.concat(all_runs).to_csv(os.path.join(OUT, "scenario_timeseries.csv"), index=False)
    if spatial_rows:
        pd.DataFrame(spatial_rows).to_csv(
            os.path.join(OUT, "spatial_jobs_by_district.csv"), index=False)
    with open(os.path.join(OUT, "questions_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # side-by-side scenario comparison table (decision dashboard)
    comp = []
    for name, q in summary.items():
        comp.append({
            "scenario": name,
            "cum_disc_GVA_£m": q["2.6_economic_benefits"]["cumulative_discounted_gva_gbp_m"],
            "end_jobs": q["2.5_employment_regional_growth"]["total_jobs_end"],
            "recycling_jobs": q["2.5_employment_regional_growth"]["recycling_jobs_end"],
            "named_company_employee_estimate": q["2.5_employment_regional_growth"]["named_company_employee_estimate"],
            "named_recycler_companies": q["2.3_business_support"]["named_recycler_companies"],
            "named_downstream_companies": q["2.3_business_support"]["named_downstream_companies"],
            "crit_recycled_share": q["2.4_secure_supply"]["crit_recycled_share_end"],
            "crit_domestic_share": q["2.4_secure_supply"]["crit_domestic_share_end"],
            "crit_max_single_country": q["2.4_secure_supply"]["crit_max_single_country_end"],
            "cum_disc_CO2_kt": q["2.7_negative_impacts"]["cumulative_discounted_co2_kt"],
        })
    comp_df = pd.DataFrame(comp)
    comp_df.to_csv(os.path.join(OUT, "scenario_comparison.csv"), index=False)
    print("\n" + "=" * 70)
    print("SCENARIO COMPARISON (decision dashboard)")
    print("=" * 70)
    print(comp_df.to_string(index=False))
    print("\nOutputs written to:", OUT)
    print("  - validation.json")
    print("  - scenario_timeseries.csv")
    print("  - questions_summary.json")


if __name__ == "__main__":
    main()
