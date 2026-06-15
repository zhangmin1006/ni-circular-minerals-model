"""
Seed parameters for the NI Circular Minerals MVM (Tier 1).

ALL economic-structure coefficients here are PROXY values, flagged as such, and
are intended to be replaced by a regionalised/updated NI Input-Output table
(NISRA Supply-Use + Scottish 2017 I-O via FLQ + RAS) once collected.

Real, sourced anchors (Minviro Final Report; Vision 2035; NISRA) are used for
control totals and validation. See ../data/data_register.csv for provenance.
"""

import numpy as np

# ---------------------------------------------------------------------------
# 1. SECTORS (aggregated NI economy for the MVM I-O)
# ---------------------------------------------------------------------------
SECTORS = [
    "Agriculture",            # 0
    "Mining_Quarrying",       # 1
    "Recycling_Secondary",    # 2  <- circular-economy sector, split out deliberately
    "Manufacturing",          # 3
    "Energy_Utilities",       # 4
    "Construction",           # 5
    "Transport_Logistics",    # 6
    "Services",               # 7
]
N = len(SECTORS)
S = {name: i for i, name in enumerate(SECTORS)}

# ---------------------------------------------------------------------------
# 2. PROXY technical-coefficient matrix A  (a_ij = input from i per unit output j)
#    Columns = buying sector, Rows = supplying sector.  STATUS: PROXY.
#    Calibrated so a Mining demand shock yields ~10 total jobs/£m and
#    GVA/output ~0.21 (Minviro Scenario anchors).
# ---------------------------------------------------------------------------
#            Agri  Mining Recyc  Manuf  Energy Constr Trans  Serv   (buyers ->)
_A_raw = np.array([
    [0.12,  0.01,  0.01,  0.08,  0.01,  0.01,  0.01,  0.02],  # Agriculture
    [0.00,  0.05,  0.02,  0.06,  0.03,  0.07,  0.00,  0.00],  # Mining_Quarrying
    [0.00,  0.00,  0.04,  0.05,  0.01,  0.03,  0.00,  0.00],  # Recycling_Secondary
    [0.04,  0.10,  0.10,  0.18,  0.05,  0.14,  0.06,  0.05],  # Manufacturing
    [0.03,  0.08,  0.08,  0.06,  0.10,  0.04,  0.05,  0.04],  # Energy_Utilities
    [0.01,  0.06,  0.03,  0.02,  0.04,  0.06,  0.02,  0.03],  # Construction
    [0.05,  0.09,  0.09,  0.08,  0.04,  0.06,  0.10,  0.05],  # Transport_Logistics
    [0.10,  0.15,  0.15,  0.16,  0.12,  0.14,  0.18,  0.22],  # Services
], dtype=float)
# Scale to reflect high import leakage of a small, open regional economy (NI),
# so Type I output multipliers land in the realistic ~1.4-1.8 range. PROXY.
DOMESTIC_INTENSITY = 0.62
A = _A_raw * DOMESTIC_INTENSITY

# ---------------------------------------------------------------------------
# 3. Value-added / GVA coefficient per unit output (1 - sum of column inputs - imports)
#    STATUS: PROXY. Mining tuned to ~0.40 (GVA/output) so £108m GVA <-> ~£270m output.
# ---------------------------------------------------------------------------
# Mining GVA/output = 0.35 reproduces Minviro's DIRECT mining GVA anchors
# (one-mine £1.6m, two-mine £9.0m) given the Type II output distribution.
GVA_COEFF = np.array([0.45, 0.35, 0.38, 0.32, 0.40, 0.36, 0.42, 0.55])

# Import share of intermediate + final demand per sector (leakage). STATUS: PROXY.
IMPORT_SHARE = np.array([0.20, 0.30, 0.25, 0.45, 0.25, 0.20, 0.20, 0.12])

# ---------------------------------------------------------------------------
# 4. Satellite accounts (per £m of OUTPUT). STATUS: PROXY (anchored where noted).
# ---------------------------------------------------------------------------
# Employment: jobs per £m output. Mining anchored to 1950 jobs / ~£270m output ~7.2,
# then indirect+induced via multipliers brings totals to the Minviro ~10 jobs/£m.
# Mining 11.5 jobs/£m output calibrated so a mining shock yields ~10 total
# jobs/£m total output (Minviro: 430 jobs / £43m; 73 jobs / £7.3m).
EMP_COEFF = np.array([12.0, 11.5, 8.5, 6.0, 2.5, 9.0, 7.0, 9.5])

# GHG: ktCO2e per £m output (env satellite, replace with NAEI/DAERA). PROXY.
CO2_COEFF = np.array([0.9, 1.4, 0.6, 0.7, 2.2, 0.5, 1.1, 0.2])

# PM (particulate matter): tonnes per £m output. PROXY.
PM_COEFF = np.array([0.05, 0.20, 0.06, 0.08, 0.12, 0.10, 0.09, 0.02])

# Household consumption coefficient (for Type II / induced effect): share of
# wages re-spent on each sector's output. STATUS: PROXY.
HH_CONSUMPTION = np.array([0.08, 0.005, 0.005, 0.12, 0.10, 0.05, 0.10, 0.54])
WAGE_SHARE_OF_GVA = 0.55  # PROXY: portion of GVA paid as wages (drives induced)
# Local marginal propensity to consume: 1 - savings - direct tax - imported consumption.
# Dampens the induced (Type II) loop to realistic levels for an open region. PROXY.
LOCAL_CONSUMPTION_PROPENSITY = 0.42

# ---------------------------------------------------------------------------
# 5. MINERALS & PRODUCTS tracked in the Material Flow Account
# ---------------------------------------------------------------------------
MINERALS = ["REE_magnet", "Lithium", "Cobalt", "Nickel", "Copper",
            "Aluminium", "Antimony", "Baryte", "Salt", "Zinc"]

# Critical-minerals subset (per BGS/Vision 2035) — reported separately from bulk
# minerals (Salt, Baryte) because tonnage-weighting otherwise lets Salt dominate.
CRITICAL_MINERALS = ["REE_magnet", "Lithium", "Cobalt", "Nickel",
                     "Copper", "Aluminium", "Antimony"]

PRODUCTS = ["EV_battery", "Permanent_magnet", "Electronics_WEEE",
            "Wind_turbine", "Vehicle_ELV", "Industrial_equipment"]

# ---------------------------------------------------------------------------
# 6. Real anchors & policy targets (from data_register.csv) — for validation
# ---------------------------------------------------------------------------
ANCHORS = {
    "ni_mining_gva_2018_gbp_m": 108.0,
    "ni_mining_workers": 1950.0,
    "ni_total_jobs_2023": 816562.0,
    "scen_onemine": {"jobs": 73.0, "output": 7.3, "gva": 1.6},
    "scen_twomine_4b": {"jobs": 430.0, "output": 43.0, "gva": 9.0},
}
TARGETS_2035 = {  # Vision 2035 (GOV.UK)
    "domestic_share": 0.10,
    "recycling_share": 0.20,
    "max_single_country": 0.60,
}
STPR = 0.035                 # Social Time Preference Rate (Green Book/NIGEAE)
MINING_COST_OF_EQUITY = 0.1126
HORIZON = 30                 # years
