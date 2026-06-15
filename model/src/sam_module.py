"""
Northern Ireland Social Accounting Matrix (SAM) builder.

NI has no published SAM, so we CONSTRUCT one from:
  - the (proxy) I-O technical-coefficient matrix A  (seed_parameters)
  - a base gross-output vector anchored to NI control totals
        * total GVA pinned via the REAL mining anchor: £108m at 0.27% share
        * sector GVA shares = plausible NI structure (PROXY, replace with NISRA)
  - factor split (labour/capital) and institutional accounts (household,
    government, capital/savings, rest-of-world).

The SAM is the calibration dataset for the CGE (cge_module). It balances by
construction (row totals == column totals). STATUS: PROXY structure / REAL anchor.
"""

import numpy as np
import pandas as pd
import seed_parameters as P

# ---- NI control totals ----------------------------------------------------
NI_TOTAL_GVA_GBP_M = 108.0 / 0.0027          # mining £108m is 0.27% -> ~£40,000m
# Sector GVA shares (PROXY NI structure; mining fixed at the real 0.27%)
GVA_SHARE = np.array([
    0.015,   # Agriculture
    0.0027,  # Mining_Quarrying   (REAL anchor)
    0.005,   # Recycling_Secondary
    0.140,   # Manufacturing
    0.030,   # Energy_Utilities
    0.070,   # Construction
    0.050,   # Transport_Logistics
    0.0,     # Services (residual, filled below)
])
GVA_SHARE[P.S["Services"]] = 1.0 - GVA_SHARE.sum()

# Institutional / closure parameters (PROXY)
LABOUR_SHARE_OF_VA = 0.60     # rest is capital (gross operating surplus)
HH_SAVINGS_RATE = 0.10
GOV_DEMAND_SHARE = 0.18       # govt share of domestic final demand
EXPORT_INTENSITY = np.array([0.25, 0.40, 0.30, 0.55, 0.10, 0.05, 0.30, 0.20])


def build_sam():
    """Construct a balanced NI SAM. Structural flows are set first; imports,
    taxes and foreign savings are residuals, so the matrix balances by Walras."""
    n = P.N
    gva = GVA_SHARE * NI_TOTAL_GVA_GBP_M               # £m GVA by sector
    output = gva / P.GVA_COEFF                          # gross output by sector
    Z = P.A * output[None, :]                           # domestic intermediate flows

    # --- activity column balance: output = domЗ + imported intermediates + VA ---
    dom_int_in = Z.sum(axis=0)                          # domestic intermediates into j
    imported_intermediates = output - dom_int_in - gva  # residual (>=0 by calibration)
    imported_intermediates = np.maximum(imported_intermediates, 0.0)

    # --- factor incomes ---
    labour = gva * LABOUR_SHARE_OF_VA
    capital = gva - labour
    hh_income = labour.sum() + capital.sum()

    # --- structural final demand on commodities ---
    exports = EXPORT_INTENSITY * output                # export share of domestic output
    dom_int_sales = Z.sum(axis=1)                       # domestic intermediate sales of i
    # domestic final demand split: household / gov / investment (proxy shares of output)
    base_fd = np.maximum(output - dom_int_sales - exports, 0.0)
    gov = GOV_DEMAND_SHARE * base_fd
    invest_share = HH_SAVINGS_RATE
    invest = invest_share * base_fd
    household = base_fd - gov - invest

    # --- commodity balance: imports of commodity = absorption - domestic supply-to-home ---
    domestic_absorption = dom_int_sales + household + gov + invest
    imported_commodities = domestic_absorption - (output - exports)
    imported_commodities = np.maximum(imported_commodities, 0.0)

    imports_total = imported_intermediates.sum() + imported_commodities.sum()

    # --- institutional residual balancing (Walras) ---
    hh_savings = HH_SAVINGS_RATE * hh_income
    direct_tax = hh_income - household.sum() - hh_savings        # HH account residual
    gov_savings = direct_tax - gov.sum()                        # Gov account residual
    foreign_savings = invest.sum() - hh_savings - gov_savings   # Capital account residual

    sam = {
        "sectors": P.SECTORS,
        "output": output, "gva": gva,
        "labour": labour, "capital": capital,
        "Z": Z, "imported_intermediates": imported_intermediates,
        "household": household, "gov": gov, "invest": invest,
        "exports": exports, "imported_commodities": imported_commodities,
        "imports_total": imports_total,
        "hh_income": hh_income, "hh_savings": hh_savings,
        "direct_tax": direct_tax, "gov_savings": gov_savings,
        "foreign_savings": foreign_savings,
        "totals": {
            "GVA": gva.sum(), "output": output.sum(),
            "labour": labour.sum(), "capital": capital.sum(),
            "exports": exports.sum(), "imports": imports_total,
        },
    }
    return sam


def sam_to_dataframe(sam):
    """Assemble a readable square SAM table (accounts x accounts)."""
    sectors = sam["sectors"]
    accounts = sectors + ["Labour", "Capital", "Household", "Government",
                          "Capital_acc", "RoW"]
    idx = {a: i for i, a in enumerate(accounts)}
    m = len(accounts)
    T = np.zeros((m, m))

    # intermediate block (commodity i -> activity j)
    for i in range(P.N):
        for j in range(P.N):
            T[idx[sectors[i]], idx[sectors[j]]] = sam["Z"][i, j]
    # value added: activities pay factors
    for j in range(P.N):
        T[idx["Labour"], idx[sectors[j]]] = sam["labour"][j]
        T[idx["Capital"], idx[sectors[j]]] = sam["capital"][j]
    # factors -> household
    T[idx["Household"], idx["Labour"]] = sam["labour"].sum()
    T[idx["Household"], idx["Capital"]] = sam["capital"].sum()
    # final demand -> commodities; imports (RoW) -> activities & commodities
    for i in range(P.N):
        T[idx[sectors[i]], idx["Household"]] = sam["household"][i]
        T[idx[sectors[i]], idx["Government"]] = sam["gov"][i]
        T[idx[sectors[i]], idx["Capital_acc"]] = sam["invest"][i]
        T[idx[sectors[i]], idx["RoW"]] = sam["exports"][i]
        # imports (intermediate + final) are paid by the commodity/activity column
        T[idx["RoW"], idx[sectors[i]]] = (sam["imported_intermediates"][i]
                                          + sam["imported_commodities"][i])
    # institutional transfers
    T[idx["Government"], idx["Household"]] = sam["direct_tax"]
    T[idx["Capital_acc"], idx["Household"]] = sam["hh_savings"]
    T[idx["Capital_acc"], idx["Government"]] = sam["gov_savings"]
    T[idx["Capital_acc"], idx["RoW"]] = sam["foreign_savings"]
    return pd.DataFrame(T, index=accounts, columns=accounts)


if __name__ == "__main__":
    sam = build_sam()
    print("NI SAM control totals (£m):")
    for k, v in sam["totals"].items():
        print(f"  {k:10s} {v:12.1f}")
    df = sam_to_dataframe(sam)
    bal = (df.sum(axis=1) - df.sum(axis=0))
    print("\nMax row-col imbalance (£m):", round(bal.abs().max(), 3))
    print("Mining GVA (should be ~108):", round(sam['gva'][P.S['Mining_Quarrying']], 1))
    import os
    out = os.path.join(os.path.dirname(__file__), "..", "outputs", "ni_sam.csv")
    df.round(1).to_csv(out)
    print("SAM written to", os.path.normpath(out))
