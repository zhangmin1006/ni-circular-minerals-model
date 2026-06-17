"""
Shared policy / economic constants used across the Q2.x experiments.

Single source of truth to remove the duplicated (drift-prone) CONCENTRATION and
lever-cost maps that previously lived separately in q2_3 / q2_4 / q2_6.
Provenance for every value is in data_register.csv.
"""

# 2023 single-country supply concentration (dominant supplier's share), the
# geopolitical-risk vector for the shock scenarios. BGS/Idoine et al. 2025 via
# GSNI OR25042 (China 74% REE, DRC 70% Co, Australia 44% Li, ...).
CONCENTRATION = {
    "REE_magnet": 0.74, "Cobalt": 0.70, "Antimony": 0.70, "Aluminium": 0.35,
    "Lithium": 0.44, "Nickel": 0.40, "Copper": 0.30,
}

# Public cost per policy lever (GBP m / yr at intensity 1.0), NI-scale, anchored to
# named UK programmes (Vision 2035 DBT, CLIMATES/Faraday, DEFRA DRS, BICS, DfE
# skills, NWF/UKEF). Used for the relative ROI / cost comparisons.
LEVER_COST = {
    "finance_support": 6.0, "exploration_grant": 3.0, "community_benefit": 3.0,
    "recycling_grant": 7.0, "innovation_grant": 5.0, "collection_infrastructure": 9.0,
    "product_passport": 2.0, "secondary_market_support": 4.0,
    "recycled_content_procurement": 1.0, "design_standards": 1.0, "skills_support": 4.0,
    "local_supplier_support": 3.0, "diversification": 3.0, "strategic_stockpile": 4.0,
}
