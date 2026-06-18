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

# IEA Global Critical Minerals Outlook 2025: the security problem is not only the
# single dominant supplier but TOP-THREE producer concentration (which rose to
# ~86% average for key minerals in 2024) and, more acutely, REFINING/PROCESSING
# concentration (China is the leading refiner for 19 of 20 strategic minerals,
# ~70% average). These are wired into the MFA as second/third risk indices beside
# single-country exposure. data_register: supply_concentration_top3_2024 (0.86),
# china_refining_share_2024 (0.70), supply_export_controls_share_2024 (0.55).
# Per-mineral desk estimates (0-1) consistent with the IEA aggregates.
TOP3_CONCENTRATION = {           # top-3 mine-supply producers' combined share
    "REE_magnet": 0.92, "Cobalt": 0.86, "Antimony": 0.90, "Aluminium": 0.70,
    "Lithium": 0.90, "Nickel": 0.78, "Copper": 0.50,
}
REFINING_CONCENTRATION = {       # leading single refiner's (China) processing share
    "REE_magnet": 0.90, "Cobalt": 0.75, "Antimony": 0.85, "Aluminium": 0.60,
    "Lithium": 0.68, "Nickel": 0.65, "Copper": 0.45,
}
# Minerals currently subject to active export controls (China REE/antimony/gallium/
# germanium/graphite; cobalt via DRC concentration). IEA: controls now touch ~55%
# of energy-related strategic minerals.
EXPORT_CONTROL = {
    "REE_magnet": True, "Antimony": True, "Cobalt": True, "Lithium": False,
    "Nickel": False, "Copper": False, "Aluminium": False,
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
