"""
Interactive dashboard for the NI Circular Minerals model (Streamlit).

Launch:
    streamlit run dashboard.py

It reads the CSV/JSON outputs in ../outputs/ (produced by run_mvm.py). If they
are missing it offers to run the model. The dashboard is organised by the seven
consultation questions (2.1-2.7) so policy reviewers can read results directly.
"""

import os
import json
import subprocess
import sys
import pandas as pd
import streamlit as st

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "outputs")

st.set_page_config(page_title="NI Circular Minerals Model", layout="wide")


@st.cache_data
def load():
    ts = pd.read_csv(os.path.join(OUT, "scenario_timeseries.csv"))
    comp = pd.read_csv(os.path.join(OUT, "scenario_comparison.csv"))
    with open(os.path.join(OUT, "questions_summary.json")) as f:
        summary = json.load(f)
    with open(os.path.join(OUT, "validation.json")) as f:
        val = json.load(f)
    sp_path = os.path.join(OUT, "spatial_jobs_by_district.csv")
    sp = pd.read_csv(sp_path) if os.path.exists(sp_path) else None
    return ts, comp, summary, val, sp


st.title("Northern Ireland Circular Minerals — Integrated Model")
st.caption("Dynamic Input-Output × CGE × Agent-Based Model — circular economy for "
           "critical minerals. Results mapped to consultation questions 2.1–2.7.")

if not os.path.exists(os.path.join(OUT, "scenario_timeseries.csv")):
    st.warning("No model outputs found.")
    if st.button("Run the model now (python run_mvm.py)"):
        subprocess.run([sys.executable, os.path.join(HERE, "run_mvm.py")], cwd=HERE)
        st.rerun()
    st.stop()

ts, comp, summary, val, sp = load()
scenarios = sorted(ts["scenario"].unique())

with st.sidebar:
    st.header("Controls")
    sel = st.multiselect("Scenarios", scenarios, default=scenarios)
    focus = st.selectbox("Focus scenario (spatial / detail)", scenarios,
                         index=min(3, len(scenarios) - 1))
    st.markdown("---")
    st.subheader("Model validation")
    for label, r in val.items():
        st.metric(f"{label}: jobs",
                  f"{r['model_jobs']:.0f}",
                  delta=f"anchor {r['anchor_jobs']:.0f}")

tsf = ts[ts["scenario"].isin(sel)]

tab1, tab2, tab3, tab4 = st.tabs(
    ["Economy (Q2.5/2.6)", "Supply security (Q2.4)",
     "Environment (Q2.7)", "Regional & comparison (Q2.5)"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Annual GVA (£m)")
        st.line_chart(tsf.pivot(index="year", columns="scenario",
                                values="gva_total_gbp_m"))
    with c2:
        st.subheader("Total employment (FTE)")
        st.line_chart(tsf.pivot(index="year", columns="scenario",
                                values="employment_total"))
    if "cge_wage_index" in tsf.columns and tsf["cge_wage_index"].notna().any():
        st.subheader("CGE wage index (economy-wide labour market)")
        st.line_chart(tsf.pivot(index="year", columns="scenario",
                                values="cge_wage_index"))

with tab2:
    st.subheader("Critical-mineral supply security vs Vision 2035 targets")
    g = ts[ts["scenario"] == focus]
    sec = g[["year", "crit_recycled_share", "crit_domestic_share",
             "crit_max_single_country"]].set_index("year")
    st.line_chart(sec)
    st.caption("Targets: recycled ≥0.20, domestic ≥0.10, single-country ≤0.60 by 2035.")
    end = g.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Recycled share (end)", f"{end['crit_recycled_share']:.3f}", "target 0.20")
    c2.metric("Domestic share (end)", f"{end['crit_domestic_share']:.3f}", "target 0.10")
    c3.metric("Max single-country (end)", f"{end['crit_max_single_country']:.3f}",
              "cap 0.60", delta_color="inverse")

with tab3:
    st.subheader("Annual CO2 (kt)")
    st.line_chart(tsf.pivot(index="year", columns="scenario", values="co2_kt"))
    st.subheader("Annual particulate matter (t)")
    st.line_chart(tsf.pivot(index="year", columns="scenario", values="pm_t"))

with tab4:
    st.subheader("Scenario comparison (decision dashboard)")
    st.dataframe(comp, use_container_width=True)
    if sp is not None:
        st.subheader(f"End-year jobs by council area — {focus}")
        gsp = sp[sp["scenario"] == focus].sort_values("end_jobs", ascending=False)
        st.bar_chart(gsp.set_index("district")["end_jobs"])

st.markdown("---")
st.caption("Proxy parameters are flagged in model/data/data_register.csv. "
           "Real anchors: NI mining GVA £108m / 1,950 workers; Minviro scenarios; "
           "REE/NdFeB pilot (Ionic Technologies, Belfast).")
