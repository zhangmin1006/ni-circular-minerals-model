"""
Spatial layer: allocate sectoral employment to the 11 Northern Ireland Local
Government Districts (council areas), for consultation question 2.5
(local employment, skills, regional growth).

Allocation = sector-specific district shares (PROXY, to be replaced by NISRA
BRES employment-by-district and GSNI deposit/licence locations). Mining is
weighted to the rural west / Mid Ulster / Fermanagh where Tellus anomalies and
quarrying activity concentrate; services follow population.
"""

import numpy as np
import seed_parameters as P

DISTRICTS = [
    "Antrim & Newtownabbey",
    "Ards & North Down",
    "Armagh, Banbridge & Craigavon",
    "Belfast",
    "Causeway Coast & Glens",
    "Derry City & Strabane",
    "Fermanagh & Omagh",
    "Lisburn & Castlereagh",
    "Mid & East Antrim",
    "Mid Ulster",
    "Newry, Mourne & Down",
]

# Population-based default share (PROXY, ~NISRA mid-year estimates order)
_POP = np.array([0.080, 0.085, 0.115, 0.180, 0.080, 0.080, 0.062,
                 0.080, 0.075, 0.083, 0.080])
_POP = _POP / _POP.sum()

# Sector -> district employment shares (rows=district, cols=sector). PROXY.
# Built by tilting the population share toward where each sector concentrates.
def _build_shares():
    n_d = len(DISTRICTS)
    shares = np.tile(_POP[:, None], (1, P.N))   # start from population

    def tilt(sector, weights):
        idx = P.S[sector]
        w = np.array(weights, dtype=float)
        shares[:, idx] = w / w.sum()

    # Mining & Quarrying: rural west + aggregates belts
    tilt("Mining_Quarrying",
         [0.06, 0.03, 0.10, 0.02, 0.10, 0.10, 0.16, 0.03, 0.08, 0.20, 0.12])
    # Recycling/Secondary: industrial sites near Belfast/Antrim/Mid Ulster
    tilt("Recycling_Secondary",
         [0.14, 0.05, 0.13, 0.18, 0.05, 0.06, 0.04, 0.08, 0.10, 0.12, 0.05])
    # Manufacturing: Mid Ulster, ABC, Antrim strong
    tilt("Manufacturing",
         [0.12, 0.05, 0.15, 0.10, 0.06, 0.07, 0.06, 0.07, 0.10, 0.16, 0.06])
    # Construction: broadly population-following but rural-tilted
    tilt("Construction",
         [0.09, 0.07, 0.12, 0.12, 0.08, 0.08, 0.08, 0.08, 0.08, 0.11, 0.09])
    # Services & Energy & Transport & Agriculture keep population/own defaults;
    # Agriculture rural-tilted:
    tilt("Agriculture",
         [0.07, 0.05, 0.13, 0.01, 0.10, 0.09, 0.14, 0.04, 0.07, 0.17, 0.13])
    return shares

SHARES = _build_shares()


def allocate_jobs(jobs_by_sector):
    """jobs_by_sector: length-N array -> dict district -> jobs."""
    jobs_by_sector = np.asarray(jobs_by_sector, dtype=float)
    by_district = SHARES @ jobs_by_sector          # (n_d x N) @ (N,) = n_d
    return dict(zip(DISTRICTS, by_district))


def allocate_detail(jobs_by_sector):
    """Return a district x sector job matrix (for richer Q2.5 reporting)."""
    import pandas as pd
    jobs_by_sector = np.asarray(jobs_by_sector, dtype=float)
    mat = SHARES * jobs_by_sector[None, :]
    return pd.DataFrame(mat, index=DISTRICTS, columns=P.SECTORS)


if __name__ == "__main__":
    # illustrative: 1000 mining jobs + 500 recycling jobs
    jbs = np.zeros(P.N)
    jbs[P.S["Mining_Quarrying"]] = 1000
    jbs[P.S["Recycling_Secondary"]] = 500
    d = allocate_jobs(jbs)
    print("Jobs by district (1000 mining + 500 recycling):")
    for k, v in sorted(d.items(), key=lambda x: -x[1]):
        print(f"  {k:32s} {v:7.1f}")
    print("Total:", round(sum(d.values()), 1))
