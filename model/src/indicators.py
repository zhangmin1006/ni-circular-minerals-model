"""
Indicator layer: turns model outputs into evidence for consultation Q2.1-2.7,
and validates the I-O core against the Minviro scenario anchors.
"""

import numpy as np
import seed_parameters as P
from io_module import DynamicIO


def validate_against_minviro():
    """Inject a mining final-demand shock sized so TOTAL output matches Minviro's
    one-mine (£7.3m) and two-mine/4b (£43m) scenarios; compare jobs & GVA."""
    io = DynamicIO()
    mine = P.S["Mining_Quarrying"]
    L_outII = io.multipliers()["output_type2"][mine]
    empII = io.multipliers()["employment_type2"][mine]

    results = {}
    for label, anchor in (("one_mine", P.ANCHORS["scen_onemine"]),
                          ("two_mine_4b", P.ANCHORS["scen_twomine_4b"])):
        target_output = anchor["output"]
        fd = target_output / L_outII                 # final demand to hit total output
        fdvec = np.zeros(P.N); fdvec[mine] = fd
        imp = io.impact(fdvec, induced=True)
        # Minviro's GVA figure is DIRECT mining GVA (not economy-wide total);
        # compare like-with-like.
        direct_mining_gva = imp["output_by_sector"][mine] * io.gva_coeff[mine]
        results[label] = {
            "model_output": imp["output_total"], "anchor_output": anchor["output"],
            "model_jobs": imp["employment_total"], "anchor_jobs": anchor["jobs"],
            "model_direct_mining_gva": direct_mining_gva, "anchor_gva": anchor["gva"],
            "model_total_gva": imp["gva_total"],
        }
    return results


def map_to_questions(df, cumulative):
    """Summarise a scenario run into the seven consultation questions."""
    last = df.iloc[-1]
    first = df.iloc[0]
    return {
        "2.1_circularity_innovation": {
            "recycling_jobs_end": round(last["recycling_jobs"], 1),
            "crit_recycled_share_start": round(first["crit_recycled_share"], 3),
            "crit_recycled_share_end": round(last["crit_recycled_share"], 3),
            "recycling_fd_gbp_m_end": round(last["recycling_fd_gbp_m"], 2),
        },
        "2.2_opportunities_challenges": {
            "mines_opened": int(last["mines_opened"]),
            "note": "binding constraints surfaced via ABM (permitting, ESG, social licence)",
        },
        "2.3_business_support": {
            "recycling_capacity_proxy_fd": round(last["recycling_fd_gbp_m"], 2),
            "named_recycler_companies": int(last.get("company_recycler_count", 0)),
            "named_downstream_companies": int(last.get("company_downstream_count", 0)),
            "named_recycler_capacity_tpa": round(last.get("company_recycler_capacity_tpa", 0.0), 0),
            "avg_feedstock_score": round(last.get("avg_feedstock_score", 0.0), 3),
            "note": "firms needing finance/skills identified in ABM agent states",
        },
        "2.4_secure_supply": {
            "crit_domestic_share_end": round(last["crit_domestic_share"], 3),
            "crit_recycled_share_end": round(last["crit_recycled_share"], 3),
            "crit_import_share_end": round(last["crit_import_share"], 3),
            "crit_max_single_country_end": round(last["crit_max_single_country"], 3),
            "vs_target_recycling_0.20": round(last["crit_recycled_share"], 3),
            "vs_target_domestic_0.10": round(last["crit_domestic_share"], 3),
            "vs_target_max_single_0.60": round(last["crit_max_single_country"], 3),
        },
        "2.5_employment_regional_growth": {
            "total_jobs_end": round(last["employment_total"], 1),
            "mining_jobs_end": round(last["mining_jobs"], 1),
            "recycling_jobs_end": round(last["recycling_jobs"], 1),
            "named_company_employee_estimate": round(last.get("company_employee_estimate", 0.0), 0),
            "proposed_mining_jobs_from_company_evidence": round(
                last.get("company_proposed_mining_jobs", 0.0), 0),
        },
        "2.6_economic_benefits": {
            "gva_total_end_gbp_m": round(last["gva_total_gbp_m"], 2),
            "output_total_end_gbp_m": round(last["output_total_gbp_m"], 2),
            "cumulative_discounted_gva_gbp_m": round(cumulative["gva"], 1),
            "cumulative_discounted_output_gbp_m": round(cumulative["output"], 1),
            "firm_capex_pipeline_gbp_m": round(last.get("company_capex_pipeline_gbp_m", 0.0), 1),
            "firm_capex_operating_gbp_m": round(last.get("company_capex_operating_gbp_m", 0.0), 1),
            "firm_capex_proposed_gbp_m": round(last.get("company_capex_proposed_gbp_m", 0.0), 1),
        },
        # Q2.7 is the ECONOMIC negative impacts (the consultation question as posed).
        # The per-scenario closure-cliff exposure (mining GVA/jobs that END at mine
        # closure) is computable here; the full five-negative breakdown (leakage,
        # closure liability, agri/tourism displacement, boom-bust, stranded capital)
        # is produced by q2_7_negative_impacts.py -> outputs/q2_7_impacts.csv.
        "2.7_economic_negative_impacts": {
            "closure_cliff_mining_gva_gbp_m_end": round(
                last["mining_fd_gbp_m"] * P.GVA_COEFF[P.S["Mining_Quarrying"]], 2),
            "closure_cliff_mining_jobs_end": round(last["mining_jobs"], 1),
            "note": "economic negatives (benefit leakage, closure/remediation liability, "
                    "agriculture/tourism displacement, boom-bust exposure, stranded capital) "
                    "are quantified in q2_7_impacts.csv",
        },
        # Environmental CO2/PM satellites are retained as a separate block (NOT the
        # Q2.7 answer, which is economic): they remain useful general indicators.
        "environmental_satellites": {
            "co2_kt_end": round(last["co2_kt"], 2),
            "pm_t_end": round(last["pm_t"], 2),
            "cumulative_discounted_co2_kt": round(cumulative["co2"], 1),
        },
    }
