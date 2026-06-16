"""
Seed parameters for the NI Circular Minerals MVM (Tier 1).

ALL economic-structure coefficients here are PROXY values, flagged as such, and
are intended to be replaced by a regionalised/updated NI Input-Output table
(NISRA Supply-Use + Scottish 2017 I-O via FLQ + RAS) once collected.

Real, sourced anchors (Minviro Final Report; Vision 2035; NISRA) are used for
control totals and validation. See ../data/data_register.csv for provenance.
"""

import numpy as np
import data_register as DR

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
# 6. Real anchors & policy targets — READ FROM data_register.csv
#    (single source of truth; the literals after the comma are fallbacks used
#    only if a register row is absent/non-numeric, so the model never crashes).
# ---------------------------------------------------------------------------
ANCHORS = {
    "ni_mining_gva_2018_gbp_m": DR.value("ni_mining_quarrying_gva_2018", 108.0),
    "ni_mining_workers": DR.value("ni_mining_quarrying_workers", 1950.0),
    "ni_total_jobs_2023": DR.value("ni_total_employee_jobs_2023", 816562.0),
    "scen_onemine": {
        "jobs": DR.value("scen_onemine_jobs_pa", 73.0),
        "output": DR.value("scen_onemine_output_pa", 7.3),
        "gva": DR.value("scen_onemine_gva_pa", 1.6),
    },
    "scen_twomine_4b": {
        "jobs": DR.value("scen4b_jobs_pa", 430.0),
        "output": DR.value("scen4b_output_pa", 43.0),
        "gva": DR.value("scen4b_gva_pa", 9.0),
    },
}
TARGETS_2035 = {  # Vision 2035 (GOV.UK)
    "domestic_share": DR.value("uk_target_domestic_share_2035", 0.10),
    "recycling_share": DR.value("uk_target_recycling_share_2035", 0.20),
    "max_single_country": DR.value("uk_target_max_single_country_2035", 0.60),
}
STPR = DR.value("stpr_discount_rate", 0.035)          # Social Time Preference Rate
MINING_COST_OF_EQUITY = DR.value("mining_cost_of_equity_nominal", 0.1126)
HORIZON = int(DR.value("model_horizon_years", 30))    # years

# Circular-economy & demand parameters now sourced from the register too, so the
# MFA and scenario runner stop carrying their own copies (see data_register.csv).
RECOVERY_YIELDS = {                                   # spent-product recovery yield
    "REE_magnet": DR.value("recovery_yield_ree_magnet", 0.85),
    "Lithium": DR.value("recovery_yield_lithium", 0.50),
    "Copper": DR.value("recovery_yield_copper", 0.90),
}
COLLECTION_RATE_WEEE = DR.value("collection_rate_weee", 0.30)
LOCAL_PROCUREMENT_SHARE_MINING = DR.value("local_procurement_share_mining", 0.45)
DEMAND_GROWTH_EV = DR.value("ni_demand_growth_ev", 0.12)      # battery-metal driver
DEMAND_GROWTH_WIND = DR.value("ni_demand_growth_wind", 0.08)  # magnet/REE driver
