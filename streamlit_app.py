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

tab_overview, tab_supply, tab_companies, tab_region, tab_data = st.tabs(
    ["Overview", "Supply Security", "Companies", "Regional Jobs", "Data Quality"]
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
