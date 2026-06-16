"""
Online Streamlit app for the NI Circular Minerals Policy Model.

This root-level entry point is designed for Streamlit Community Cloud and other
simple hosts. It reads committed outputs when present and can regenerate them on
the server if needed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "model"
OUT = MODEL_DIR / "outputs"
DATA = MODEL_DIR / "data"

SCENARIO_LABELS = {
    "1_baseline": "Baseline",
    "2_circular_innovation": "Circular innovation",
    "3_primary_extraction": "Primary extraction",
    "4_integrated_circular_primary": "Integrated circular + primary",
    "5_supply_shock": "Supply shock",
    "6_high_esg_low_impact": "High ESG / low impact",
}


st.set_page_config(
    page_title="NI Circular Minerals Model",
    page_icon="model/outputs/figures/fig3_supply_security.png",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_outputs():
    ts = pd.read_csv(OUT / "scenario_timeseries.csv")
    comp = pd.read_csv(OUT / "scenario_comparison.csv")
    company = pd.read_csv(DATA / "company_register.csv")
    register = pd.read_csv(DATA / "data_register.csv")
    with open(OUT / "questions_summary.json", encoding="utf-8") as f:
        questions = json.load(f)
    with open(OUT / "validation.json", encoding="utf-8") as f:
        validation = json.load(f)
    spatial_path = OUT / "spatial_jobs_by_district.csv"
    spatial = pd.read_csv(spatial_path) if spatial_path.exists() else pd.DataFrame()
    return ts, comp, company, register, questions, validation, spatial


@st.cache_data(show_spinner=False)
def load_interventions():
    path = OUT / "q2_1_interventions.csv"
    if not path.exists():
        return None, None
    df = pd.read_csv(path, index_col=0)
    memo_path = OUT / "q2_1_memo.md"
    memo = memo_path.read_text(encoding="utf-8") if memo_path.exists() else None
    return df, memo


def generate_interventions():
    return subprocess.run(
        [sys.executable, "q2_1_circularity_interventions.py"],
        cwd=MODEL_DIR, capture_output=True, text=True, timeout=300,
    )


@st.cache_data(show_spinner=False)
def load_q22():
    opp_path = OUT / "q2_2_opportunity_ranking.csv"
    sc_path = OUT / "q2_2_constraint_scenarios.csv"
    if not (opp_path.exists() and sc_path.exists()):
        return None, None, None
    opp = pd.read_csv(opp_path, index_col=0)
    sc = pd.read_csv(sc_path, index_col=0)
    memo_path = OUT / "q2_2_memo.md"
    memo = memo_path.read_text(encoding="utf-8") if memo_path.exists() else None
    return opp, sc, memo


def generate_q22():
    return subprocess.run(
        [sys.executable, "q2_2_opportunities_challenges.py"],
        cwd=MODEL_DIR, capture_output=True, text=True, timeout=300,
    )


@st.cache_data(show_spinner=False)
def load_demand_supply():
    dem_path = OUT / "q_demand_scenarios.csv"
    gap_path = OUT / "q_supply_capacity_gap.csv"
    if not (dem_path.exists() and gap_path.exists()):
        return None, None, None
    dem = pd.read_csv(dem_path, index_col=0)
    gap = pd.read_csv(gap_path, index_col=0)
    memo_path = OUT / "q_demand_supply_memo.md"
    memo = memo_path.read_text(encoding="utf-8") if memo_path.exists() else None
    return dem, gap, memo


def generate_demand_supply():
    return subprocess.run(
        [sys.executable, "q_demand_supply_strategy.py"],
        cwd=MODEL_DIR, capture_output=True, text=True, timeout=300,
    )


@st.cache_data(show_spinner=False)
def load_q23():
    sc_path = OUT / "q2_3_support_scenarios.csv"
    stage_path = OUT / "q2_3_stage_support.csv"
    if not (sc_path.exists() and stage_path.exists()):
        return None, None, None
    sc = pd.read_csv(sc_path, index_col=0)
    stages = pd.read_csv(stage_path, index_col=0)
    memo_path = OUT / "q2_3_memo.md"
    memo = memo_path.read_text(encoding="utf-8") if memo_path.exists() else None
    return sc, stages, memo


def generate_q23():
    return subprocess.run(
        [sys.executable, "q2_3_business_support.py"],
        cwd=MODEL_DIR, capture_output=True, text=True, timeout=300,
    )


def ensure_outputs():
    needed = [
        OUT / "scenario_timeseries.csv",
        OUT / "scenario_comparison.csv",
        OUT / "questions_summary.json",
        OUT / "validation.json",
    ]
    if all(path.exists() for path in needed):
        return

    st.warning("Model outputs are not present in this deployment.")
    if st.button("Run model now"):
        with st.spinner("Running the 30-year scenario suite..."):
            result = subprocess.run(
                [sys.executable, "run_mvm.py"],
                cwd=MODEL_DIR,
                capture_output=True,
                text=True,
                timeout=120,
            )
        if result.returncode:
            st.error("The model run failed.")
            st.code(result.stderr or result.stdout)
        else:
            st.success("Model outputs generated.")
            st.cache_data.clear()
            st.rerun()
    st.stop()


def label_scenario(name: str) -> str:
    return SCENARIO_LABELS.get(name, name)


def _roi_band_figure(plot: pd.DataFrame):
    """Horizontal ROI plot: central point with a high-cost/low-cost whisker."""
    d = plot.sort_values("gva_roi_central")
    central = d["gva_roi_central"].to_numpy(dtype=float)
    lo = d["gva_roi_pessimistic"].to_numpy(dtype=float)   # high cost -> low ROI
    hi = d["gva_roi_optimistic"].to_numpy(dtype=float)     # low cost -> high ROI
    y = range(len(d))
    fig, ax = plt.subplots(figsize=(8, 0.5 * len(d) + 1.2))
    ax.errorbar(central, y, xerr=[central - lo, hi - central], fmt="o",
                color="#006A6A", ecolor="#9CC", elinewidth=3, capsize=4)
    ax.axvline(1.0, color="#B00", linestyle="--", linewidth=1, label="break-even (ROI = 1)")
    ax.set_yticks(list(y))
    ax.set_yticklabels(d.index)
    ax.set_xlabel("Discounted GVA per £ public cost (ROI)")
    ax.legend(loc="lower right", fontsize=8)
    ax.margins(y=0.1)
    fig.tight_layout()
    return fig


def metric_card(col, label, value, help_text=None):
    col.metric(label, value, help=help_text)


def scenario_options(ts):
    scenarios = list(ts["scenario"].drop_duplicates())
    return {label_scenario(s): s for s in scenarios}


def format_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "scenario" in out.columns:
        out["scenario"] = out["scenario"].map(label_scenario)
    return out


ensure_outputs()
ts, comp, company, register, questions, validation, spatial = load_outputs()
options = scenario_options(ts)
scenario_names = list(options)

with st.sidebar:
    st.title("NI Minerals Model")
    selected_labels = st.multiselect(
        "Scenarios",
        scenario_names,
        default=scenario_names,
    )
    focus_label = st.selectbox(
        "Focus scenario",
        scenario_names,
        index=min(3, len(scenario_names) - 1),
    )
    selected = [options[label] for label in selected_labels]
    focus = options[focus_label]

    st.divider()
    st.caption("Validation anchors")
    for label, row in validation.items():
        st.metric(
            label.replace("_", " ").title(),
            f"{row['model_jobs']:.0f} jobs",
            f"anchor {row['anchor_jobs']:.0f}",
        )

st.title("Northern Ireland Circular Minerals Policy Model")
st.caption(
    "Interactive ABM x material-flow x dynamic input-output x CGE dashboard for "
    "consultation questions 2.1-2.7."
)

focus_df = ts[ts["scenario"] == focus].sort_values("year")
end = focus_df.iloc[-1]
start = focus_df.iloc[0]
ts_selected = ts[ts["scenario"].isin(selected)]

top = st.columns(5)
metric_card(top[0], "End-year jobs", f"{end['employment_total']:,.0f}")
metric_card(top[1], "End-year GVA", f"GBP {end['gva_total_gbp_m']:,.1f}m")
metric_card(top[2], "Critical recycled share", f"{end['crit_recycled_share']:.3f}")
metric_card(top[3], "Critical domestic share", f"{end['crit_domestic_share']:.3f}")
metric_card(top[4], "Single-country exposure", f"{end['crit_max_single_country']:.3f}")

(tab_overview, tab_q21, tab_q22, tab_q23, tab_demand, tab_supply, tab_companies,
 tab_region, tab_data) = st.tabs(
    ["Overview", "Q2.1 Interventions", "Q2.2 Opportunities", "Q2.3 Business Support",
     "Demand & Supply", "Supply Security", "Companies", "Regional Jobs", "Data Quality"]
)

with tab_overview:
    left, right = st.columns(2)
    with left:
        st.subheader("GVA trajectory")
        chart = ts_selected.pivot(index="year", columns="scenario", values="gva_total_gbp_m")
        chart = chart.rename(columns=label_scenario)
        st.line_chart(chart)
    with right:
        st.subheader("Employment trajectory")
        chart = ts_selected.pivot(index="year", columns="scenario", values="employment_total")
        chart = chart.rename(columns=label_scenario)
        st.line_chart(chart)

    st.subheader("Scenario comparison")
    st.dataframe(format_columns(comp), width="stretch", hide_index=True)

with tab_q21:
    st.subheader("Q2.1 — Supporting innovation for circularity")
    st.caption(
        "How can the Department support innovation in materials recovery, secondary "
        "materials markets, recycling and circular design? Seven NI-government "
        "interventions, each mapped to the firm-grounded ABM levers, run individually "
        "and as a combined package over 30 years (STPR 3.5%)."
    )
    iv, memo = load_interventions()
    if iv is None:
        st.warning("Q2.1 intervention results are not present in this deployment.")
        if st.button("Run the Q2.1 experiment now"):
            with st.spinner("Running seven interventions over 30 years..."):
                res = generate_interventions()
            if res.returncode:
                st.error("The experiment failed.")
                st.code(res.stderr or res.stdout)
            else:
                st.cache_data.clear()
                st.rerun()
    else:
        plot = iv.drop(index="0_baseline", errors="ignore")
        best_roi = plot["gva_roi_central"].idxmax()
        best_share = plot["d_recycled_share_pp"].idxmax()
        target = 0.20

        k1, k2, k3 = st.columns(3)
        k1.metric("Best value-for-money (GVA ROI)", best_roi,
                  f"{plot.loc[best_roi, 'gva_roi_central']:.2f}x central")
        k2.metric("Biggest recycled-share lift", best_share,
                  f"+{plot.loc[best_share, 'd_recycled_share_pp']:.1f} pp")
        hit = [i for i in plot.index if plot.loc[i, "crit_recycled_share_end"] >= target]
        k3.metric("Meets Vision-2035 20% target", ", ".join(hit) if hit else "none alone")

        left, right = st.columns(2)
        with left:
            st.markdown("**Critical-mineral recycled share (end-year)**")
            st.bar_chart(plot["crit_recycled_share_end"])
            st.caption(f"Vision-2035 target = {target:.0%} (dashed expectation).")
        with right:
            st.markdown("**Extra discounted GVA vs baseline (£m)**")
            st.bar_chart(plot["d_cum_gva_gbp_m"])

        st.markdown("**Innovation ROI with cost-uncertainty band** "
                    "(GVA per £ public cost; whisker = high-cost to low-cost bound)")
        st.pyplot(_roi_band_figure(plot))
        st.caption(
            "An intervention whose whole band stays above 1.0 is robustly value-positive; "
            "one straddling 1.0 (e.g. smart collection / DRS) is sensitive to programme cost."
        )

        show_cols = {
            "theme": "Theme",
            "crit_recycled_share_end": "Recycled share",
            "secondary_value_gbp_m_end": "Secondary value £m",
            "recycling_jobs_end": "Recycling jobs",
            "circular_design_uptake_end": "Design uptake",
            "d_cum_gva_gbp_m": "ΔGVA £m",
            "disc_public_cost_gbp_m": "Public cost £m",
            "gva_roi_central": "ROI (central)",
            "gva_roi_range": "ROI (band)",
        }
        st.dataframe(iv[list(show_cols)].rename(columns=show_cols), width="stretch")

        c1, c2 = st.columns([1, 3])
        c1.download_button(
            "Download intervention results",
            iv.to_csv().encode("utf-8"),
            "q2_1_interventions.csv", "text/csv",
        )
        if memo:
            with st.expander("Full findings memo (UK-anchored costs & calibration sources)"):
                st.markdown(memo)


with tab_q22:
    st.subheader("Q2.2 — Opportunities & challenges for sustainable minerals development")
    st.caption(
        "A mineral-by-mineral opportunity ranking (demand, geology, circular potential, "
        "strategic value) and constraint-relaxation scenarios that reveal the binding "
        "barrier — relaxing one constraint at a time to see what unlocks development."
    )
    opp, sc, memo22 = load_q22()
    if opp is None:
        st.warning("Q2.2 results are not present in this deployment.")
        if st.button("Run the Q2.2 experiment now"):
            with st.spinner("Ranking opportunities and testing constraints..."):
                res = generate_q22()
            if res.returncode:
                st.error("The experiment failed.")
                st.code(res.stderr or res.stdout)
            else:
                st.cache_data.clear()
                st.rerun()
    else:
        st.markdown("**Opportunity ranking (higher = stronger opportunity)**")
        st.bar_chart(opp["opportunity_score"])
        opp_cols = {
            "critical": "Critical", "opportunity_score": "Score", "pathway": "Pathway",
            "key_challenge": "Key challenge", "domestic_geology": "Geology",
            "import_dependence": "Import dep.", "named_miners": "Named miners",
        }
        st.dataframe(opp[list(opp_cols)].rename(columns=opp_cols), width="stretch")

        st.markdown("**Constraint relaxation — what unlocks development?** "
                    "(extra discounted GVA vs today's constraints)")
        single = sc.drop(index="0_current_constraints", errors="ignore")
        chart = single["d_cum_gva_gbp_m"]
        chart.index = single["label"]
        st.bar_chart(chart)

        binding = single.drop(
            index=["responsible_high_esg", "enabling_environment"], errors="ignore"
        ).sort_values(["d_mines", "d_cum_gva_gbp_m"], ascending=False)
        if len(binding):
            b = binding.index[0]
            st.success(
                f"**Binding constraint: {sc.loc[b, 'label']}** — unlocks "
                f"{sc.loc[b, 'projects_unlocked']} (+{int(sc.loc[b, 'd_mines'])} project(s), "
                f"+£{sc.loc[b, 'd_cum_gva_gbp_m']}m discounted GVA, "
                f"+{sc.loc[b, 'd_cum_co2_kt']} ktCO₂ trade-off)."
            )
        sc_cols = {
            "label": "Scenario", "mines_opened": "Mines", "projects_unlocked": "Projects",
            "crit_domestic_share_end": "Crit. domestic share", "end_jobs": "End jobs",
            "cum_disc_gva_gbp_m": "Cum. GVA £m", "d_cum_co2_kt": "ΔCO₂ kt",
        }
        st.dataframe(sc[list(sc_cols)].rename(columns=sc_cols), width="stretch")

        if memo22:
            with st.expander("Full Q2.2 findings memo"):
                st.markdown(memo22)


with tab_q23:
    st.subheader("Q2.3 — Business support across the supply chain")
    st.caption(
        "What support do firms at each supply-chain stage need to participate and "
        "withstand an upstream supply shock (critical-mineral imports capped at 60% "
        "of demand + price spike)? Stage-targeted government support packages, run "
        "over 30 years."
    )
    sc23, stages23, memo23 = load_q23()
    if sc23 is None:
        st.warning("Q2.3 results are not present in this deployment.")
        if st.button("Run the Q2.3 experiment now"):
            with st.spinner("Running the supply shock + stage-support packages..."):
                res = generate_q23()
            if res.returncode:
                st.error("The experiment failed.")
                st.code(res.stderr or res.stdout)
            else:
                st.cache_data.clear()
                st.rerun()
    else:
        if "shock_no_support" in sc23.index:
            shock = sc23.loc["shock_no_support"]
            k1, k2, k3 = st.columns(3)
            k1.metric("Supply gap under shock (no support)",
                      f"{shock['crit_supply_gap_end']:.0%}", "unmet critical-mineral demand",
                      delta_color="off")
            if "shock_full_support" in sc23.index:
                full = sc23.loc["shock_full_support"]
                k2.metric("Supply gap with full support",
                          f"{full['crit_supply_gap_end']:.0%}",
                          f"{(full['crit_supply_gap_end']-shock['crit_supply_gap_end'])*100:.0f} pp")
                k3.metric("Jobs protected (full vs unsupported)",
                          f"+{full['total_jobs_end']-shock['total_jobs_end']:.0f}")

        st.markdown("**Support needed by supply-chain stage**")
        st.dataframe(stages23.rename(columns={
            "firms": "Firms", "employees": "Employees",
            "binding_challenge": "Binding challenge", "shock_exposure": "Shock exposure",
            "support_needed": "Support needed", "model_levers": "Model levers"}),
            width="stretch")

        st.markdown("**Effect of each support package (under the shock)**")
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Critical-mineral supply gap (lower = more resilient)")
            st.bar_chart(sc23["crit_supply_gap_end"])
        with c2:
            st.caption("Jobs by stage (end-year)")
            st.bar_chart(sc23[["mining_jobs_end", "recycling_jobs_end",
                               "manufacturing_jobs_end"]])
        st.info(
            "Sequencing insight: **downstream support alone barely helps under the shock** — "
            "manufacturers can't buy recycled content that doesn't exist yet. It pays off only "
            "once **midstream processing/recovery capacity** is built. Upstream support brings "
            "domestic primary forward; full cross-chain support roughly halves the supply gap."
        )
        sc_cols = {
            "label": "Scenario", "crit_supply_gap_end": "Supply gap",
            "crit_recycled_share_end": "Recycled", "crit_domestic_share_end": "Domestic",
            "total_jobs_end": "Total jobs", "cum_disc_gva_gbp_m": "Cum. GVA £m",
            "d_total_jobs": "Δ jobs vs shock",
        }
        st.dataframe(sc23[list(sc_cols)].rename(columns=sc_cols), width="stretch")

        sev_path = OUT / "q2_3_shock_severity.csv"
        if sev_path.exists():
            sweep = pd.read_csv(sev_path)
            order = ["mild_cap80", "moderate_cap60", "severe_cap40", "extreme_cap20"]
            pkgs = ["no_support", "upstream", "midstream", "full"]
            gap_pivot = (sweep.pivot(index="severity", columns="support",
                                     values="supply_gap_end").reindex(order)[pkgs])
            st.markdown("**Resilience across shock severity** (import cap 80%→20%; "
                        "supply gap, lower = more resilient)")
            st.line_chart(gap_pivot)
            st.info(
                "Support is worth more the deeper the shock — but there's a ceiling: even full "
                "cross-chain support can't fully offset an extreme (80% import loss) shock, because "
                "NI's domestic + recovery capacity can't replace that volume. The best *single* "
                "lever shifts with severity (midstream for mild shocks, upstream for severe), and "
                "the residual gap argues for strategic stockpiles + international diversification."
            )

        if memo23:
            with st.expander("Full Q2.3 findings memo (stage-by-stage support)"):
                st.markdown(memo23)


with tab_demand:
    st.subheader("Demand-side opportunities & supply-side capacity challenges")
    st.caption(
        "Demand scenarios from the UK Critical Minerals Strategy (Vision 2035), the "
        "EU Critical Raw Materials Act and the UK Industrial Strategy, run under a "
        "sustainable enabling-policy stance (demand grows to ~2035 then plateaus); "
        "plus the current circular supply chain's capacity gap by mineral."
    )
    dem, gap, memo_ds = load_demand_supply()
    if dem is None:
        st.warning("Demand/supply results are not present in this deployment.")
        if st.button("Run the demand & supply analysis now"):
            with st.spinner("Running strategy demand scenarios + capacity analysis..."):
                res = generate_demand_supply()
            if res.returncode:
                st.error("The analysis failed.")
                st.code(res.stderr or res.stdout)
            else:
                st.cache_data.clear()
                st.rerun()
    else:
        st.markdown("**Part A — demand-side opportunity (by strategy scenario)**")
        d1, d2 = st.columns(2)
        with d1:
            st.caption("Discounted GVA £m")
            chart = dem["cum_disc_gva_gbp_m"].copy(); chart.index = dem["label"]
            st.bar_chart(chart)
        with d2:
            st.caption("Critical recycled vs import share (end-year)")
            st.bar_chart(dem[["crit_recycled_share_end", "crit_import_share_end"]])
        st.info(
            "Tension: stronger strategy demand grows jobs and GVA, but **erodes the "
            "recycled share and raises import dependence** unless processing/recovery "
            "capacity scales with it — see the capacity gap below."
        )
        dem_cols = {
            "label": "Scenario", "mines_opened": "Mines", "crit_domestic_share_end": "Domestic",
            "crit_recycled_share_end": "Recycled", "crit_import_share_end": "Import",
            "end_jobs": "End jobs", "cum_disc_gva_gbp_m": "Cum. GVA £m",
        }
        st.dataframe(dem[list(dem_cols)].rename(columns=dem_cols), width="stretch")

        st.markdown("**Part B — current circular supply chain: capacity coverage of 2035 demand**")
        st.caption("Coverage = NI processing capacity ÷ projected 2035 demand "
                   "(only REE has any; the battery metals have none).")
        st.bar_chart(gap["capacity_coverage"])
        gap_cols = {
            "proj_2035_demand_t": "2035 demand t", "ni_processing_capacity_tpa": "NI capacity tpa",
            "capacity_coverage": "Coverage", "has_primary_prospect": "Primary?",
            "has_collection_route": "Collection?", "key_gap": "Key gap",
        }
        st.dataframe(gap[list(gap_cols)].rename(columns=gap_cols), width="stretch")

        sens_path = OUT / "q_demand_sensitivity.csv"
        if sens_path.exists():
            sens = pd.read_csv(sens_path, index_col=0)
            st.markdown("**Demand sensitivity** — annex-derived central case ±50% "
                        "(lithium alone, and all demand)")
            s1, s2 = st.columns(2)
            with s1:
                st.caption("Discounted GVA £m by demand case")
                st.bar_chart(sens["cum_disc_gva_gbp_m"])
            with s2:
                st.caption("Recycled vs import share by demand case")
                st.bar_chart(sens[["crit_recycled_share_end", "crit_import_share_end"]])
            if "central_annex" in sens.index:
                c = sens.loc["central_annex"]
                lo, hi = sens.loc["all_demand_-50%"], sens.loc["all_demand_+50%"]
                st.caption(
                    f"±50% on all demand moves jobs {lo['end_jobs']:.0f}–{hi['end_jobs']:.0f} "
                    f"(central {c['end_jobs']:.0f}) and GVA £{lo['cum_disc_gva_gbp_m']:.0f}–"
                    f"{hi['cum_disc_gva_gbp_m']:.0f}m. Lithium alone ±50% barely moves GVA "
                    f"(tiny NI tonnage base). The qualitative findings hold across the band; "
                    f"higher demand consistently erodes the recycled share — reinforcing the "
                    f"capacity-gap message."
                )

        st.markdown("**NI evidence base** (strategy documents + GSNI/BGS briefing)")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("REE supply: single-country", "74%", "China, 2023", delta_color="off")
        e2.metric("UK metals exported to process", "~80%", "midstream gap", delta_color="off")
        e3.metric("NI recycling rate", "50.4%", "flat since 2019", delta_color="off")
        e4.metric("Curraghinalt gold (M&I)", "3.79 Moz", "+Cu/Sb/Te/Co", delta_color="off")
        evid = register[register["parameter"].str.startswith(
            ("uk_demand", "iea_", "supply_concentration", "uk_metals", "ni_recycling",
             "ni_windsor", "curraghinalt", "belfast_harbour"), na=False)]
        if not evid.empty:
            st.caption("Cited evidence rows (from data_register.csv):")
            st.dataframe(evid[["parameter", "value", "unit", "source", "notes"]],
                         width="stretch", hide_index=True)
        st.caption(
            "Opportunity drivers: NI is the UK/Ireland's most prospective area for precious "
            "metals (Curraghinalt + Mourne REE potential); a REE-recycling cluster (Ionic, "
            "QUILL, + Plaswire on turbine blades); Belfast Harbour offshore-wind decommissioning "
            "feedstock; and possible **dual UK + EU market access** via Windsor Framework Art. 13(4). "
            "Challenges: the ~80% processing-export gap, supply concentration to displace, stalled "
            "recycling (energy-from-waste competing), and ~20-yr contested primary lead times."
        )
        if memo_ds:
            with st.expander("Full demand & supply findings memo (3-strategy analysis + sources)"):
                st.markdown(memo_ds)


with tab_supply:
    st.subheader(f"Critical-mineral supply security: {focus_label}")
    security = focus_df[
        ["year", "crit_recycled_share", "crit_domestic_share", "crit_max_single_country"]
    ].set_index("year")
    st.line_chart(security)

    target_cols = st.columns(3)
    target_cols[0].metric("Recycling target", "0.20", f"end {end['crit_recycled_share']:.3f}")
    target_cols[1].metric("Domestic target", "0.10", f"end {end['crit_domestic_share']:.3f}")
    target_cols[2].metric(
        "Single-country cap",
        "0.60",
        f"end {end['crit_max_single_country']:.3f}",
        delta_color="inverse",
    )

    st.subheader("Mining and recycling final demand")
    flows = focus_df[["year", "mining_fd_gbp_m", "recycling_fd_gbp_m"]].set_index("year")
    st.area_chart(flows)

with tab_companies:
    st.subheader("Company evidence layer")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Named companies", f"{int(end.get('company_count', len(company)))}")
    c2.metric("Mining / quarry", f"{int(end.get('company_mining_count', 0))}")
    c3.metric("Recycler / waste", f"{int(end.get('company_recycler_count', 0))}")
    c4.metric("Downstream / supply chain", f"{int(end.get('company_downstream_count', 0))}")

    c5, c6, c7 = st.columns(3)
    c5.metric("Evidence employment estimate", f"{end.get('company_employee_estimate', 0):,.0f}")
    c6.metric("Avg feedstock score", f"{end.get('avg_feedstock_score', 0):.3f}")
    c7.metric("Avg planning risk", f"{end.get('avg_planning_risk_score', 0):.3f}")

    display_cols = [
        "company", "role", "district", "location", "lifecycle_stage",
        "employee_estimate", "minerals_or_products", "evidence_status",
        "capacity_score", "feedstock_score", "demand_score",
        "planning_risk_score", "source_url",
    ]
    st.dataframe(company[display_cols], width="stretch", hide_index=True)

with tab_region:
    if spatial.empty:
        st.info("Spatial output file is not available.")
    else:
        st.subheader(f"End-year jobs by council area: {focus_label}")
        regional = spatial[spatial["scenario"] == focus].sort_values("end_jobs", ascending=False)
        st.bar_chart(regional.set_index("district")["end_jobs"])
        st.dataframe(format_columns(regional), width="stretch", hide_index=True)

with tab_data:
    st.subheader("Data status register")
    status_counts = register["status"].value_counts().rename_axis("status").reset_index(name="count")
    st.dataframe(status_counts, width="stretch", hide_index=True)
    st.dataframe(register, width="stretch", hide_index=True)

    st.subheader("Downloads")
    d1, d2, d3 = st.columns(3)
    d1.download_button(
        "Download scenario comparison",
        comp.to_csv(index=False).encode("utf-8"),
        "scenario_comparison.csv",
        "text/csv",
    )
    d2.download_button(
        "Download company register",
        company.to_csv(index=False).encode("utf-8"),
        "company_register.csv",
        "text/csv",
    )
    d3.download_button(
        "Download data register",
        register.to_csv(index=False).encode("utf-8"),
        "data_register.csv",
        "text/csv",
    )

st.caption(
    "Company and behavioural scores are proxy/desk-researched until replaced "
    "with audited company accounts, BRES, facility tonnage, and firm survey data."
)
