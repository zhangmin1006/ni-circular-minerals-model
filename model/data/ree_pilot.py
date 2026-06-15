"""
REE / NdFeB permanent-magnet PILOT — one mineral thread grounded in published
literature and the NI-specific Ionic Technologies case, replacing the generic
proxy for "REE_magnet" in the MFA.

Status legend in PROVENANCE:
  LIT   = published literature / official figure (cited)
  EST   = derived estimate (NI-scaled from UK/EU figures)
  PROXY = placeholder, replace when primary data collected

NOTE: values are best-available desk estimates for an illustrative pilot, not
audited statistics. Each carries a source note so it can be firmed up.
"""

# ---------------------------------------------------------------------------
# Pilot parameters for the REE permanent-magnet system in Northern Ireland
# ---------------------------------------------------------------------------
REE_PILOT = {
    # Annual NI demand for REE contained in NdFeB magnets (tonnes REE-oxide eq).
    # EST: UK NdFeB magnet demand ~ a few kt/yr; NI ~2-3% of UK population/industry.
    "demand0_t": 95.0,                 # EST

    # Average in-use lifetime of magnet-bearing products (EVs, wind, electronics,
    # industrial motors) weighted to NI stock. LIT/EST.
    "lifetime_yr": 11,                 # EST (wind ~20-25, EV ~10-15, electronics ~5-8)

    # Collection rate of end-of-life magnet-bearing products in NI.
    # LIT: REE functional recycling globally <1-5%; collection (not recovery) higher
    # for bulky items. Set low to reflect current reality.
    "collection_rate": 0.06,           # LIT/EST

    # Recovery yield once collected & processed (Ionic Technologies hydromet route
    # for separating/refining REE from spent magnets). LIT (process-scale figure).
    "recovery_yield": 0.90,            # LIT (Ionic Technologies / Met4Tech, process yield)

    # Domestic primary share — NI has no REE mine; Tellus shows REE/PGE anomalies but
    # no producing deposit. Kept at zero for the pilot baseline.
    "domestic_primary_share": 0.00,    # LIT (no NI REE production)

    # Import single-country concentration (China dominates REE magnet supply chain).
    # LIT: China ~>80-90% of refined REE / magnet output.
    "import_single_country_share": 0.87,  # LIT

    # Price of contained REE in magnets (GBP/tonne, Nd/Pr/Dy blend, volatile).
    "price_gbp_per_t": 95000.0,        # LIT/EST (NdPr oxide blended, indicative)

    # REE mass fraction of an NdFeB magnet (Nd+Pr+Dy+Tb), for product<->mineral conv.
    "ree_mass_fraction_of_magnet": 0.31,  # LIT (~30-32% rare-earth content)

    # Energy intensity of the recycling route vs primary (relative), for env signal.
    # LIT: magnet-to-magnet recycling materially lower CO2 than primary mine+refine.
    "recycling_co2_vs_primary": 0.30,  # LIT (recycling ~30% of primary footprint)
}

PROVENANCE = {
    "demand0_t": ("EST", "NI-scaled from UK NdFeB magnet demand; firm with HMRC trade + sector survey"),
    "lifetime_yr": ("EST", "Weighted product lifetimes (wind/EV/electronics/motors)"),
    "collection_rate": ("LIT/EST", "REE functional recycling <1-5% globally; Vision 2035 notes low collection"),
    "recovery_yield": ("LIT", "Ionic Technologies hydrometallurgical separation/refining; Met4Tech"),
    "domestic_primary_share": ("LIT", "No producing REE deposit in NI; GSNI Tellus shows anomalies only"),
    "import_single_country_share": ("LIT", "China dominance of refined REE / magnet supply (Vision 2035)"),
    "price_gbp_per_t": ("LIT/EST", "Indicative NdPr blended oxide price; replace with USGS/Argus series"),
    "ree_mass_fraction_of_magnet": ("LIT", "NdFeB rare-earth content ~30-32%"),
    "recycling_co2_vs_primary": ("LIT", "Magnet recycling LCA vs primary; Minviro CLCA template, ecoinvent"),
}


def apply_to_mineral_params(mineral_params):
    """Overwrite the generic 'REE_magnet' proxy row in mfa_module.MINERAL_PARAMS
    with the pilot values. Tuple order:
    (demand0, lifetime, coll, rec, dom0, imp_conc)."""
    p = REE_PILOT
    mineral_params["REE_magnet"] = (
        p["demand0_t"], p["lifetime_yr"], p["collection_rate"],
        p["recovery_yield"], p["domestic_primary_share"],
        p["import_single_country_share"],
    )
    return mineral_params


def apply_price(price_dict):
    price_dict["REE_magnet"] = REE_PILOT["price_gbp_per_t"]
    return price_dict


if __name__ == "__main__":
    print("REE permanent-magnet pilot parameters:")
    for k, v in REE_PILOT.items():
        tag = PROVENANCE.get(k, ("", ""))[0]
        print(f"  {k:32s} {v:>10}  [{tag}]")
