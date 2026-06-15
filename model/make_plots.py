"""
Static plot generator for the NI Circular Minerals model.

Reads the scenario outputs in ../outputs/ and writes publication-style PNG
figures to ../outputs/figures/. Run after run_mvm.py:

    python make_plots.py

Figures:
  fig1_gva_trajectory.png        cumulative-relevant GVA path per scenario
  fig2_jobs_trajectory.png       total employment path per scenario
  fig3_supply_security.png       critical-mineral recycled / domestic / single-country vs targets
  fig4_emissions.png             annual CO2 path per scenario
  fig5_tradeoff.png              jobs vs CO2 decision scatter (end-year)
  fig6_spatial_jobs.png          end-year jobs by council area (integrated scenario)
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(__file__), "outputs")
FIG = os.path.join(OUT, "figures")
os.makedirs(FIG, exist_ok=True)

TARGETS = {"recycled": 0.20, "domestic": 0.10, "single_country": 0.60}


def _load():
    ts = pd.read_csv(os.path.join(OUT, "scenario_timeseries.csv"))
    comp = pd.read_csv(os.path.join(OUT, "scenario_comparison.csv"))
    sp_path = os.path.join(OUT, "spatial_jobs_by_district.csv")
    sp = pd.read_csv(sp_path) if os.path.exists(sp_path) else None
    return ts, comp, sp


def _line_by_scenario(ts, ycol, title, ylabel, fname):
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, g in ts.groupby("scenario"):
        ax.plot(g["year"], g[ycol], marker="", linewidth=1.8, label=name)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=7, loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, fname), dpi=130)
    plt.close(fig)


def main():
    ts, comp, sp = _load()

    _line_by_scenario(ts, "gva_total_gbp_m",
                      "Annual GVA by scenario (Q2.6 economic benefits)",
                      "GVA (£m / yr)", "fig1_gva_trajectory.png")
    _line_by_scenario(ts, "employment_total",
                      "Total employment by scenario (Q2.5 jobs)",
                      "Jobs (FTE)", "fig2_jobs_trajectory.png")
    _line_by_scenario(ts, "co2_kt",
                      "Annual CO2 by scenario (Q2.7 negative impacts)",
                      "CO2 (kt / yr)", "fig4_emissions.png")

    # supply-security panel (Q2.4) for the integrated scenario
    integ = ts[ts["scenario"] == "4_integrated_circular_primary"]
    if not integ.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(integ["year"], integ["crit_recycled_share"], label="recycled share")
        ax.plot(integ["year"], integ["crit_domestic_share"], label="domestic share")
        ax.plot(integ["year"], integ["crit_max_single_country"],
                label="max single-country exposure")
        ax.axhline(TARGETS["recycled"], ls="--", color="green", alpha=0.6,
                   label="recycled target 0.20")
        ax.axhline(TARGETS["domestic"], ls="--", color="blue", alpha=0.6,
                   label="domestic target 0.10")
        ax.axhline(TARGETS["single_country"], ls="--", color="red", alpha=0.6,
                   label="single-country cap 0.60")
        ax.set_title("Critical-mineral supply security, integrated scenario (Q2.4)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Share of critical-mineral demand")
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, "fig3_supply_security.png"), dpi=130)
        plt.close(fig)

    # decision trade-off scatter (end-year jobs vs CO2)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(comp["cum_disc_CO2_kt"], comp["end_jobs"], s=60)
    for _, row in comp.iterrows():
        ax.annotate(row["scenario"], (row["cum_disc_CO2_kt"], row["end_jobs"]),
                    fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_title("Decision trade-off: jobs vs cumulative CO2")
    ax.set_xlabel("Cumulative discounted CO2 (kt)")
    ax.set_ylabel("End-year jobs (FTE)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_tradeoff.png"), dpi=130)
    plt.close(fig)

    # spatial: end-year jobs by council (integrated scenario)
    if sp is not None:
        g = sp[sp["scenario"] == "4_integrated_circular_primary"] \
            .sort_values("end_jobs")
        if not g.empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.barh(g["district"], g["end_jobs"], color="#3b7a57")
            ax.set_title("End-year jobs by council area, integrated scenario (Q2.5)")
            ax.set_xlabel("Jobs (FTE)")
            fig.tight_layout()
            fig.savefig(os.path.join(FIG, "fig6_spatial_jobs.png"), dpi=130)
            plt.close(fig)

    print("Figures written to:", FIG)
    for f in sorted(os.listdir(FIG)):
        print("  -", f)


if __name__ == "__main__":
    main()
